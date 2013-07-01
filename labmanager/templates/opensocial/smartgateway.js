function trace(msg) {
    if (console && console.log) 
        console.log(msg);
}

function SmartGateway(container) {

    var me = this;

    // Create a unique identifier
    this._identifier = Math.random();
    this._container = container;

    this._loadCallback = null;

    // Constructor
    this._init = function() {

        // When an inter-iframes message is received, call _processMessages
        window.addEventListener('message', me._processMessages, false);

        trace("Submitted " + me._identifier + "; now configuring timer: " + new Date().getTime());

        // Receive messages by other widgets and call the method _onEvent
        gadgets.openapp.connect(me._onEvent);

        me._buildUI();
    }

    /////////////////////////////////////////////////////////////////////////
    // 
    //    UI - related methods
    // 

    this._buildUI = function() {

        me._container.html("");

        var $button = $("<button id='reserve-button' class='btn btn-success'>Reserve</button>");
        $button.click( me.startReservation );
        var $div = $("<div></div>");
        $div.css({
            'text-align' : 'center',
            'width'      : '100%',
            'margin-top' : '5px'
        });
        $div.append($button);

        me._container.append($div);
    }

    this._onWaitReservationEvent = function() {
        $('#reserve-button').attr('disabled', 'disabled');
    }

    // 
    // onEvent: catches OpenApp events and forwards them to the appropriate method
    // 
    this._onEvent = function(envelope, message) {
        if (message["labmanager-msg"] == 'labmanager::activate') {

            me._onActivateEvent(envelope, message);

        } else if(message["labmanager-msg"] == 'labmanager::wait_reservation') {

            me._onWaitReservationEvent(envelope, message);

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
        if (message["labmanager-msg"] == 'labmanager::activate') {
            me._loadCallback(message['labmanager-reservation-id']);
        }
    }

    // 
    // This message takes a message from the iframe through the inter-frame communication
    // and uses OpenApp to send a message to the rest of the widgets.
    this._processMessages = function(e) {
        if((e.origin == 'http://{{ request.host }}' || e.origin == 'https://{{ request.host }}') && new String(e.data).indexOf("reserved::") == 0) {
            var data_str = e.data.split('::')[1];
            trace('Do something with: ' + data_str);

            var data = JSON.parse(data_str);
            var reservation_id = data['reservation-id'];

            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'labmanager-msg'             : 'labmanager::activate',
                    'labmanager-reservation-id'  : reservation_id,
                }
            });

            me._loadCallback(reservation_id);
        }
    }

    this.startReservation() {
        // This method is called when the user clicks on the button.
        // Don't do anything if the button was disabled.
        if ($('#reserve-button').attr('disabled') != 'disabled') {

            // First, report the rest of the widgets: "I'm doing a reservation"
            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'labmanager-msg'             : 'labmanager::wait_reservation'
                }
            });

            // Then, take the token
            var token = shindig.auth.getSecurityToken();
            var url = '{{ url_for(".reserve", institution_id = institution_id, lab_name = lab_name) }}?st=' + token;

            // and perform the reservation itself
            $("container").html("<iframe src='" + url + "' width='100%' height='100%'></iframe>");
        }
    }

    // Whenever the widget gets a reservation
    // this method is called.
    this.registerOnLoad = function(onLoadCallback) {
        this._loadCallback = onLoadCallback;
    };

    this._init();
}
