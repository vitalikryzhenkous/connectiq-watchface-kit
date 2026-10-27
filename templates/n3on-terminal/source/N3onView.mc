import Toybox.Activity;
import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.WatchUi;
import Toybox.Weather;

class N3onView extends WatchUi.WatchFace {

    const DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

    private var _fSmall = null;
    private var _fBig = null;
    private var _ox = 0;
    private var _oy = 0;
    private var _awake = true;

    // settings
    private var _pal = Theme.PALETTES[0];
    private var _scan = true;
    private var _glitch = true;
    private var _showBot = true;

    // sunrise / sunset cache
    private var _sunKey = null;
    private var _sunRise = null;
    private var _sunSet = null;
    private var _savedLoc = null;

    function initialize() {
        WatchFace.initialize();
        loadSettings();
    }

    function onLayout(dc) {
        _fSmall = WatchUi.loadResource(Rez.Fonts.TermSmall);
        _fBig = WatchUi.loadResource(Rez.Fonts.TermBig);
        // layout is designed for 240x240, center it on other screens
        _ox = (dc.getWidth() - 240) / 2;
        _oy = (dc.getHeight() - 240) / 2;
    }

    function loadSettings() {
        var theme = readProp("Theme", 0);
        if (!(theme instanceof Number) || theme < 0 || theme >= Theme.PALETTES.size()) {
            theme = 0;
        }
        _pal = Theme.PALETTES[theme];
        _scan = readProp("Scanlines", true);
        _glitch = readProp("Glitch", true);
        _showBot = readProp("ShowBot", true);
    }

    function onEnterSleep() {
        _awake = false;
        WatchUi.requestUpdate();
    }

    function onExitSleep() {
        _awake = true;
        WatchUi.requestUpdate();
    }

    function onUpdate(dc) {
        var tr = Graphics.COLOR_TRANSPARENT;
        var clock = System.getClockTime();
        var settings = System.getDeviceSettings();
        var battery = System.getSystemStats().battery;
        var act = ActivityMonitor.getInfo();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        // scanlines
        if (_scan) {
            dc.setColor(_pal[Theme.SCAN], tr);
            for (var y = 6; y < 240; y += 8) {
                dc.drawLine(_ox, _oy + y, _ox + 240, _oy + y);
            }
        }

        // header
        txt(dc, 120, 18, _pal[Theme.ACCENT], "[ sys://n3on-0x1 ]", Graphics.TEXT_JUSTIFY_CENTER);
        dc.setColor(_pal[Theme.ACCENT], tr);
        dc.drawLine(_ox + 42, _oy + 37, _ox + 198, _oy + 37);
        txt(dc, 26, 42, _pal[Theme.PRIMARY], "> uptime", Graphics.TEXT_JUSTIFY_LEFT);

        // time with glitch shadow
        var h = clock.hour;
        if (!settings.is24Hour) {
            h = h % 12;
            if (h == 0) { h = 12; }
        }
        var timeStr = h.format("%02d") + ":" + clock.min.format("%02d");
        if (_glitch) {
            dc.setColor(_pal[Theme.ACCENT], tr);
            dc.drawText(_ox + 21, _oy + 59, _fBig, timeStr, Graphics.TEXT_JUSTIFY_LEFT);
            var shift = (clock.min % 4) * 5;
            dc.fillRectangle(_ox + 8, _oy + 80 + shift, 18, 3);
            dc.setColor(_pal[Theme.HILITE], tr);
            dc.fillRectangle(_ox + 130 + shift, _oy + 70, 14, 2);
        }
        dc.setColor(_pal[Theme.PRIMARY], tr);
        dc.drawText(_ox + 24, _oy + 57, _fBig, timeStr, Graphics.TEXT_JUSTIFY_LEFT);

        // date
        var d = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        var dateStr = "> " + DAYS[d.day_of_week - 1] + " " + d.day.format("%02d") + "." +
            d.month.format("%02d") + "." + (d.year % 100).format("%02d");
        txt(dc, 24, 114, _pal[Theme.HILITE], dateStr, Graphics.TEXT_JUSTIFY_LEFT);

        // weather + location for the sun calculation
        var temp = null;
        var kind = -1;
        var loc = null;
        if (Toybox has :Weather) {
            var cc = Weather.getCurrentConditions();
            if (cc != null) {
                if (cc.temperature != null) {
                    var tf = cc.temperature.toFloat();
                    if (settings.temperatureUnits == System.UNIT_STATUTE) {
                        tf = tf * 9.0 / 5.0 + 32.0;
                    }
                    temp = (tf + (tf >= 0 ? 0.5 : -0.5)).toNumber();
                }
                if (cc.condition != null) {
                    kind = WeatherIcon.kindOf(cc.condition);
                }
                if (cc.observationLocationPosition != null) {
                    loc = cc.observationLocationPosition.toDegrees();
                }
            }
        }
        if (loc == null) {
            var ai = Activity.getActivityInfo();
            if (ai != null && ai.currentLocation != null) {
                loc = ai.currentLocation.toDegrees();
            }
        }
        loc = cacheLocation(loc);

        var x = 16;
        x = seg(dc, x, 134, _pal[Theme.PRIMARY], "> wx ");
        if (temp == null) {
            x = seg(dc, x, 134, _pal[Theme.DIM], "--");
        } else {
            x = seg(dc, x, 134, _pal[Theme.ACCENT], (temp > 0 ? "+" : "") + temp + "°");
            x = seg(dc, x, 134, _pal[Theme.PRIMARY], " " + WeatherIcon.label(kind));
            WeatherIcon.draw(dc, _ox + x + 8, _oy + 136, kind, _pal);
        }

        // sunrise / sunset
        updateSun(loc, d, clock);
        x = 12;
        x = seg(dc, x, 154, _pal[Theme.PRIMARY], "> sun ");
        x = seg(dc, x, 154, _pal[Theme.HILITE], "▲" + hm(_sunRise, settings.is24Hour));
        x = seg(dc, x, 154, _pal[Theme.ACCENT], " ▼" + hm(_sunSet, settings.is24Hour));

        // steps + battery
        var steps = (act.steps != null) ? act.steps : 0;
        var stepStr = (steps < 1000) ? steps.toString() : (steps / 1000.0).format("%.1f") + "k";
        x = 20;
        x = seg(dc, x, 174, _pal[Theme.PRIMARY], "> stp ");
        x = seg(dc, x, 174, _pal[Theme.ACCENT], stepStr);
        x = seg(dc, x, 174, _pal[Theme.PRIMARY], "  bat ");
        seg(dc, x, 174, battery < 20 ? _pal[Theme.ACCENT] : _pal[Theme.HILITE], battery.toNumber().format("%d") + "%");

        // status line
        dc.setColor(_pal[Theme.ACCENT], tr);
        dc.drawLine(_ox + 46, _oy + 196, _ox + 194, _oy + 196);
        var online = settings.phoneConnected;
        var stColor = online ? _pal[Theme.OK] : _pal[Theme.DIM];
        dc.setColor(stColor, tr);
        dc.fillCircle(_ox + 78, _oy + 210, 4);
        x = seg(dc, 88, 201, stColor, online ? "online" : "offline");
        if (!_awake || clock.sec % 2 == 0) {
            seg(dc, x, 201, _pal[Theme.HILITE], "_");
        }

        // bot
        if (_showBot) {
            var mood = Bot.NORMAL;
            var nowMin = clock.hour * 60 + clock.min;
            var goal = act.stepGoal;
            if (battery < 20) {
                mood = Bot.LOW;
            } else if (_sunRise != null && _sunSet != null && (nowMin < _sunRise || nowMin >= _sunSet)) {
                mood = Bot.NIGHT;
            } else if (goal != null && goal > 0 && steps >= goal) {
                mood = Bot.HAPPY;
            }
            var blink = _awake && (clock.sec % 7 == 0);
            Bot.draw(dc, _ox + 178, _oy + 46, _pal, mood, blink, _fSmall);
        }
    }

