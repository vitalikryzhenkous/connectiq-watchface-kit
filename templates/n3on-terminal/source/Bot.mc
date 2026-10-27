import Toybox.Graphics;
import Toybox.Lang;

// Original pixel robot "N3o". Draws inside a ~42x68 box starting at (x, y).
// Extra elements (umbrella, sparkles, bubble, mug) stay within the round
// 240px screen when the bot is placed at (178, 46).
module Bot {

    const NORMAL  = 0;
    const LOW     = 1; // battery < 20 %
    const NIGHT   = 2; // after sunset
    const HAPPY   = 3; // step goal reached
    const RAIN    = 4; // rain / storm / snow in weather
    const NOTIFY  = 5; // unread phone notifications
    const RUN     = 6; // high step rate right now
    const MORNING = 7; // first hour after sunrise

    // phase: toggles every second while awake (used for blinking antenna)
    function draw(dc, x, y, pal as Array<Number>, mood, blink, phase, font) {
        var tr = Graphics.COLOR_TRANSPARENT;
        var dimmed = (mood == LOW || mood == NIGHT);
        var bk = Graphics.COLOR_BLACK;

        // ---- antenna / umbrella / notification ----
        if (mood == RAIN) {
            // handle sits behind the head; canopy covers the antenna
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x + 18, y + 6, 2, 12);
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 8, y - 2, 22, 4);
            dc.fillRectangle(x, y + 2, 38, 4);
            dc.fillRectangle(x - 2, y + 6, 42, 3);
            dc.setColor(pal[Theme.PRIMARY], tr);
            dc.fillRectangle(x - 3, y + 13, 1, 4);
            dc.fillRectangle(x + 41, y + 15, 1, 4);
            dc.fillRectangle(x - 5, y + 22, 1, 4);
            dc.fillRectangle(x + 42, y + 26, 1, 4);
        } else if (mood == LOW) {
            // drooping antenna
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x + 18, y + 8, 2, 8);
            dc.fillRectangle(x + 20, y + 4, 6, 6);
        } else {
            var antColor = pal[Theme.HILITE];
            if (mood == NIGHT) {
                antColor = pal[Theme.DIM];
            } else if (mood == NOTIFY) {
                antColor = phase ? pal[Theme.ACCENT] : pal[Theme.HILITE];
            }
            dc.setColor(antColor, tr);
            dc.fillRectangle(x + 16, y, 6, 6);
            dc.fillRectangle(x + 18, y + 6, 2, 10);
        }
        if (mood == NOTIFY) {
            // rays around the antenna tip
            dc.setColor(pal[Theme.HILITE], tr);
            dc.fillRectangle(x + 12, y - 3, 2, 2);
            dc.fillRectangle(x + 24, y - 3, 2, 2);
            dc.fillRectangle(x + 10, y + 2, 2, 2);
            dc.fillRectangle(x + 26, y + 2, 2, 2);
            // "!" bubble on the left
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x - 18, y - 2, 12, 13);
            dc.fillRectangle(x - 8, y + 11, 3, 3);
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x - 13, y, 2, 6);
            dc.fillRectangle(x - 13, y + 8, 2, 2);
        }

        // ---- head ----
        dc.setColor(pal[Theme.ACCENT], tr);
        dc.setPenWidth(2);
        dc.drawRectangle(x, y + 16, 38, 28);
        dc.setPenWidth(1);

        // visor
        dc.setColor(mood == NIGHT ? pal[Theme.DIM] : pal[Theme.PRIMARY], tr);
        dc.fillRectangle(x + 5, y + 22, 28, 12);

        // eyes
        dc.setColor(bk, tr);
        if (mood == HAPPY) {
            eyeArc(dc, x + 10, y + 25);
            eyeArc(dc, x + 23, y + 25);
        } else if (blink || mood == NIGHT) {
            dc.fillRectangle(x + 10, y + 28, 5, 2);
            dc.fillRectangle(x + 23, y + 28, 5, 2);
        } else if (mood == LOW || mood == MORNING) {
            dc.fillRectangle(x + 10, y + 28, 5, 3);
            dc.fillRectangle(x + 23, y + 28, 5, 3);
        } else if (mood == NOTIFY) {
            // looking left at the bubble
            dc.fillRectangle(x + 8, y + 25, 5, 6);
            dc.fillRectangle(x + 21, y + 25, 5, 6);
        } else {
            dc.fillRectangle(x + 10, y + 25, 5, 6);
            dc.fillRectangle(x + 23, y + 25, 5, 6);
        }

        // mouth
        if (mood == HAPPY || mood == RUN) {
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 8, y + 37, 22, 2);
            dc.fillRectangle(x + 10, y + 39, 18, 2);
        } else if (mood == MORNING) {
            // yawn
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 15, y + 36, 8, 6);
            dc.setColor(bk, tr);
            dc.fillRectangle(x + 17, y + 38, 4, 2);
        } else if (dimmed) {
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x + 14, y + 38, 10, 2);
        } else {
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.fillRectangle(x + 11, y + 37, 16, 3);
        }

        // ---- body ----
        dc.setColor(pal[Theme.BOT], tr);
        dc.fillRectangle(x + 6, y + 48, 26, 14);
        if (mood == LOW) {
            // battery icon with one red cell
            dc.setColor(bk, tr);
            dc.fillRectangle(x + 12, y + 52, 13, 6);
            dc.setColor(pal[Theme.ACCENT], tr);
            dc.drawRectangle(x + 12, y + 52, 13, 6);
            dc.fillRectangle(x + 25, y + 54, 2, 2);
            dc.setColor(Graphics.COLOR_RED, tr);
            dc.fillRectangle(x + 13, y + 53, 3, 4);
        }

        // ---- arms ----
        dc.setColor(pal[Theme.PRIMARY], tr);
        if (mood == HAPPY) {
            dc.fillRectangle(x - 2, y + 40, 3, 12);
            dc.fillRectangle(x + 37, y + 40, 3, 12);
            dc.fillRectangle(x + 1, y + 49, 5, 3);
            dc.fillRectangle(x + 32, y + 49, 5, 3);
        } else if (mood == RUN) {
            dc.fillRectangle(x - 4, y + 46, 8, 3);
            dc.fillRectangle(x + 32, y + 54, 8, 3);
        } else if (mood == MORNING) {
            dc.fillRectangle(x - 2, y + 50, 8, 3);
            dc.fillRectangle(x + 32, y + 50, 9, 3);
        } else {
            dc.fillRectangle(x - 2, y + 50, 8, 3);
            dc.fillRectangle(x + 32, y + 50, 8, 3);
        }

        // ---- legs ----
        if (mood == RUN) {
            dc.fillRectangle(x + 2, y + 63, 6, 5);
            dc.fillRectangle(x + 30, y + 61, 6, 5);
            // motion lines (below the big time digits)
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x - 14, y + 58, 8, 1);
            dc.fillRectangle(x - 18, y + 62, 8, 1);
            dc.fillRectangle(x - 12, y + 66, 8, 1);
        } else {
            dc.fillRectangle(x + 8, y + 63, 6, 5);
            dc.fillRectangle(x + 24, y + 63, 6, 5);
        }

        // ---- extras ----
        if (mood == HAPPY) {
            dc.setColor(pal[Theme.HILITE], tr);
            sparkle(dc, x - 8, y - 2);
            sparkle(dc, x + 42, y + 2);
            sparkle(dc, x + 44, y + 30);
        } else if (mood == MORNING) {
            // coffee mug + steam
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x + 40, y + 45, 8, 8);
            dc.fillRectangle(x + 48, y + 47, 2, 4);
            dc.setColor(pal[Theme.DIM], tr);
            dc.fillRectangle(x + 42, y + 39, 1, 4);
            dc.fillRectangle(x + 45, y + 37, 1, 5);
        } else if (mood == NIGHT) {
            dc.setColor(pal[Theme.DIM], tr);
            dc.drawText(x + 27, y - 4, font, "z", Graphics.TEXT_JUSTIFY_LEFT);
        }
    }

    function eyeArc(dc, x, y) {
        dc.fillRectangle(x + 1, y, 3, 2);
        dc.fillRectangle(x, y + 2, 2, 3);
        dc.fillRectangle(x + 3, y + 2, 2, 3);
    }

    function sparkle(dc, x, y) {
        dc.fillRectangle(x + 2, y, 2, 6);
        dc.fillRectangle(x, y + 2, 6, 2);
    }
}
