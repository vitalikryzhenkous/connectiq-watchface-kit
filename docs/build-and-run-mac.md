# Сборка и запуск на Mac и часах

## 1. Подготовка (один раз)
- Аккаунт разработчика: developer.garmin.com, вход обычным Garmin-аккаунтом.
- Установить VS Code и расширение **Monkey C** (Garmin).
- Установить **Connect IQ SDK Manager** → войти в аккаунт:
  - вкладка SDK: скачать последний → «Use as current SDK»;
  - вкладка Devices: скачать нужные часы (fr945 и т. д.).
- `Cmd+Shift+P` → `Monkey C: Verify Installation`. Если ругается на Java: `brew install openjdk@17`.
- `Cmd+Shift+P` → `Monkey C: Generate a Developer Key`, сохранить в `~/garmin/`. **Не терять:** этим же ключом подписываются все обновления в сторе.

## 2. Симулятор
- VS Code → File → Open Folder → папка циферблата.
- Run → Run Without Debugging (`Ctrl+F5`) → выбрать устройство.
- Что проверить:
  - настройки: File → Edit Persistent Storage → Edit Application.Properties;
  - сон: Settings → Low Power Mode;
  - позиция: меню Simulation (Познань 52.41, 16.93);
  - погода, время, батарея: меню Simulation.
- Скриншот для стора: File → Save Screenshot.

## 3. Сборка для часов
- `Cmd+Shift+P` → `Monkey C: Build for Device` → устройство → папка вывода → файл `.prg`.

## 4. Установка (sideload)
- Установить **OpenMTP** и закрыть Garmin Express.
- USB → `GARMIN/APPS` → перетащить `.prg`.
- Отключить кабель → на часах удерживать UP → Циферблат → выбрать.
- Удаление: стереть `.prg` из `GARMIN/APPS`.

## 5. Падение (IQ!)
- Создать пустой файл `GARMIN/APPS/LOGS/CIQ_LOG.YML` → воспроизвести падение → передать файл в `/wf-debug`.

## 6. Публикация
- Сначала: `python3 scripts/release_check.py templates/n3on-terminal` (или `/wf-release-check`). Все ❌ должны быть исправлены, ручной чек-лист пройден.
- `Monkey C: Export Project` → `.iq` → Developer Dashboard. Подробности в `.claude/skills/connectiq-watchface/references/store-listing.md`.
