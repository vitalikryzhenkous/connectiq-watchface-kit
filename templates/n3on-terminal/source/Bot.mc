import Toybox.Graphics;
import Toybox.Lang;

// Original pixel robot. Draws inside a 42x68 box starting at (x, y).
module Bot {

    const NORMAL = 0;
    const LOW    = 1; // battery < 20 %
    const NIGHT  = 2; // after sunset
    const HAPPY  = 3; // step goal reached

    function draw(dc, x, y, pal as Array<Number>, mood, blink, font) {
        var tr = Graphics.COLOR_TRANSPARENT;
        var dimmed = (mood == LOW || mood == NIGHT);

        // antenna
        dc.setColor(dimmed ? pal[Theme.DIM] : pal[Theme.HILITE], tr);
        dc.fillRectangle(x + 16, y, 6, 6);
        dc.fillRectangle(x + 18, y + 6, 2, 10);

        // head
        dc.setColor(pal[Theme.ACCENT], tr);
        dc.setPenWidth(2);
        dc.drawRectangle(x, y + 16, 38, 28);
        dc.setPenWidth(1);

        // visor
        dc.setColor(mood == NIGHT ? pal[Theme.DIM] : pal[Theme.PRIMARY], tr);
        dc.fillRectangle(x + 5, y + 22, 28, 12);

        // eyes
        dc.setColor(Graphics.COLOR_BLACK, tr);
        if (mood == HAPPY) {
            eyeArc(dc, x + 10, y + 25);
            eyeArc(dc, x + 23, y + 25);
        } else if (blink || mood == NIGHT) {
            dc.fillRectangle(x + 10, y + 28, 5, 2);
            dc.fillRectangle(x + 23, y + 28, 5, 2);
        } else if (mood == LOW) {
            dc.fillRectangle(x + 10, y + 27, 5, 4);
            dc.fillRectangle(x + 23, y + 27, 5, 4);
        } else {
            dc.fillRectangle(x + 10, y + 25, 5, 6);
            dc.fillRectangle(x + 23, y + 25, 5, 6);
        }

        // mouth
        if (mood == HAPPY) {
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 8, y + 37, 22, 2);
            dc.fillRectangle(x + 10, y + 39, 18, 2);
        } else if (dimmed) {
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x + 14, y + 38, 10, 2);
        } else {
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 11, y + 37, 16, 3);
        }

        // body
        dc.setColor(pal[Theme.BOT], tr);
        dc.fillRectangle(x + 6, y + 48, 26, 14);

        // arms (raised when happy)
        dc.setColor(pal[Theme.PRIMARY], tr);
        if (mood == HAPPY) {
            dc.fillRectangle(x - 2, y + 42, 3, 10);
            dc.fillRectangle(x + 37, y + 42, 3, 10);
            dc.fillRectangle(x + 1, y + 49, 5, 3);
            dc.fillRectangle(x + 32, y + 49, 5, 3);
        } else {
            dc.fillRectangle(x - 2, y + 50, 8, 3);
            dc.fillRectangle(x + 32, y + 50, 8, 3);
        }

        // legs
        dc.fillRectangle(x + 8, y + 63, 6, 5);
        dc.fillRectangle(x + 24, y + 63, 6, 5);

        // sleeping
        if (mood == NIGHT) {
            dc.setColor(pal[Theme.DIM], tr);
            dc.drawText(x + 27, y - 4, font, "z", Graphics.TEXT_JUSTIFY_LEFT);
        }
    }

    function eyeArc(dc, x, y) {
        dc.fillRectangle(x + 1, y, 3, 2);
        dc.fillRectangle(x, y + 2, 2, 3);
        dc.fillRectangle(x + 3, y + 2, 2, 3);
    }
}
