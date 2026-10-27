import Toybox.Math;

// Sunrise / sunset calculation (NOAA "Almanac for Computers" algorithm).
// Works fully offline from latitude / longitude; accuracy is about 1-2 minutes.
module Sun {

    const ZENITH = 90.833; // official sunrise/sunset incl. refraction

    // Returns minutes after local midnight, or null if the sun
    // does not rise/set that day (polar day / night).
    function calc(dayOfYear, lat, lon, tzHours, rising) {
        var lngHour = lon / 15.0;
        var t = dayOfYear + (((rising ? 6.0 : 18.0) - lngHour) / 24.0);

        var m = (0.9856 * t) - 3.289;
        var l = norm360(m + (1.916 * sinD(m)) + (0.020 * sinD(2.0 * m)) + 282.634);

        var ra = norm360(Math.toDegrees(Math.atan(0.91764 * Math.tan(Math.toRadians(l)))));
        var lQuad = Math.floor(l / 90.0) * 90.0;
        var raQuad = Math.floor(ra / 90.0) * 90.0;
        ra = (ra + (lQuad - raQuad)) / 15.0;

        var sinDec = 0.39782 * sinD(l);
        var cosDec = Math.cos(Math.asin(sinDec));
        var cosH = (cosD(ZENITH) - (sinDec * sinD(lat))) / (cosDec * cosD(lat));
        if (cosH > 1.0 || cosH < -1.0) {
            return null;
        }

        var h = Math.toDegrees(Math.acos(cosH));
        if (rising) {
            h = 360.0 - h;
        }
        h = h / 15.0;

        var localT = h + ra - (0.06571 * t) - 6.622;
        var ut = norm24(localT - lngHour);
        var local = norm24(ut + tzHours);
        return (local * 60.0 + 0.5).toNumber() % 1440;
    }

    function dayOfYear(year, month, day) {
        var cum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        var n = cum[month - 1] + day;
        var leap = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
        if (leap && month > 2) {
            n += 1;
        }
        return n;
    }

    function sinD(deg) { return Math.sin(Math.toRadians(deg)); }
    function cosD(deg) { return Math.cos(Math.toRadians(deg)); }

    function norm360(v) {
        while (v < 0) { v += 360.0; }
        while (v >= 360.0) { v -= 360.0; }
        return v;
    }

    function norm24(v) {
        while (v < 0) { v += 24.0; }
        while (v >= 24.0) { v -= 24.0; }
        return v;
    }
}
