import Toybox.Lang;
import Toybox.System;

// What N3o "says" on the first line. Short on purpose:
// Latin/Cyrillic <= 14 chars, Japanese <= 9 chars (glyphs are 12px wide).
// Every character used here must exist in the bundled fonts
// (term_small: ASCII + Polish + Ukrainian; term_ja: subset built from JA below).
module Phrases {

    const EN = 0;
    const PL = 1;
    const UA = 2;
    const JA = 3;

    // situations
    const S_IDLE = 0;      // rotates hourly through IDLE lists
    const S_MORNING = 1;
    const S_RAIN = 2;
    const S_GOAL = 3;
    const S_NOTIFY = 4;    // "%d" is replaced by the count
    const S_LOW = 5;
    const S_NIGHT = 6;
    const S_RUN = 7;
    const S_HALLOWEEN = 8;
    const S_XMAS = 9;
    const S_NEWYEAR = 10;
    const S_VALENTINE = 11;
    const S_EASTER = 12;

    // [language][situation]; index 0 is unused (idle comes from IDLE)
    const TEXT = [
        ["", "good morning", "take umbrella", "goal smashed!", "%d new msg", "charge me pls", "sleep tight",
         "go go go!", "boo!", "merry xmas!", "happy new year", "love you <3", "happy easter"],
        ["", "dzień dobry", "weź parasol", "brawo! cel!", "%d wiad.", "naładuj mnie", "dobranoc",
         "dajesz!", "buu!", "wesołych świąt", "do siego roku", "kocham <3", "wesołego jajka"],
        ["", "доброго ранку", "бери парасолю", "ура! ціль!", "%d повід.", "заряди мене", "на добраніч",
         "вперед!", "бу!", "з різдвом!", "з новим роком!", "кохаю <3", "з великоднем!"],
        ["", "おはよう", "かさをもって", "やったね!", "つうち %d", "じゅうでんして", "おやすみ",
         "ファイト!", "ハッピーハロウィン", "メリクリ!", "あけおめ!", "だいすき", "イースター!"]
    ];

    const IDLE = [
        ["hi there", "hey!", "stay curious", "keep moving"],
        ["hejka!", "cześć!", "co tam?", "dawaj dalej"],
        ["привіт!", "хей!", "як справи?", "так тримати"],
        ["こんにちは", "やあ!", "がんばって", "いいね!"]
    ];

    // setting value: 0 = auto (watch language), 1 = EN, 2 = PL, 3 = UA, 4 = JA
    function resolveLanguage(setting) {
        if (setting == 1) { return EN; }
        if (setting == 2) { return PL; }
        if (setting == 3) { return UA; }
        if (setting == 4) { return JA; }
        var ds = System.getDeviceSettings();
        if (ds has :systemLanguage) {
            if (ds.systemLanguage == System.LANGUAGE_POL) { return PL; }
            if (ds.systemLanguage == System.LANGUAGE_JPN) { return JA; }
        }
        return EN; // Ukrainian is not a watch UI language on most devices: choose it manually
    }

    function get(lang, situation, hour, notifyCount) {
        if (lang < 0 || lang >= TEXT.size()) {
            lang = EN;
        }
        if (situation == S_IDLE) {
            var list = IDLE[lang];
            return list[hour % list.size()];
        }
        var s = TEXT[lang][situation];
        var i = s.find("%d");
        if (i != null) {
            s = s.substring(0, i) + notifyCount.toString() + s.substring(i + 2, s.length());
        }
        return s;
    }
}
