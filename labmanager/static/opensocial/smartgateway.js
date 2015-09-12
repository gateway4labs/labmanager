function trace(msg) {
    if (console && console.log) 
        console.log(msg);
}

function SmartGateway(container, button_div, reserve_button) {

    var me = this;

    var prefs = new gadgets.Prefs();
    this.localeString = "";
    if (prefs.getLang() != undefined && prefs.getLang() != null && prefs.getCountry() != undefined && prefs.getCountry() != null) {
        if (prefs.getLang().length > 0 && prefs.getCountry().length > 0) {
            this.localeString = "&locale=" + prefs.getLang() + "_" + prefs.getCountry();
        }
    }


    // Create a unique identifier
    this._identifier = Math.random();
    this._container = container;
    this._button_div = button_div;
    this._reserve_button = reserve_button;

    this._loadCallback = null;
    this._reservation_id = null;

    // Constructor
    this._init = function() {

        // When an inter-iframes message is received, call _processMessages
        window.addEventListener('message', me._processMessages, false);

        // Receive messages by other widgets and call the method _onEvent
        gadgets.openapp.connect(me._onEvent);

        me._buildUI();

        // If you move a widget, it automatically reloads its contents.
        // Therefore, we will ask the rest of the widgets in the space
        // whether there is an active reservation or not. If there is,
        // we will call the callback.
        gadgets.openapp.publish({
            event: "select",
            type: "json",
            message: {
                'srclabid'                   : LAB_ID,
                'labmanager-msg'             : 'labmanager::someone-there'
            }
        });

       


    }

    /////////////////////////////////////////////////////////////////////////
    // 
    //    UI - related methods
    // 

    this._buildUI = function() {

        me._container.html("");
        me._button_div.show();
        
        me._reserve_button.click(me.startReservation);

        gadgets.window.adjustHeight();

        // $(document).hover(me._onHover, me._noHover)
    }

    this._onWaitReservationEvent = function(envelope, message) {
        // Only one widget from the same labid performs each reservation, so the other widgets from the same labid should disable their reserve button.

        var messlabid = message["srclabid"];
 
        if ( (message['labmanager-src'] != me._identifier) && ( messlabid == LAB_ID ) )
        { 
            $('#reserve-button').attr('disabled', 'disabled');
        }
    }

    // 
    // onEvent: catches OpenApp events and forwards them to the appropriate method
    // 
    this._onEvent = function(envelope, message) {
        if (message["labmanager-msg"] == 'labmanager::activate') {

            me._onActivateEvent(envelope, message);

        } else if (message["labmanager-msg"] == 'labmanager::wait_reservation') {

            me._onWaitReservationEvent(envelope, message);

        } else if (message["labmanager-msg"] == 'labmanager::someone-there') {

            me._onSomeoneThere(envelope, message);

        } else if (message["labmanager-msg"] == 'labmanager::updateBgColor') {

            me._onUpdateBgColor(envelope, message);

        } else if (message["labmanager-msg"] == 'labmanager::reload') {

            location.reload();

        }
        return true;
    }

    this._onHover = function() {
        var color ="LightGray"
        document.body.style.backgroundColor=color; 

        // send data
        gadgets.openapp.publish({
            event: "select",
            type: "json",
            message: {
                'srclabid'           : LAB_ID,
                'labmanager-msg'    : 'labmanager::updateBgColor',
                'color'             : color,
            }
        });
    };

    this._noHover = function() {
        var color ="white"
        document.body.style.backgroundColor=color; 

        // send data
        gadgets.openapp.publish({
            event: "select",
            type: "json",
            message: {
                'srclabid'           : LAB_ID,
                'labmanager-msg'    : 'labmanager::updateBgColor',
                'color'             : color,
            }
        });
    };


    this._onUpdateBgColor = function(envelope, message) {
        var color = message["color"];

        var messlabid = message["srclabid"];
 
        if (messlabid == LAB_ID)
        {
            document.body.style.backgroundColor=color; 
        }
                 
        return true;
    }


    /////////////////////////////////////////////////////////////////////////////////////////
    // 
    //           Activation process
    // 
    // Whenever the reservation button is pressed, one of the widgets gets a reservation id,
    // and forwards it to the rest of the widgets. In that moment, the system will propagate
    // an 'activate' message to display the current widget.
    // 

    this._onActivateEvent = function(envelope, message) {

        var messlabid = message["srclabid"];

        if ( ( me._reservation_id == null ) && ( messlabid  == LAB_ID ) ) {
            me._reservation_id = message['labmanager-reservation-id'];
            me._loadCallback(me._reservation_id);
        }
    }


    this._onSomeoneThere = function(envelope, message) {
            
        var messlabid = message["srclabid"];
 
        if ( ( me._reservation_id != null ) && ( messlabid  == LAB_ID ) )
        {
            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'srclabid'                   : LAB_ID,
                    'labmanager-msg'             : 'labmanager::activate',
                    'labmanager-reservation-id'  : me._reservation_id,
                }
            });
        }
    }

    // 
    // This message takes a message from the iframe through the inter-frame communication
    // and uses OpenApp to send a message to the rest of the widgets.
    this._processMessages = function(e) {
        if((e.origin == CURRENT_HOST_HTTP || e.origin == CURRENT_HOST_HTTPS) && new String(e.data).indexOf("reserved::") == 0) {
            var data_str = e.data.split('::')[1];
            trace('Do something with: ' + data_str);

            var data = JSON.parse(data_str);
            var reservation_id = data['reservation-id'];

            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'srclabid'                   : LAB_ID,
                    'labmanager-msg'             : 'labmanager::activate',
                    'labmanager-reservation-id'  : reservation_id,
                }
            });
                
            me._reservation_id = reservation_id;
            me._loadCallback(reservation_id);
        } else if((e.origin == CURRENT_HOST_HTTP || e.origin == CURRENT_HOST_HTTPS) && new String(e.data).indexOf("reload::") == 0) {
            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'srclabid'                   : LAB_ID,
                    'labmanager-msg'             : 'labmanager::reload',
                }
            });
            location.reload();
        }
    }

    this.startReservation = function() {
        // This method is called when the user clicks on the button.
        // Don't do anything if the button was disabled.
        if ($('#reserve-button').attr('disabled') != 'disabled') {

            // First, report the rest of the widgets: "I'm doing a reservation"
            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'srclabid'                   : LAB_ID,
                    'labmanager-msg'             : 'labmanager::wait_reservation',
                    'labmanager-src'             : me._identifier
                }
            });

            // Then, take the token
            var token = shindig.auth.getSecurityToken();
            var url = getReservationUrl(token, this.localeString);

            trace("Loading... " + url);

            // and perform the reservation itself
            me._button_div.hide();
            me._container.html("<iframe src='" + url + "' width='100%' onload='gadgets.window.adjustHeight();'></iframe>");
        }
    }

    // Whenever the widget gets a reservation
    // this method is called.
    this.registerOnLoad = function(onLoadCallback) {
        this._loadCallback = onLoadCallback;
    };

    this._init();
}