    // ---- helpers ----

    private function txt(dc, x, y, color, s, just) {
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(_ox + x, _oy + y, _fSmall, s, just);
    }

    // draws a text segment and returns the x where the next one starts
    private function seg(dc, x, y, color, s) {
        txt(dc, x, y, color, s, Graphics.TEXT_JUSTIFY_LEFT);
        return x + dc.getTextWidthInPixels(s, _fSmall);
    }

    private function hm(minutes, is24) {
        if (minutes == null) {
            return "--:--";
        }
        var h = minutes / 60;
        if (!is24) {
            h = h % 12;
            if (h == 0) { h = 12; }
        }
        return h.format("%02d") + ":" + (minutes % 60).format("%02d");
    }

    private function updateSun(loc, d, clock) {
        if (loc == null) {
            return;
        }
        var key = d.year * 1000 + Sun.dayOfYear(d.year, d.month, d.day);
        var lat = loc[0];
        var lon = loc[1];
        var fullKey = "" + key + ":" + (lat * 10).toNumber() + ":" + (lon * 10).toNumber() + ":" + clock.timeZoneOffset;
        if (fullKey.equals(_sunKey)) {
            return;
        }
        var doy = Sun.dayOfYear(d.year, d.month, d.day);
        var tz = clock.timeZoneOffset / 3600.0;
        _sunRise = Sun.calc(doy, lat, lon, tz, true);
        _sunSet = Sun.calc(doy, lat, lon, tz, false);
        _sunKey = fullKey;
    }

    // keeps the last known position so sunrise/sunset survive a restart
    private function cacheLocation(loc) {
        try {
            if (loc != null && !(loc[0] == 0.0 && loc[1] == 0.0)) {
                var lat = loc[0].toFloat();
                var lon = loc[1].toFloat();
                // write only when the position really changed (~1 km)
                if (_savedLoc == null || (lat - _savedLoc[0]).abs() > 0.01 || (lon - _savedLoc[1]).abs() > 0.01) {
                    _savedLoc = [lat, lon];
                    Application.Storage.setValue("loc", _savedLoc);
                }
                return loc;
            }
            if (_savedLoc == null) {
                _savedLoc = Application.Storage.getValue("loc");
            }
            return _savedLoc;
        } catch (e) {
            return loc;
        }
    }

    private function readProp(key, def) {
        try {
            var v = Application.Properties.getValue(key);
            return (v == null) ? def : v;
        } catch (e) {
            return def;
        }
    }
}
