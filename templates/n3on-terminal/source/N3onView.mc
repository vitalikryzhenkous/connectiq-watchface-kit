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
    private var _fJa = null;   // loaded only when Japanese is needed
    private var _ox = 0;
    private var _oy = 0;
    private var _awake = true;

    // settings
    private var _pal = Theme.PALETTES[0];
    private var _scan = true;
    private var _glitch = 2;     // 0 off, 1 on wake (~3 s), 2 always
    private var _showBot = true;
    private var _manLoc = null; // manual [lat, lon] from settings
    private var _emotions = true;
    private var _holidays = true;
    private var _holiday = 0;
    private var _holidayDay = -1;

    // bot phrases (first line)
    private var _lang = 0;
    private var _phraseMode = 0; // 0 auto, 1 my phrase only, 2 mixed
    private var _custom = "";
    private var _typing = true;
    private var _wakeSec = 0;    // when the watch last woke up (typing + glitch burst)

    // step-rate tracking for the RUN mood (sampled once per minute)
    private var _rateMin = -1;
    private var _rateSteps = 0;
    private var _active = false;

    // sunrise / sunset cache
    private var _sunKey = null;
    private var _sunRise = null;
    private var _sunSet = null;
    private var _savedLoc = null;

    function initialize() {
        WatchFace.initialize();
        _wakeSec = Time.now().value();
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
        var g = readProp("Glitch", 2);
        if (g instanceof Boolean) {
            g = g ? 2 : 0; // older boolean setting
        }
        _glitch = (g instanceof Number && g >= 0 && g <= 2) ? g : 2;
        if (theme == Theme.HIGH_CONTRAST) {
            _scan = false;
            _glitch = 0;
        }
        _showBot = readProp("ShowBot", true);
        _emotions = readProp("Emotions", true);
        _holidays = readProp("Holidays", true);

        var langSetting = readProp("Language", 0);
        _lang = Phrases.resolveLanguage(langSetting instanceof Number ? langSetting : 0);
        var mode = readProp("PhraseMode", 0);
        _phraseMode = (mode instanceof Number && mode >= 0 && mode <= 2) ? mode : 0;
        var custom = readProp("Phrase", "");
        _custom = (custom instanceof String) ? custom : "";
        if (_custom.length() > 14) {
            _custom = _custom.substring(0, 14);
        }
        if (hasJa(_custom) && _custom.length() > 9) {
            _custom = _custom.substring(0, 9); // kana are 12px wide: keep clear of the bot
        }
        _typing = readProp("Typing", true);
        // the Japanese font costs memory: load it only when it can be shown
        if (_lang == Phrases.JA || hasJa(_custom)) {
            if (_fJa == null) {
                _fJa = WatchUi.loadResource(Rez.Fonts.TermJa);
            }
        } else {
            _fJa = null;
        }
        var lat = readProp("Lat", 0.0);
        var lon = readProp("Lon", 0.0);
        _manLoc = null;
        if ((lat instanceof Number || lat instanceof Float || lat instanceof Double) &&
            (lon instanceof Number || lon instanceof Float || lon instanceof Double) &&
            !(lat == 0 && lon == 0) && lat.abs() <= 90 && lon.abs() <= 180) {
            _manLoc = [lat.toFloat(), lon.toFloat()];
        }
    }

    function onEnterSleep() {
        _awake = false;
        WatchUi.requestUpdate();
    }

    function onExitSleep() {
        _awake = true;
        _wakeSec = Time.now().value();
        WatchUi.requestUpdate();
    }

    function onUpdate(dc) {
        var tr = Graphics.COLOR_TRANSPARENT;
        var clock = System.getClockTime();
        var settings = System.getDeviceSettings();
        var battery = System.getSystemStats().battery;
        var act = ActivityMonitor.getInfo();
        var nowSec = Time.now().value();

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
        // first line (bot phrase) is drawn at the end, once the mood is known

        // time with glitch shadow: always, or only ~3 s after waking up
        var h = clock.hour;
        if (!settings.is24Hour) {
            h = h % 12;
            if (h == 0) { h = 12; }
        }
        var timeStr = h.format("%02d") + ":" + clock.min.format("%02d");
        if (_glitch == 2 || (_glitch == 1 && _awake && (nowSec - _wakeSec) < 3)) {
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
        // data lines follow the curve of the round screen: x = 12, 14, 20, 30
        txt(dc, 12, 114, _pal[Theme.HILITE], dateStr, Graphics.TEXT_JUSTIFY_LEFT);

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
        loc = (_manLoc != null) ? _manLoc : cacheLocation(loc);

        var x = 14;
        x = seg(dc, x, 134, _pal[Theme.PRIMARY], "> wx ");
        if (temp == null) {
            x = seg(dc, x, 134, _pal[Theme.MUTED], "--");
        } else {
            x = seg(dc, x, 134, _pal[Theme.ACCENT], (temp > 0 ? "+" : "") + temp + "°");
            x = seg(dc, x, 134, _pal[Theme.PRIMARY], " " + WeatherIcon.label(kind));
            WeatherIcon.draw(dc, _ox + x + 8, _oy + 136, kind, _pal);
        }

        // sunrise / sunset
        updateSun(loc, d, clock);
        x = 20;
        x = seg(dc, x, 154, _pal[Theme.PRIMARY], "> sun ");
        if (_sunRise == null && _sunSet == null && loc == null) {
            // no position yet: hint instead of --:--
            seg(dc, x, 154, _pal[Theme.MUTED], "no gps fix");
        } else {
            x = seg(dc, x, 154, _pal[Theme.HILITE], "▲" + hm(_sunRise, settings.is24Hour));
            x = seg(dc, x, 154, _pal[Theme.ACCENT], " ▼" + hm(_sunSet, settings.is24Hour));
        }

        // steps + battery
        var steps = (act.steps != null) ? act.steps : 0;
        var stepStr = (steps < 1000) ? steps.toString() : (steps / 1000.0).format("%.1f") + "k";
        x = 30;
        x = seg(dc, x, 174, _pal[Theme.PRIMARY], "> stp ");
        x = seg(dc, x, 174, _pal[Theme.ACCENT], stepStr);
        x = seg(dc, x, 174, _pal[Theme.PRIMARY], "  bat ");
        seg(dc, x, 174, battery < 20 ? _pal[Theme.ACCENT] : _pal[Theme.HILITE], battery.toNumber().format("%d") + "%");

        // status line
        dc.setColor(_pal[Theme.ACCENT], tr);
        dc.drawLine(_ox + 46, _oy + 196, _ox + 194, _oy + 196);
        var online = settings.phoneConnected;
        var stColor = online ? _pal[Theme.OK] : _pal[Theme.MUTED];
        dc.setColor(stColor, tr);
        dc.fillCircle(_ox + 78, _oy + 210, 4);
        seg(dc, 88, 201, stColor, online ? "online" : "offline");

        // mood + holiday (also drive the phrase, even if the bot is hidden)
        var nowMin = clock.hour * 60 + clock.min;
        updateActivity(nowMin, steps);
        var mood = pickMood(nowMin, battery, steps, act.stepGoal, settings, kind);
        var holiday = Holiday.NONE;
        if (_holidays) {
            var dayKey = d.year * 400 + d.month * 32 + d.day;
            if (dayKey != _holidayDay) {
                _holiday = Holiday.of(d.year, d.month, d.day);
                _holidayDay = dayKey;
            }
            holiday = _holiday;
        }

        // bot
        if (_showBot) {
            var blink = _awake && (clock.sec % 7 == 0);
            var phase = _awake && (clock.sec % 2 == 0);
            Bot.draw(dc, _ox + 178, _oy + 46, _pal, mood, blink, phase, _fSmall);
            if (holiday != Holiday.NONE) {
                Holiday.draw(dc, _ox + 178, _oy + 46, _pal, holiday, mood);
            }
        }

        // first line: what N3o says
        var n = settings.notificationCount;
        drawPhrase(dc, currentPhrase(mood, holiday, clock.hour, (n != null) ? n : 0), nowSec);
    }

    // ---- bot phrase ----

    private function currentPhrase(mood, holiday, hour, notifyCount) {
        var hasCustom = (_custom.length() > 0);
        if (_phraseMode == 1 && hasCustom) {
            return _custom;
        }
        var sit = Phrases.S_IDLE;
        if (mood == Bot.LOW) {
            sit = Phrases.S_LOW;
        } else if (mood == Bot.NOTIFY) {
            sit = Phrases.S_NOTIFY;
        } else if (mood == Bot.NIGHT) {
            sit = Phrases.S_NIGHT;
        } else if (mood == Bot.HAPPY) {
            sit = Phrases.S_GOAL;
        } else if (mood == Bot.RUN) {
            sit = Phrases.S_RUN;
        } else if (mood == Bot.RAIN) {
            sit = Phrases.S_RAIN;
        } else if (mood == Bot.MORNING) {
            sit = Phrases.S_MORNING;
        } else if (holiday == Holiday.HALLOWEEN) {
            sit = Phrases.S_HALLOWEEN;
        } else if (holiday == Holiday.CHRISTMAS) {
            sit = Phrases.S_XMAS;
        } else if (holiday == Holiday.NEWYEAR) {
            sit = Phrases.S_NEWYEAR;
        } else if (holiday == Holiday.VALENTINE) {
            sit = Phrases.S_VALENTINE;
        } else if (holiday == Holiday.EASTER) {
            sit = Phrases.S_EASTER;
        }
        if (sit == Phrases.S_IDLE && _phraseMode == 2 && hasCustom && hour % 2 == 0) {
            return _custom;
        }
        return Phrases.get(_lang, sit, hour, notifyCount);
    }

    // "> " + phrase; types in 3 characters per second after waking up, then a blinking cursor
    private function drawPhrase(dc, text, nowSec) {
        var x = seg(dc, 26, 42, _pal[Theme.PRIMARY], "> ");
        var shown = text;
        var typingNow = false;
        if (_typing && _awake) {
            var count = (nowSec - _wakeSec + 1) * 3;
            if (count > 0 && count < text.length()) {
                shown = text.substring(0, count);
                typingNow = true;
            }
        }
        var ja = (_fJa != null && hasJa(text));
        var font = ja ? _fJa : _fSmall;
        dc.setColor(_pal[Theme.PRIMARY], Graphics.COLOR_TRANSPARENT);
        dc.drawText(_ox + x, _oy + (ja ? 44 : 42), font, shown, Graphics.TEXT_JUSTIFY_LEFT);
        if (_awake && (typingNow || nowSec % 2 == 0)) {
            seg(dc, x + dc.getTextWidthInPixels(shown, font), 42, _pal[Theme.HILITE], "_");
        }
    }

    private function hasJa(text) {
        var chars = text.toCharArray();
        for (var i = 0; i < chars.size(); i++) {
            if (chars[i].toNumber() >= 0x3000) {
                return true;
            }
        }
        return false;
    }

    // ---- bot mood ----

    // Priority: low battery > notification > night > goal > active > rain > morning > normal
    private function pickMood(nowMin, battery, steps, goal, settings, kind) {
        if (battery < 20) {
            return Bot.LOW;
        }
        var haveSun = (_sunRise != null && _sunSet != null && _sunSet > _sunRise);
        if (_emotions && settings.notificationCount != null && settings.notificationCount > 0) {
            return Bot.NOTIFY;
        }
        if (haveSun && (nowMin < _sunRise || nowMin >= _sunSet)) {
            return Bot.NIGHT;
        }
        if (goal != null && goal > 0 && steps >= goal) {
            return Bot.HAPPY;
        }
        if (!_emotions) {
            return Bot.NORMAL;
        }
        if (_active) {
            return Bot.RUN;
        }
        if (kind == WeatherIcon.RAIN || kind == WeatherIcon.STORM || kind == WeatherIcon.SNOW) {
            return Bot.RAIN;
        }
        if (haveSun && nowMin >= _sunRise && nowMin < _sunRise + 60) {
            return Bot.MORNING;
        }
        return Bot.NORMAL;
    }

    // ~100+ steps per minute since the last sample = running / brisk walking
    private function updateActivity(nowMin, steps) {
        if (nowMin == _rateMin) {
            return;
        }
        var elapsed = nowMin - _rateMin;
        if (_rateMin >= 0 && elapsed > 0 && elapsed <= 3 && steps >= _rateSteps) {
            _active = ((steps - _rateSteps) / elapsed) >= 100;
        } else {
            _active = false; // first sample, midnight reset or a long gap
        }
        _rateMin = nowMin;
        _rateSteps = steps;
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
