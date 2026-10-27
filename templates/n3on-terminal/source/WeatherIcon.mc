import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Weather;

// Maps Garmin weather conditions to 6 pixel icons and short labels.
module WeatherIcon {

    const SUN = 0;
    const CLOUD = 1;
    const RAIN = 2;
    const SNOW = 3;
    const STORM = 4;
    const FOG = 5;

    function kindOf(c) {
        if (c == Weather.CONDITION_CLEAR || c == Weather.CONDITION_MOSTLY_CLEAR ||
            c == Weather.CONDITION_PARTLY_CLEAR || c == Weather.CONDITION_FAIR) {
            return SUN;
        }
        if (c == Weather.CONDITION_THUNDERSTORMS || c == Weather.CONDITION_SCATTERED_THUNDERSTORMS ||
            c == Weather.CONDITION_CHANCE_OF_THUNDERSTORMS) {
            return STORM;
        }
        if (c == Weather.CONDITION_SNOW || c == Weather.CONDITION_LIGHT_SNOW ||
            c == Weather.CONDITION_HEAVY_SNOW || c == Weather.CONDITION_WINTRY_MIX ||
            c == Weather.CONDITION_RAIN_SNOW || c == Weather.CONDITION_LIGHT_RAIN_SNOW ||
            c == Weather.CONDITION_HEAVY_RAIN_SNOW || c == Weather.CONDITION_SLEET ||
            c == Weather.CONDITION_HAIL || c == Weather.CONDITION_ICE ||
            c == Weather.CONDITION_FLURRIES || c == Weather.CONDITION_ICE_SNOW ||
            c == Weather.CONDITION_FREEZING_RAIN) {
            return SNOW;
        }
        if (c == Weather.CONDITION_RAIN || c == Weather.CONDITION_LIGHT_RAIN ||
            c == Weather.CONDITION_HEAVY_RAIN || c == Weather.CONDITION_SHOWERS ||
            c == Weather.CONDITION_LIGHT_SHOWERS || c == Weather.CONDITION_HEAVY_SHOWERS ||
            c == Weather.CONDITION_SCATTERED_SHOWERS || c == Weather.CONDITION_CHANCE_OF_SHOWERS ||
            c == Weather.CONDITION_DRIZZLE || c == Weather.CONDITION_UNKNOWN_PRECIPITATION) {
            return RAIN;
        }
        if (c == Weather.CONDITION_FOG || c == Weather.CONDITION_MIST ||
            c == Weather.CONDITION_HAZY || c == Weather.CONDITION_HAZE ||
            c == Weather.CONDITION_SMOKE || c == Weather.CONDITION_DUST) {
            return FOG;
        }
        return CLOUD;
    }

    function label(kind) {
        if (kind == SUN) { return "clear"; }
        if (kind == RAIN) { return "rain"; }
        if (kind == SNOW) { return "snow"; }
        if (kind == STORM) { return "storm"; }
        if (kind == FOG) { return "fog"; }
        return "cloudy";
    }

    // draws an ~18x14 pixel icon with top-left at (x, y)
    function draw(dc, x, y, kind, pal as Array<Number>) {
        var tr = Graphics.COLOR_TRANSPARENT;
        if (kind == SUN) {
            dc.setColor(pal[Theme.HILITE], tr);
            dc.fillCircle(x + 8, y + 7, 4);
            dc.fillRectangle(x + 7, y, 2, 2);
            dc.fillRectangle(x + 7, y + 13, 2, 2);
            dc.fillRectangle(x + 1, y + 6, 2, 2);
            dc.fillRectangle(x + 14, y + 6, 2, 2);
            return;
        }
        if (kind == FOG) {
            dc.setColor(0xAAAAAA, tr);
            dc.fillRectangle(x, y + 3, 16, 2);
            dc.fillRectangle(x + 3, y + 7, 14, 2);
            dc.fillRectangle(x, y + 11, 16, 2);
            return;
        }
        // cloud
        dc.setColor(0xAAAAAA, tr);
        dc.fillRectangle(x + 4, y + 2, 6, 4);
        dc.fillRectangle(x + 9, y, 6, 6);
        dc.fillRectangle(x, y + 5, 18, 5);
        if (kind == RAIN) {
            dc.setColor(pal[Theme.PRIMARY], tr);
            dc.fillRectangle(x + 3, y + 12, 2, 3);
            dc.fillRectangle(x + 8, y + 12, 2, 3);
            dc.fillRectangle(x + 13, y + 12, 2, 3);
        } else if (kind == SNOW) {
            dc.setColor(Graphics.COLOR_WHITE, tr);
            dc.fillRectangle(x + 3, y + 12, 2, 2);
            dc.fillRectangle(x + 8, y + 13, 2, 2);
            dc.fillRectangle(x + 13, y + 12, 2, 2);
        } else if (kind == STORM) {
            dc.setColor(pal[Theme.HILITE], tr);
            dc.fillRectangle(x + 9, y + 10, 2, 2);
            dc.fillRectangle(x + 7, y + 12, 2, 2);
            dc.fillRectangle(x + 9, y + 14, 2, 2);
        }
    }
}
