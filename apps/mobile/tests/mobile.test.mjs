import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { resolve, dirname } from "node:path";
import vm from "node:vm";
import ts from "typescript";
const require = createRequire(import.meta.url);
const root = resolve("src");
function load(file, overrides = {}, globals = {}) {
  const filename = resolve(root, file);
  const source = ts.transpileModule(readFileSync(filename, "utf8"), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      esModuleInterop: true,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (name) => {
    if (Object.hasOwn(overrides, name)) return overrides[name];
    if (name.startsWith("@/"))
      return load(name.slice(2) + ".ts", overrides, globals);
    if (name.startsWith("."))
      return load(resolve(dirname(filename), name + ".ts"), overrides, globals);
    return require(name);
  };
  vm.runInNewContext(source, {
    module,
    exports: module.exports,
    require: localRequire,
    setTimeout,
    clearTimeout,
    AbortController,
    Error,
    Response,
    ...globals,
  });
  return module.exports;
}
const geometry = load("features/cell-selection/geometry.ts");
const plain = (value) => JSON.parse(JSON.stringify(value));
test("drag and resize remain within image edges", () => {
  const box = { x: 0.3, y: 0.3, width: 0.4, height: 0.4 };
  assert.equal(geometry.moveCrop(box, 5, -5).x, 0.6);
  assert.equal(geometry.moveCrop(box, 5, -5).y, 0);
  assert.equal(geometry.resizeCrop(box, 5, 5).width, 0.7);
  assert.equal(geometry.resizeCrop(box, -5, -5).height, 0.05);
});
test("normalized crops map to original portrait and landscape pixels", () => {
  assert.deepEqual(
    plain(
      geometry.pixelCrop(
        { x: 0.25, y: 0.1, width: 0.5, height: 0.2 },
        4000,
        3000,
      ),
    ),
    { originX: 1000, originY: 300, width: 2000, height: 600 },
  );
  assert.deepEqual(
    plain(geometry.pixelCrop({ x: 0, y: 0, width: 1, height: 1 }, 3000, 4000)),
    { originX: 0, originY: 0, width: 3000, height: 4000 },
  );
  assert.throws(() =>
    geometry.pixelCrop({ x: -0.1, y: 0, width: 1, height: 1 }, 100, 100),
  );
  assert.throws(() =>
    geometry.pixelCrop({ x: 0, y: 0, width: NaN, height: 1 }, 100, 100),
  );
});
test("invalid input is rejected before upload", () => {
  const { validateImageInput } = load("features/capture/validation.ts");
  assert.equal(
    validateImageInput({ fileName: "field.PNG", width: 500, height: 500 }),
    "image/png",
  );
  assert.throws(() =>
    validateImageInput({ mimeType: "image/heic", width: 500, height: 500 }),
  );
  assert.throws(() =>
    validateImageInput({ mimeType: "image/jpeg", width: 0, height: 500 }),
  );
  assert.throws(() =>
    validateImageInput({
      mimeType: "image/jpeg",
      width: 500,
      height: 500,
      fileSize: 11000000,
    }),
  );
});
const valid = {
  analysis_id: "a",
  analysis_status: "analysis_complete",
  quality_status: "accepted",
  inference_mode: "real",
  model_version: "v1",
  warning: "Research only",
};
test("malformed, unknown, or contradictory results fail closed", () => {
  const { validateAnalysis } = load("features/analysis/result.ts");
  assert.equal(validateAnalysis(valid).analysis_status, "analysis_complete");
  for (const change of [
    { analysis_status: "negative" },
    { quality_status: "rejected" },
    { model_version: null },
    { raw_model_score: NaN },
    { inference_mode: null },
  ])
    assert.throws(() => validateAnalysis({ ...valid, ...change }));
});
test("malformed quality payload cannot unlock cell selection", () => {
  const { validateQuality } = load("features/quality-check/validation.ts");
  assert.throws(() => validateQuality({ acceptable: true }));
  assert.throws(() =>
    validateQuality({ acceptable: true, quality_status: "rejected" }),
  );
});
class FormDataStub {
  fields = [];
  append(...args) {
    this.fields.push(args);
  }
}
function client(fetch, overrides = {}) {
  return load(
    "services/api/client.ts",
    {
      "@/constants/api": {
        API_BASE_URL: "https://test.example",
        USE_MOCK_API: false,
      },
      ...overrides,
    },
    { fetch, FormData: FormDataStub },
  );
}
test("analysis uploads only confirmed crop with agreed multipart fields", async () => {
  let body;
  const api = client(async (url, init) => {
    assert.equal(url, "https://test.example/analyze");
    body = init.body;
    return Response.json(valid);
  });
  await api.analyzeConfirmedCrop({
    cellCrop: {
      uri: "file:///crop.jpg",
      mimeType: "image/jpeg",
      fileName: "private-name.jpg",
    },
    researchSessionId: "local-1",
  });
  assert.deepEqual(plain(body.fields), [
    [
      "cell_crop",
      {
        uri: "file:///crop.jpg",
        name: "confirmed-cell.jpg",
        type: "image/jpeg",
      },
    ],
    ["crop_confirmed", "true"],
    ["research_session_id", "local-1"],
  ]);
});
test("offline, timeout, server, and malformed responses never become results", async () => {
  for (const fetch of [
    async () => {
      throw new Error("offline");
    },
    async () => {
      const e = new Error("timeout");
      e.name = "AbortError";
      throw e;
    },
    async () =>
      Response.json(
        { error: { message: "Model unavailable" } },
        { status: 503 },
      ),
    async () => Response.json({ analysis_status: "negative" }),
  ]) {
    await assert.rejects(() =>
      client(fetch).analyzeConfirmedCrop({
        cellCrop: { uri: "crop", mimeType: "image/jpeg", fileName: "crop.jpg" },
      }),
    );
  }
});
test("all successful mock scenarios are labeled simulated and contract-valid", async () => {
  const mock = load("services/api/mock.ts");
  const { validateAnalysis } = load("features/analysis/result.ts");
  const { validateQuality } = load("features/quality-check/validation.ts");
  for (const scenario of [
    "analysis_complete",
    "inconclusive",
    "review_required",
  ]) {
    mock.setMockScenario(scenario);
    assert.equal(
      validateAnalysis(await mock.mockRequest("/analyze")).inference_mode,
      "simulated",
    );
    assert.equal(
      validateQuality(await mock.mockRequest("/quality")).acceptable,
      true,
    );
  }
  mock.setMockScenario("recapture_required");
  assert.equal(
    validateQuality(await mock.mockRequest("/quality")).acceptable,
    false,
  );
});
test("history preserves capture time and simulated metadata without image content", async () => {
  let raw = null;
  const store = load("services/storage/sessionStore.ts", {
    "@react-native-async-storage/async-storage": {
      getItem: async () => raw,
      setItem: async (_, value) => {
        raw = value;
      },
      removeItem: async () => {
        raw = null;
      },
    },
  });
  const base = {
    sessionId: "local-1",
    imageId: "local-1",
    capturedAt: "2026-11-15T01:00:00Z",
    qualityStatus: "accepted",
    analysisStatus: "not_started",
  };
  await store.updateLocalSession(base);
  await store.updateLocalSession({
    ...base,
    capturedAt: "2026-11-15T02:00:00Z",
    analysisStatus: "inconclusive",
    inferenceMode: "simulated",
    modelVersion: "MOCK-NOT-A-MODEL",
  });
  const sessions = await store.listLocalSessions();
  assert.equal(sessions.length, 1);
  assert.equal(sessions[0].capturedAt, base.capturedAt);
  assert.equal(sessions[0].inferenceMode, "simulated");
  assert.equal(raw.includes("uri"), false);
  await store.clearLocalSessions();
  assert.equal((await store.listLocalSessions()).length, 0);
});
test("timeout covers a stalled response body download", async () => {
  const api = load(
    "services/api/client.ts",
    {
      "@/constants/api": {
        API_BASE_URL: "https://test.example",
        USE_MOCK_API: false,
      },
    },
    {
      FormData: FormDataStub,
      setTimeout: (fn) => setTimeout(fn, 10),
      fetch: async (_, { signal }) => ({
        text: () =>
          new Promise((_, reject) =>
            signal.addEventListener("abort", () => {
              const error = new Error("Aborted");
              error.name = "AbortError";
              reject(error);
            }),
          ),
      }),
    },
  );
  await assert.rejects(() => api.getHealth(), /timed out/);
});
test("production ignores mock configuration and live remains the default", () => {
  assert.equal(
    load(
      "constants/api.ts",
      {},
      { __DEV__: false, process: { env: { EXPO_PUBLIC_API_MODE: "mock" } } },
    ).USE_MOCK_API,
    false,
  );
  assert.equal(
    load("constants/api.ts", {}, { __DEV__: true, process: { env: {} } })
      .USE_MOCK_API,
    false,
  );
  assert.equal(
    load(
      "constants/api.ts",
      {},
      { __DEV__: true, process: { env: { EXPO_PUBLIC_API_MODE: "mock" } } },
    ).USE_MOCK_API,
    true,
  );
});
test("all four crop corners stay inside the image and preserve the opposite edge", () => {
  const box = { x: 0.2, y: 0.3, width: 0.4, height: 0.4 };
  for (const corner of ["topLeft", "topRight", "bottomLeft", "bottomRight"]) {
    const next = geometry.resizeFromCorner(box, -5, 5, corner);
    assert.ok(
      next.x >= 0 && next.y >= 0 && next.width >= 0.049 && next.height >= 0.049,
    );
    assert.ok(
      next.x + next.width <= 1.000001 && next.y + next.height <= 1.000001,
    );
  }
  const topLeft = geometry.resizeFromCorner(box, 0.1, 0.1, "topLeft");
  assert.ok(Math.abs(topLeft.x + topLeft.width - 0.6) < 0.000001);
  assert.ok(Math.abs(topLeft.y + topLeft.height - 0.7) < 0.000001);
});
