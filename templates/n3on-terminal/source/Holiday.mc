import Toybox.Graphics;
import Toybox.Lang;

// Date-based holiday looks for N3o. Accessories are drawn on top of the bot
// after Bot.draw(), so every mood keeps working underneath.
module Holiday {

    const NONE      = 0;
    const HALLOWEEN = 1; // Oct 24-31
    const CHRISTMAS = 2; // Dec 24-26
    const NEWYEAR   = 3; // Dec 31 - Jan 1
    const VALENTINE = 4; // Feb 14
    const EASTER    = 5; // Western Easter, Fri..Mon
    const WINTER    = 6; // rest of Dec-Feb: scarf

    const ORANGE = 0xFF5500;
    const RED    = 0xFF0000;
    const GREEN  = 0x00AA00;
    const PINK   = 0xFF55AA;

    function of(year, month, day) {
        if (month == 10 && day >= 24) { return HALLOWEEN; }
        if ((month == 12 && day == 31) || (month == 1 && day == 1)) { return NEWYEAR; }
        if (month == 12 && day >= 24 && day <= 26) { return CHRISTMAS; }
        if (month == 2 && day == 14) { return VALENTINE; }
        if (isEasterWindow(year, month, day)) { return EASTER; }
        if (month == 12 || month == 1 || month == 2) { return WINTER; }
        return NONE;
    }

    // Anonymous Gregorian algorithm (Meeus/Jones/Butcher)
    function easter(year) {
        var a = year % 19;
        var b = year / 100;
        var c = year % 100;
        var d = b / 4;
        var e = b % 4;
        var f = (b + 8) / 25;
        var g = (b - f + 1) / 3;
        var h = (19 * a + b - d - g + 15) % 30;
        var i = c / 4;
        var k = c % 4;
        var l = (32 + 2 * e + 2 * i - h - k) % 7;
        var m = (a + 11 * h + 22 * l) / 451;
        var month = (h + l - 7 * m + 114) / 31;
        var day = ((h + l - 7 * m + 114) % 31) + 1;
        return [month, day];
    }

    function isEasterWindow(year, month, day) {
        var e = easter(year);
        var target = e[0] * 31 + e[1];
        var now = month * 31 + day;
        return now >= target - 2 && now <= target + 1;
    }

    // Draw the accessory for `holiday` on a bot placed at (x, y).
    function draw(dc, x, y, pal as Array<Number>, holiday, mood) {
        var tr = Graphics.COLOR_TRANSPARENT;
        var hatOk = (mood != Bot.RAIN); // the umbrella already covers the head
        var leftFree = (mood != Bot.NOTIFY && mood != Bot.HAPPY); // bubble / sparkle area

        if (holiday == HALLOWEEN) {
            // pumpkin at the bot's feet (right, clear of the time digits), bat on the left
            dc.setColor(ORANGE, tr);
            dc.fillRectangle(x + 37, y + 58, 13, 9);
            dc.fillRectangle(x + 39, y + 56, 9, 2);
            dc.setColor(GREEN, tr);
            dc.fillRectangle(x + 43, y + 53, 2, 3);
            dc.setColor(Graphics.COLOR_BLACK, tr);
            dc.fillRectangle(x + 40, y + 60, 2, 2);
            dc.fillRectangle(x + 45, y + 60, 2, 2);
            dc.fillRectangle(x + 41, y + 64, 6, 1);
            if (leftFree) {
                dc.setColor(pal[Theme.DIM], tr);
                dc.fillRectangle(x - 16, y + 6, 10, 2);
                dc.fillRectangle(x - 13, y + 4, 4, 6);
                dc.fillRectangle(x - 18, y + 4, 2, 2);
                dc.fillRectangle(x - 6, y + 4, 2, 2);
            }
        } else if (holiday == CHRISTMAS && hatOk) {
            // red hat with white trim and pom (covers the antenna)
            dc.setColor(RED, tr);
            dc.fillRectangle(x + 4, y + 9, 30, 5);
            dc.fillRectangle(x + 8, y + 5, 22, 4);
            dc.fillRectangle(x + 12, y + 1, 16, 4);
            dc.fillRectangle(x + 18, y - 2, 14, 3);
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x + 1, y + 13, 36, 3);
            dc.fillRectangle(x + 31, y - 5, 5, 5);
        } else if (holiday == NEWYEAR) {
            if (hatOk) {
                dc.setColor(pal[Theme.ACCENT], tr);
                dc.fillRectangle(x + 12, y + 9, 14, 5);
                dc.fillRectangle(x + 16, y + 1, 6, 4);
                dc.setColor(pal[Theme.HILITE], tr);
                dc.fillRectangle(x + 14, y + 5, 10, 4);
                dc.fillRectangle(x + 18, y - 2, 2, 3);
                // cover the antenna stem between hat and head
                dc.setColor(pal[Theme.ACCENT], tr);
                dc.fillRectangle(x + 12, y + 14, 14, 2);
            }
            // confetti
            dc.setColor(pal[Theme.PRIMARY], tr);
            dc.fillRectangle(x - 6, y + 4, 2, 2);
            dc.fillRectangle(x + 44, y + 20, 2, 2);
            dc.setColor(pal[Theme.HILITE], tr);
            dc.fillRectangle(x - 10, y + 14, 2, 2);
            dc.fillRectangle(x + 40, y + 6, 2, 2);
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 2, y - 2, 2, 2);
            dc.fillRectangle(x + 42, y + 34, 2, 2);
        } else if (holiday == VALENTINE) {
            if (mood == Bot.NORMAL) {
                // heart eyes
                dc.setColor(pal[Theme.PRIMARY], tr);
                dc.fillRectangle(x + 8, y + 24, 22, 8);
                heart(dc, x + 10, y + 25, RED);
                heart(dc, x + 23, y + 25, RED);
            }
            if (leftFree) {
                heart(dc, x - 12, y + 2, PINK);
                heart(dc, x - 6, y + 10, RED);
            }
        } else if (holiday == EASTER && mood != Bot.MORNING) {
            // painted egg in the right hand
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x + 41, y + 43, 6, 9);
            dc.fillRectangle(x + 42, y + 42, 4, 1);
            dc.fillRectangle(x + 42, y + 52, 4, 1);
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 41, y + 45, 6, 1);
            dc.setColor(pal[Theme.PRIMARY], tr);
            dc.fillRectangle(x + 41, y + 48, 6, 1);
        } else if (holiday == WINTER) {
            // scarf between head and body
            dc.setColor(RED, tr);
            dc.fillRectangle(x + 4, y + 44, 30, 4);
            dc.fillRectangle(x + 24, y + 48, 5, 9);
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x + 4, y + 45, 30, 1);
            dc.fillRectangle(x + 24, y + 53, 5, 1);
        }
    }

    // 5x5 pixel heart with top-left at (x, y)
    function heart(dc, x, y, color) {
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(x, y + 1, 5, 2);
        dc.fillRectangle(x + 1, y, 1, 1);
        dc.fillRectangle(x + 3, y, 1, 1);
        dc.fillRectangle(x + 1, y + 3, 3, 1);
        dc.fillRectangle(x + 2, y + 4, 1, 1);
    }
}
