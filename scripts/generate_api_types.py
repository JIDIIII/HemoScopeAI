#!/usr/bin/env python3
"""Generate compact TypeScript schema types from the committed OpenAPI JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OPENAPI = ROOT / "packages" / "contracts" / "openapi.json"
OUTPUT = ROOT / "apps" / "mobile" / "src" / "types" / "api.generated.ts"


def quote(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", maxsplit=1)[-1]
        return f'components["schemas"]["{name}"]'
    if "enum" in schema:
        return " | ".join(quote(value) for value in schema["enum"])
    if "const" in schema:
        return quote(schema["const"])
    if "anyOf" in schema:
        return " | ".join(f"({render_type(part)})" for part in schema["anyOf"])
    if "oneOf" in schema:
        return " | ".join(f"({render_type(part)})" for part in schema["oneOf"])
    if "allOf" in schema:
        return " & ".join(f"({render_type(part)})" for part in schema["allOf"])

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return " | ".join(render_type({"type": item}) for item in schema_type)
    if schema_type == "array":
        return f"Array<{render_type(schema.get('items', {}))}>"
    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        members = []
        for property_name, property_schema in properties.items():
            marker = "" if property_name in required else "?"
            members.append(f"      {quote(property_name)}{marker}: {render_type(property_schema)};")
        if members:
            return "{\n" + "\n".join(members) + "\n    }"
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            return f"Record<string, {render_type(additional)}>"
        if additional is True:
            return "Record<string, unknown>"
        return "Record<string, never>"

    if schema_type == "string":
        return "string"
    if schema_type in {"integer", "number"}:
        return "number"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "null":
        return "null"
    return "unknown"


def main() -> None:
    document = json.loads(OPENAPI.read_text(encoding="utf-8"))
    schemas = document["components"]["schemas"]
    lines = [
        "/* Generated from packages/contracts/openapi.json. Do not edit by hand. */",
        "export interface components {",
        "  schemas: {",
    ]
    for name, schema in schemas.items():
        lines.append(f'    "{name}": {render_type(schema)};')
    lines.extend(["  };", "}", ""])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
