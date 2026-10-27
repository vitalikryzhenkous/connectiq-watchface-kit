# N3on Terminal — циферблат для Garmin Forerunner 945

Cyberpunk-терминал: glitch-время, оригинальный пиксельный бот с настроением, погода, восход/закат, шаги, батарея, статус телефона.

## Структура
- `source/N3onView.mc` — отрисовка и логика
- `source/Bot.mc` — бот (настроения: normal / low battery / night / step goal)
- `source/Sun.mc` — восход и закат офлайн по координатам
- `source/WeatherIcon.mc` — иконки погоды
- `source/Theme.mc` — 3 темы, только цвета из 64-цветной палитры MIP
- `resources/fonts/` — пиксельные моноширинные шрифты (BMFont, без сглаживания)
- `resources/settings/` — настройки: тема, scanlines, glitch, бот

## Сборка
1. Установить VS Code и расширение **Monkey C** (Garmin).
2. Установить **Connect IQ SDK Manager**, скачать в нём последний SDK и устройство **Forerunner 945**.
3. В VS Code: `Cmd+Shift+P` → `Monkey C: Generate a Developer Key`.
4. Открыть папку проекта → `Cmd+Shift+P` → `Monkey C: Build for Device` → `fr945` → получится `.prg`.
5. Симулятор: `Run → Run Without Debugging`. Позицию для восхода/заката задать в меню симулятора (Simulation → Set Position).

## Установка на часы (sideload)
1. Подключить часы по USB. На macOS нужен MTP-клиент (например, OpenMTP).
2. Скопировать `.prg` в `GARMIN/APPS`.
3. Отключить часы и выбрать циферблат в меню.

Важно: у sideload-версии настройки с телефона не меняются. Для теста меняй значения по умолчанию в `resources/settings/properties.xml`. Настройки через Garmin Connect заработают после публикации в Connect IQ Store (можно как приватную beta).

## Публикация
1. `Cmd+Shift+P` → `Monkey C: Export Project` → файл `.iq`.
2. Загрузить на developer-портал Connect IQ, добавить скриншоты и описание, отправить на модерацию.

## Требования
- Connect IQ API 3.2+ (FR945 поддерживает).
- Погода приходит с телефона; без синхронизации показывается `--`.
- Восход/закат: нужна хотя бы одна известная позиция (погода с телефона или GPS-активность); позиция кэшируется.
