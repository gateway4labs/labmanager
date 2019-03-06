// TODO: FALTA TODO EL TEMA DE QUE CUANDO SE ENVIA ALGO DESDE ABAJO LLEGUE AQUI. BASICAMENTE LO QUE HACEMOS ES ESO, EN LUGAR DE UNA QUERY, CARGAMOS UN API QUE HACE LA MAGIA

function getLanguage() {
    var language = "";
    var country = "";

    if (window.location.hash) {
        language = getParameterByName("lang") || "";
        country = getParameterByName("country") || "";
    }

    if (language) {
        if (language.split('_').length > 1)
            return language;

        if (country)
            return language + "_" + country;
        
        // No _ and no country
        return language + "_ALL";
    }

    return "en_ALL";
}

function SmartGateway(container, button_div, reserve_button) {

    var me = this;

    this.localeString = getLanguage();

    // Create a unique identifier
    this._identifier = Math.random();
    this._container = container;
    this._button_div = button_div;
    this._reserve_button = reserve_button;

    this._loadCallback = null;
    this._reservation_id = null;
    this._g4l_session_id = null;

    // Constructor
    this._init = function() {
        me._container.html("");
        me._button_div.show();
        
        me._reserve_button.click(me.startReservation);

        adjustIframeHeight();
    }

    /////////////////////////////////////////////////////////////////////////////////////////
    // 
    //           Activation process
    // 
    // Whenever the reservation button is pressed, one of the widgets gets a reservation id,
    // and forwards it to the rest of the widgets. In that moment, the system will propagate
    // an 'activate' message to display the current widget.
    // 

    this.startReservation = function() {
        // This method is called when the user clicks on the button.
        // Don't do anything if the button was disabled.
        if ($('#reserve-button').attr('disabled') != 'disabled') {
            var url = getReservationUrl(this.localeString);

            console.log("Loading2... " + url);
            $.post(url).done(function (data) {
                if (data.success) {
                    me._loadCallback(data.reservation_id, data.g4l_session_id);
                } else {
                    // ERROR TODO
                }
            }).fail(function (data) {
                // ERROR TODO
            });
            
            console.log('HIDING');
            console.log(me._button_div)
            me._button_div.hide();
        }
    }

    // Whenever the widget gets a reservation
    // this method is called.
    this.registerOnLoad = function(onLoadCallback) {
        this._loadCallback = onLoadCallback;
    };

    this._init();
}
