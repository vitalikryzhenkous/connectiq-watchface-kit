import Toybox.Application;
import Toybox.WatchUi;

class N3onApp extends Application.AppBase {

    private var _view = null;

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() {
        _view = new N3onView();
        return [ _view ];
    }

    // Called when the user changes settings in Garmin Connect / Connect IQ app
    function onSettingsChanged() {
        if (_view != null) {
            _view.loadSettings();
        }
        WatchUi.requestUpdate();
    }
}
