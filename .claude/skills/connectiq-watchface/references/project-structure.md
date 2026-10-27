# Project structure

```
myface/
├── manifest.xml              # app id (UUID, no dashes), type="watchface", products, minApiLevel
├── monkey.jungle             # project.manifest = manifest.xml (+ per-device resource paths)
├── source/
│   ├── <Name>App.mc          # AppBase: getInitialView, onSettingsChanged -> view.loadSettings()
│   ├── <Name>View.mc         # WatchFace: onLayout/onUpdate/onEnterSleep/onExitSleep
│   └── *.mc                  # modules: Theme, Bot, Sun, WeatherIcon ...
└── resources/
    ├── fonts/fonts.xml       # <font id="X" filename="x.fnt" antialias="false"/>
    ├── drawables/            # launcher_icon.png + drawables.xml
    ├── strings/strings.xml   # AppName + setting labels
    └── settings/
        ├── properties.xml    # <property id="Theme" type="number">0</property>
        └── settings.xml      # list / boolean settingConfig bound via @Properties.X
```

## Per-device resources
```
resources-fenix7/fonts/...    # overrides resources/ for that device
```
In `monkey.jungle`:
```
fenix7.resourcePath = $(fenix7.resourcePath);resources-fenix7
```

## Common product ids
| Device | id | Screen | Type |
|---|---|---|---|
| Forerunner 945 | fr945 | 240 | MIP |
| Forerunner 955 / Solar | fr955 | 260 | MIP |
| Forerunner 255 | fr255 | 260 | MIP |
| Forerunner 265 | fr265 | 416 | AMOLED |
| Forerunner 965 | fr965 | 454 | AMOLED |
| Fenix 7 | fenix7 | 260 | MIP |
| Fenix 7X | fenix7x | 280 | MIP |
| Venu 2 | venu2 | 416 | AMOLED |

Verify ids in SDK Manager → Devices before adding them to the manifest; names change between SDK releases.
