// Color themes. All values are from the 64-color MIP palette
// (each RGB channel is 00, 55, AA or FF), so they render exactly on FR945.
module Theme {

    const PRIMARY = 0;   // main text, visor
    const ACCENT  = 1;   // header, glitch shadow, values
    const HILITE  = 2;   // date, antenna, sunrise
    const DIM     = 3;   // inactive elements
    const OK      = 4;   // status "online"
    const BOT     = 5;   // bot body
    const SCAN    = 6;   // scanlines

    const PALETTES = [
        // Neon: cyan / magenta / yellow
        [0x00FFFF, 0xFF00AA, 0xFFFF00, 0x555555, 0x00FF55, 0xAA00AA, 0x000055],
        // Amber CRT
        [0xFFAA00, 0xFF5500, 0xFFFF55, 0x555555, 0xFFAA00, 0xAA5500, 0x550000],
        // Green terminal
        [0x00FF00, 0x00AA55, 0xAAFF55, 0x555555, 0x55FF55, 0x00AA00, 0x005500]
    ];
}
