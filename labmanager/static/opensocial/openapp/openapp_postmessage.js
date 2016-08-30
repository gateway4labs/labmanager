/*jslint laxbreak: true */
/*global window: true, opensocial: true, gadgets: true*/

/**
 * Open Application Event API.
 * 
 * Choice of communication channel:
 * 1. If requirements for postMessage are met, use postMessage.
 * 2. If requirements for pubsub are met, use pubsub.
 * 3. No channel; communication is disabled (and thus the Open Application events are disabled).
 */
gadgets.openapp = function() {

	/**
	 * Whether or not postMessage is the communication channel that is to be used.
	 *
	 * Openapp events when using postMessage:
	 * 1. When the script is loaded, notify the parent (i.e., the container) that "I exist and
	 *  want to use openapp event communication via postMessage".
	 * 2. When an event is published, broadcast the event to (1) the parent (container) and
	 *  (2) the parent's frames (all gadgets).
	 * 3. If a special event is received from the parent as a reply to 1. above, that says it
	 *  wants to handle broadcast of events to other frames, then in 2., skip (2).
	 * 4. When an event is received, then if the event is accepted (i.e., the callback returns
	 *  true), send a special event to the parent to notify it of the receipt.
	 */
	var usePostMessage = typeof window !== "undefined" && typeof window.parent !== "undefined"
	  && typeof window.postMessage !== "undefined" && typeof JSON !== "undefined"
	  && typeof JSON.parse !== "undefined" && typeof JSON.stringify !== "undefined";

	/**
	 * Whether or not gadgets.pubsub is the communication channel that is to be used.
	 */
	var usePubSub = !usePostMessage && typeof gadgets !== "undefined" && typeof gadgets.pubsub
	  !== "undefined" && typeof gadgets.pubsub.subscribe !== "undefined" &&
	  typeof gadgets.pubsub.unsubscribe !== "undefined" && typeof gadgets.pubsub.publish
	  !== "undefined";

	/**
	 * Initialization data received from the parent, with default values.
	 */
	var init = {
		/**
		 * Whether events should only be sent to the parent or be broadcasted to both the
		 *  parent and all the parent's frames.
		 */
		postParentOnly: false
	};

	/**
	 * Initialization data to be used when the parent does not take responsiblity for
	 *  message propagation (the data will be set at the first call to "publish").
	 */
	var ownData = null;

	/**
	 * The callback function specified by a call to connect is kept here.
	 */
	var doCallback = null;

	/**
	 * The internal callback function that in turn calls doCallback is kept here.
	 */
	var onMessage = null;
	if (usePostMessage) {

		onMessage = function(event) {
			if (typeof event.data === "string" && event.data.slice(0, 25)
			  === "{\"OpenApplicationEvent\":{") {
				var envelope = JSON.parse(event.data).OpenApplicationEvent;
				if (envelope.event === "openapp" && envelope.welcome === true
				  && event.source === window.parent) {
					for (var p in envelope.message) {
						if (envelope.message.hasOwnProperty(p)) {
							init[p] = envelope.message[p];
						}
					}
				} else {
					envelope.source = event.source;
					envelope.origin = event.origin;
					envelope.toJSON = function() {
						var json = {};
						for (var e in this) {
							if (this.hasOwnProperty(e)
							  && typeof this[e] !== "function"
							  && e !== "source" && e !== "origin") {
								json[e] = this[e];
							}
						}
						return json;
					};
					if (typeof doCallback === "function") {
						if (doCallback(envelope, envelope.message)
						  === true) {
							window.parent.postMessage(JSON.stringify(
							  { OpenApplicationEvent: { event:
							  "openapp", receipt: true } }), "*");
						}
					}
				}
			}
		};
		if (typeof window.attachEvent !== "undefined") {
			window.attachEvent("onmessage", onMessage);
		} else {
			window.addEventListener("message", onMessage, false);
		}
		if (typeof window.parent !== "undefined") {
			window.parent.postMessage(JSON.stringify({ OpenApplicationEvent:
			  { event: "openapp", hello: true } }), "*");
		}

	} else if (usePubSub) {

		onMessage = function(sender, envelope) {
			envelope.source = undefined;
			envelope.origin = undefined;
			envelope.sender = sender;
			if (typeof doCallback === "function") {
				if (doCallback(envelope, envelope.message) === true) {
					gadgets.pubsub.publish("openapp-recieve", true);  // [sic]
				}
			}
		};

	}
	
	return {

		/**
		 * The RDF namespace (specified here as it is commonly used).
		 */
		RDF: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",

		/**
		 * Sets the function to be called when an event has occurred. The callback function
		 *  will be called as: callback(envelope, message)
		 */
		connect: function(callback) {
			doCallback = callback;
			if (usePubSub) {

				gadgets.pubsub.subscribe("openapp", onMessage);

			}
		},

		/**
		 * Stops calls from being made to the callback function set using connect(callback).
		 */
		disconnect: function() {
			if (usePubSub) {

				gadgets.pubsub.unsubscribe("openapp");

			}
			doCallback = null;
		},

		/**
		 * Publishes an event. The message may be given either as envelope.message or as
		 *  the second argument.
		 */
		publish: function(envelope, message) {
			envelope.event = envelope.event || "select";
			envelope.sharing = envelope.sharing || "public";
			envelope.date = envelope.date || new Date();
			envelope.message = message || envelope.message;
			if (usePostMessage) {

				if (init.postParentOnly === false && ownData === null) {
					ownData = {
						sender: "unknown",
						viewer: "unknown"
					};
					if (typeof window.location !== "undefined" &&
					  typeof window.location.search === "string" &&
					  typeof window.unescape === "function") {
						var pairs = window.location.search.substring(1)
						  .split("&"), pair, query = {};
						if (!(pairs.length == 1 && pairs[0] === "")) {
							for (var p = 0; p < pairs.length; p++) {
								pair = pairs[p].split("=");
								if (pair.length == 2) {
									query[pair[0]] =
									  window.unescape(pair[1]);
								}
							}
						}
						if (typeof query.url === "string") {
							ownData.sender = query.url;
						}
					}
					if (typeof opensocial !== "undefined" && typeof
					  opensocial.newDataRequest === "function") {
						var req = opensocial.newDataRequest();
						req.add(req.newFetchPersonRequest(
						  opensocial.IdSpec.PersonId.VIEWER), "viewer");
						var that = this;
						req.send(function(resp) {
							var person = resp.get("viewer").getData();
							if (typeof person === "object" &&
							  person !== null && typeof
							  person.getId === "function") {
								var viewer = person.getId();
								if (typeof viewer === "string") {
									ownData.viewer = viewer;
								}
							}
							that.publish(envelope, message);
						});
						return;
					}
				}

				if (ownData !== null) {
					if (typeof ownData.sender === "string") {
						envelope.sender = ownData.sender;
					}
					if (typeof ownData.viewer === "string") {
						envelope.viewer = ownData.viewer;
					}
				}

				var data = JSON.stringify({ OpenApplicationEvent: envelope });
				if (window.parent !== "undefined") {
					window.parent.postMessage(data, "*");
					if (!init.postParentOnly) {
						var frames = window.parent.frames;
						for (var i = 0; i < frames.length; i++) {
							frames[i].postMessage(data, "*");
						}
					}
				} else {
					window.postMessage(data, "*");
				}

			} else if (usePubSub) {

				gadgets.pubsub.publish("openapp", envelope);

			}
		}

	};
}();
