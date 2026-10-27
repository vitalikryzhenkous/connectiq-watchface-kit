You are writing a Garmin Connect IQ watch face in Monkey C. Output a complete, buildable project as files:

- `manifest.xml` (type `watchface`, a valid 32-hex-char app id, the listed products, `launcherIcon="@Drawables.LauncherIcon"`)
- `monkey.jungle` containing `project.manifest = manifest.xml`
- `source/*.mc`
- `resources/strings/strings.xml` (with `AppName`), `resources/drawables/drawables.xml` defining `LauncherIcon` as `launcher_icon.png`, and any settings/properties resources the task needs

Rules: do not create binary files (the harness supplies `resources/drawables/launcher_icon.png`); use only Toybox APIs available on the listed devices; no network access and no permissions unless the task says so; original design only (no brand logos or characters).
