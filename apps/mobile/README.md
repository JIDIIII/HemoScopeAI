# HemoScope AI mobile app

This is the Expo Router mobile client for the HemoScope AI research demonstrator. It supports onboarding, microscope setup guidance, camera and gallery selection, an API-backed quality check, local session metadata, and a results shell.

The initial scaffold targets Android only. Expo iOS support can be enabled later by adding it to the `platforms` list after its permissions and device workflow are reviewed.

## Setup

From the repository root, install dependencies with npm. The app targets Expo SDK 57 so a physical Android phone can use the matching Expo Go client during the current SDK transition. Its React Native and React versions follow Expo's SDK compatibility table.

```sh
npm ci
cp apps/mobile/.env.example apps/mobile/.env
npm run mobile:start
```

Install Expo Go on the Android phone, connect the phone and computer to the same trusted Wi-Fi network, then scan the QR code. Camera access requires a physical device. To test the backend from the phone, set EXPO_PUBLIC_API_BASE_URL in apps/mobile/.env to http://COMPUTER_LAN_IP:8000. Do not use localhost from a physical phone.

## Available checks

```sh
npm run mobile:typecheck
npm run mobile:lint
npm --workspace @hemoscope/mobile run format:check
```

## Current scope

Camera and gallery permission paths are implemented. The selected image is previewed and sent to POST /quality. Manual drag-and-resize crop selection is an explicit TODO, so the app keeps analysis disabled until a real crop file and confirmation are available. Huawei credentials are never part of this package.

Research-use only: the app does not diagnose leukemia, rule out disease, or recommend treatment. One selected cell does not represent an entire smear.
