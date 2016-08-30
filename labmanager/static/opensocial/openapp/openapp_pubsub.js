gadgets.openapp = function() {
	return {
		RDF: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
		connect: function(callback) {
			gadgets.pubsub.subscribe("openapp", function(sender, envelope) {
				envelope.sender = sender;
				if (callback(envelope, envelope.message) === true) {
					gadgets.pubsub.publish("openapp-recieve", true);
				}
			});
		},
		disconnect: function() {
			gadgets.pubsub.unsubscribe("openapp");
		},
		publish: function(envelope, message) {
			envelope.event = envelope.event || "select";
			envelope.sharing = envelope.sharing || "public";
			envelope.date = envelope.date || new Date();
			envelope.message = message || envelope.message;
			gadgets.pubsub.publish("openapp", envelope);
		}
	};
}();
