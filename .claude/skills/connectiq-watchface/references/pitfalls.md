# Pitfalls (learned the hard way)

## Compiler
- `Cannot determine if container access is using container type` (WARNING): you indexed an untyped array. Type the parameter, e.g. `pal as Array<Number>`, and add `import Toybox.Lang;`.
- String concatenation that starts with a Number fails or does math. Start with `""`, e.g. `"" + key + ":"`.
- `Float.toNumber()` truncates. Round manually: `(v + 0.5).toNumber()`.
- `Weather` is missing on old devices. Guard it with `if (Toybox has :Weather)`.
- Unicode literals (`°`, `▲`, `▼`) work only if the glyph is in your custom font (`gen_font.py --chars`).

## Runtime
- `IQ!` on the watch means a crash. Create `GARMIN/APPS/LOGS/CIQ_LOG.YML` (empty file), reproduce the crash, then read the file.
- `Application.Properties.getValue` can throw or return null on the first run. Wrap it in try/catch with a default.
- Weather and location can be null until the phone syncs. Show `--` or `--:--`, never crash.
- `Storage.setValue` on every `onUpdate` wears flash and costs battery. Write only on change.

## Tooling (macOS)
- SDK Manager log `Reading password for "Garmin.ConnectIQ.SdkManager.accessToken" failed: User canceled` means the Keychain prompt was dismissed. It's harmless if the SDK and devices are already downloaded. To fix it, click "Always Allow" on the Keychain prompt, or sign in again.
- `Monkey C: Verify Installation` complains about Java: `brew install openjdk@17`.
- The Mac can't see the watch in Finder. Use OpenMTP and quit Garmin Express first.
- Sideloaded faces ignore phone settings. To test settings, change the defaults in `properties.xml` or use the simulator: File → Edit Persistent Storage → Edit Application.Properties.

## Phone pairing (iOS)
- "Cannot Add Accessory" while the watch shows a code: forget the device in iOS Bluetooth and in Settings → Privacy → Accessories, remove it from Garmin Connect, reboot both, turn off Low Power mode and Focus, then pair only from the Garmin Connect app and confirm the code quickly.

## Location (sunrise/sunset shows --:--)
- `Weather.getCurrentConditions().observationLocationPosition` is often null, and `Activity.getActivityInfo().currentLocation` stays null until the watch has had a GPS fix (in any GPS activity). A fresh face has no position, so cache the last good one in `Application.Storage`.
- Always offer a manual Lat/Lon setting (0/0 = auto) and show a hint like "no gps fix" instead of an empty time.
