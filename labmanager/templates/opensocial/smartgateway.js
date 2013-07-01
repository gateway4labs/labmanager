function trace(msg) {
    if (console && console.log) 
        console.log(msg);
}

function SmartGateway(container, url) {

    var me = this;

    // Create a unique identifier
    this._identifier = Math.random();
    this._container = container;

    // By default, I'm not the master
    this._imMaster = false;

    this._LOADING_TIME     = 900; // ms
    this._inLoadingPeriod  = true;
    this._imMasterTemporal = false; // During the loading period, see if I'm gonna be one
    this._forceNotMaster   = false; // If after the loading time, somebody comes back, define "no, you're not the master"

    this._loadCallback = null;

    // Constructor
    this._init = function() {

        // When an inter-iframes message is received, call _processMessages
        window.addEventListener('message', me._processMessages, false);

        // On startup (in the constructor), report everyone in the space that I'm here.
        gadgets.openapp.publish({
            event: "select",
            type: "json",
            message: {
                'labmanager-msg' : 'labmanager::master-solver',
                'labmanager-id'     : me._identifier, 
            }
        });

        trace("Submitted " + me._identifier + "; now configuring timer: " + new Date().getTime());

        // Call onLoadingTimeElapsed on a given time.
        setTimeout(function(){ me._onLoadingTimeElapsed(); }, me._LOADING_TIME);

        // Receive messages by other widgets and call the method _onEvent
        gadgets.openapp.connect(me._onEvent);
    }

    // 
    // onEvent: catches OpenApp events and forwards them to the appropriate method
    // 
    this._onEvent = function(envelope, message) {
        if (message["labmanager-msg"].indexOf('labmanager::master-solver') == 0) {

            me._onMasterSolvingEvent(envelope, message);

        } else if (message["labmanager-msg"] == 'labmanager::activate') {

            me._onActivateEvent(envelope, message);

        }
        return true;
    }


    //////////////////////////////////////////////////////////////////////////////////////////////
    // 
    //    Master - slave  detection system
    // 
    // At this point, all the widgets send a message to the rest, reporting that they're there
    // 

    // onLoadTimeElapsed: after some time, check if I'm still the master or not.
    this._onLoadingTimeElapsed = function() {
        if ( !me._inLoadingPeriod )
            return;

        me._inLoadingPeriod = false;
        trace("Loading time elapsed: " + new Date().getTime() + "; force not master: " + me._forceNotMaster + "; imMasterTemporal: " + me._imMasterTemporal);

        if (me._forceNotMaster) {
            me._setUpSlave();
        } else {
            if(me._imMasterTemporal) {
                me._setUpMaster();
            } else {
                me._setUpSlave();
            }
        }
    }

    this._onMasterSolvingEvent = function(envelope, message) {

        // Solving who is the master: there are two periods: the first one, short (LOADING_TIME), on which all the widgets send a message.
        // The last message received by everybody will be the master. So everybody will think that they're the master until they receive
        // a message defining that they're not. If in LOADING_TIME no more systems define that they're the master, they everyone know that
        // they're the master. If later somebody comes in and says "hey, I'm the master", they will receive a message defining "no, you're 
        // not".

        if (message["labmanager-msg"] == 'labmanager::master-solver') {
            if (me._inLoadingPeriod) {
                trace("Still loading: I'm " + me._identifier + "; got: " + message['labmanager-id']);
                
                if( me._forceNotMaster )
                    return;

                if (message['labmanager-id'] == me._identifier) {
                    me._imMasterTemporal = true;
                } else {
                    me._imMasterTemporal = false;
                }
            } else {
                trace("Not loading anymore: force not master");

                gadgets.openapp.publish({
                    event: "select",
                    type: "json",
                    message: {
                        'labmanager-msg' : 'labmanager::master-solver::not-master',
                        'labmanager-id'     : me._identifier, 
                    }
                });
            }
        } else if (message["labmanager-msg"] == 'labmanager::master-solver::not-master') {
            trace("Got a force not master");
            me._forceNotMaster = true;
            me._onLoadingTimeElapsed();
        }
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
            if (!me._imMaster ) {
                if ( me._loadCallback != null )
                    me._loadCallback(message['labmanager-reservation-id'], message['labmanager-reservation-url']);
                else
                    alert("No callback defined!");
            }
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
            var url = data['url'];

            gadgets.openapp.publish({
                event: "select",
                type: "json",
                message: {
                    'labmanager-msg'             : 'labmanager::activate',
                    'labmanager-reservation-id'  : reservation_id,
                    'labmanager-reservation-url' : url,
                }
            });


            me._loadCallback(reservation_id, url);
        }
    }

    // 
    // Display a master widget
    // 
    this._setUpMaster = function() {
        me._imMaster = true;

        var buttonContainer = document.createElement("div");
        buttonContainer.style.textAlign = "center"; 
        buttonContainer.style.width = "100%"; 
        buttonContainer.style.marginTop = "5px";
        var button = document.createElement("button");
        button.className = "btn btn-success";
        button.appendChild(document.createTextNode("Start reservation process"));
        button.onclick = function() {
            var token = shindig.auth.getSecurityToken();
            var srcString = url + '?st=' + token;
            me._container.innerHTML = '<iframe id="weblabIFrame" onload="gadgets.window.adjustHeight();" frameborder="0" width="100%" height="100%" src="'+srcString+'"></iframe>';
        };
        button.onClick = button.onclick;

        buttonContainer.appendChild(button);
        me._container.appendChild(buttonContainer);
    }

    // 
    // Display a slave widget
    // 
    this._setUpSlave = function(){
        me._container.innerHTML = "<div style='width: 100%; margin-top: 5px; text-align: center' class='label label-info'>Waiting for the master widget...</span>";
    }

    // Whenever the widget (being a master or a slave) gets a reservation
    // finished, this method is called.
    this.registerOnLoad = function(onLoadCallback) {
        this._loadCallback = onLoadCallback;
    };

    this._init();
}
