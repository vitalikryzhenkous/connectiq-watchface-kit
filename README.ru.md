# connectiq-watchface-kit

🇬🇧 [English](README.md) · 🇷🇺 Русский

Набор для создания циферблатов Garmin Connect IQ вместе с Claude Code: скилл, slash-команды, скрипты и эталонный проект.

![N3on Terminal](docs/n3on-preview.png)

## Что внутри
| Путь | Что это |
|---|---|
| `.claude/skills/connectiq-watchface/` | Скилл: весь цикл работы, ключевые API, грабли, публикация в стор |
| `.claude/commands/` | `/wf-new`, `/wf-preview`, `/wf-add-device`, `/wf-debug`, `/wf-store` |
| `templates/n3on-terminal/` | Эталонный cyberpunk-циферблат (FR945, проверен на часах) |
| `scripts/gen_font.py` | TTF → пиксельный BMFont (`.fnt` + `.png`) без сглаживания |
| `scripts/gen_icon.py` | Иконка лаунчера: пиксельный бот |
| `scripts/preview_n3on.py` | PNG-превью без симулятора |
| `docs/build-and-run-mac.md` | Сборка, симулятор, sideload, публикация |

## Использование
```bash
git clone https://github.com/vitalikryzhenkous/connectiq-watchface-kit.git
cd connectiq-watchface-kit
claude            # скилл и команды подхватятся из .claude/
```
Примеры:
- `/wf-new минималистичный янтарный аналог для fenix7`
- `/wf-add-device templates/n3on-terminal fr955 fenix7 fr965`
- `/wf-debug <вывод компилятора>`
- `/wf-store templates/n3on-terminal`

Новые циферблаты создаются в `faces/<slug>/`.

## Скрипты
```bash
pip install pillow
python3 scripts/gen_font.py --ttf /path/Mono.ttf --size 14 --name term_small --out faces/x/resources/fonts
python3 scripts/gen_icon.py --out faces/x/resources/drawables/launcher_icon.png
python3 scripts/preview_n3on.py templates/n3on-terminal preview.png
```

## Безопасность и лицензии
- Код под **MIT** (`LICENSE`). Пиксельные шрифты сделаны из DejaVu Sans Mono, см. `templates/n3on-terminal/resources/fonts/LICENSE-DejaVu.txt`.
- **Никогда не коммить** `developer_key` (`*.der`, `*.pem`). Они уже в `.gitignore`. Потерянный или утёкший ключ означает, что обновить приложение в сторе будет нельзя.
- Форкаешь шаблон, чтобы опубликовать свой циферблат? Сгенерируй **новый UUID** в `manifest.xml`: `python3 -c "import uuid;print(uuid.uuid4().hex)"`.
- Используй только оригинальный дизайн, без чужих логотипов и персонажей. Не ставь «Garmin» в название приложения.

## Магазин
N3on Terminal готовится к публикации в Connect IQ Store. Тексты на 4 языках, скриншоты и иконка лежат в `templates/n3on-terminal/store/`.

## Скилл глобально (во всех проектах)
```bash
mkdir -p ~/.claude/skills ~/.claude/commands
ln -s "$PWD/.claude/skills/connectiq-watchface" ~/.claude/skills/connectiq-watchface
ln -s "$PWD"/.claude/commands/wf-*.md ~/.claude/commands/
```
