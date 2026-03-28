# Mindstream Mobile

Minimal Flutter app for local APK testing against the Mindstream FastAPI backend.

## Backend

Default backend URL in the app:

`http://192.168.1.13:8000`

You can change it at runtime in the app UI before testing.

## Commands

```bash
flutter pub get
flutter run
flutter build apk
```

## Notes

- The backend must be reachable from the phone on the same Wi-Fi network.
- Android cleartext HTTP is enabled in the manifest for local development.
