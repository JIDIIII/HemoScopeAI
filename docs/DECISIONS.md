# HemoScope AI decisions

| Decision | Rationale | Revisit when |
| --- | --- | --- |
| Expo SDK 57 baseline | Current Expo SDK guidance pairs SDK 57 with React Native 0.86 and React 19.2.3; its camera and picker versions are available to Expo Go on a physical device during the SDK transition | Expo Go and SDK 58 compatibility is confirmed for the target phone |
| FastAPI contract uses Pydantic | One backend schema source exports OpenAPI and generated TypeScript API types | A versioned contract package is introduced |
| Field quality and cell-crop quality are separate checks | A full microscope field and a manually selected cell have different expected dimensions | Representative capture data supports calibrated rules |
| Quality values are development defaults | No representative microscope calibration set is included | Target phone/microscope captures have been collected and reviewed |
| No model loads by default | The backend must start without weights and must not imply a prediction exists | A reviewed checkpoint and inference package are supplied |
| Demo mock is opt-in and abstains | Demonstrates request/response handling without fabricating a class or score | A real inference integration is validated |
| History remains local-first | Avoids collecting image/session data on a server during the scaffold | Authorization, authentication, retention, and deletion requirements are implemented |
| Five-day sprint is the working plan | The explicit project request and checklist specify five days, while the outline describes a seven-day horizon | Team explicitly revises the sprint plan |
| GitHub branches are recommendations only | Parallel ownership is documented without creating remote state | Team creates authorized branches in its own workflow |
