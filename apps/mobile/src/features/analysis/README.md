# Analysis

The crop screen checks quality before submitting the confirmed crop through the existing multipart API contract. Runtime validation rejects invalid/contradictory responses. Each status has scoped instructions; failures preserve the crop for retry. Development mocks are opt-in, labeled on screen and in history, and disabled in production. Huawei credentials remain server-side. Live authentication/inference verification requires Developer 3's endpoint.
