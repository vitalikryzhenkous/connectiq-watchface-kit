// Color themes. All values are from the 64-color MIP palette
// (each RGB channel is 00, 55, AA or FF), so they render exactly on FR945.
// Contrast on black (WCAG): text colors are >= 7:1, decor may be lower.
module Theme {

    const PRIMARY = 0;   // main text, visor
    const ACCENT  = 1;   // header, glitch shadow, values
    const HILITE  = 2;   // date, antenna, sunrise
    const DIM     = 3;   // decor only (sleeping bot, bat) - 2.8:1, never for text
    const OK      = 4;   // status "online"
    const BOT     = 5;   // bot body
    const SCAN    = 6;   // scanlines
    const MUTED   = 7;   // secondary text: "offline", "--", "no gps fix" - 9:1

    const HIGH_CONTRAST = 3; // theme index that also disables scanlines and glitch

    const PALETTES = [
        // Neon: cyan / magenta / yellow (magenta FF55AA = 7.1:1)
        [0x00FFFF, 0xFF55AA, 0xFFFF00, 0x555555, 0x00FF55, 0xAA00AA, 0x000055, 0xAAAAAA],
        // Amber CRT
        [0xFFAA00, 0xFF5500, 0xFFFF55, 0x555555, 0xFFAA00, 0xAA5500, 0x550000, 0xAAAAAA],
        // Green terminal
        [0x00FF00, 0x55AA55, 0xAAFF55, 0x555555, 0x55FF55, 0x00AA00, 0x005500, 0xAAAAAA],
        // High contrast: white / yellow / cyan, no scanlines, no glitch
        [0xFFFFFF, 0xFFFF00, 0x00FFFF, 0x555555, 0x55FF55, 0xAA00AA, 0x000000, 0xAAAAAA]
    ];
}
