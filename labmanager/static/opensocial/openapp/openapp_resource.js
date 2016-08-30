hmm

var linkexp=/<[^>]*>\s*(\s*;\s*[^\(\)<>@,;:"\/\[\]\?={} \t]+=(([^\(\)<>@,;:"\/\[\]\?={} \t]+)|("[^"]*")))*(,|\$)/g;
var paramexp=/[^\(\)<>@,;:"\/\[\]\?={} \t]+=(([^\(\)<>@,;:"\/\[\]\?={} \t]+)|("[^"]*"))/g;

function unquote(value)
{
    if (value.charAt(0) == '"' && value.charAt(value.length - 1) == '"') return value.substring(1, value.length - 1);
    return value;
}

function parseLinkHeader(value)
{
   var matches = value.match(linkexp);
   var rels = new Object();
   var titles = new Object();
   for (i = 0; i < matches.length; i++)
   {
      var split = matches[i].split('>');
      var href = split[0].substring(1);
      var ps = split[1];
      var link = new Object();
      link.href = href;
      var s = ps.match(paramexp);
      for (j = 0; j < s.length; j++)
      {
         var p = s[j];
         var paramsplit = p.split('=');
         var name = paramsplit[0];
         link[name] = unquote(paramsplit[1]);
      }

      if (link.rel != undefined)
      {
         rels[link.rel] = link;
      }
      if (link.title != undefined)
      {
         titles[link.title] = link;
      }
   }
   var linkheader = new Object();
   linkheader.rels = rels;
   linkheader.titles = titles;
   return linkheader;
}

var openapp = openapp || {};
openapp.ns = openapp.ns || {};
openapp.ns.rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
openapp.ns.rdfs = "http://www.w3.org/2000/01/rdf-schema#";
openapp.ns.dcterms = "http://purl.org/dc/terms/";
openapp.ns.foaf = "http://xmlns.com/foaf/0.1/";
openapp.ns.rest = "http://kmr.csc.kth.se/rdf/rest/";
openapp.ns.role = "http://www.role-project.eu/rdf/";

var openapp = openapp || {};
openapp.rest = openapp.rest || {};

/**
 * Creates an XMLHttpRequest object, in a manner compatible with the
 * current browser environment.
 *  
 * @private
 * @returns {XMLHttpRequest} The created XMLHttpRequest object.
 * @throws {Object} If XMLHttpRequest is not supported in this environment.
 */
openapp.rest.createXMLHttpRequest = function () {
	/*global XMLHttpRequest, ActiveXObject */
	if (typeof XMLHttpRequest !== 'undefined') {
		return new XMLHttpRequest();
	} else if (typeof ActiveXObject !== 'undefined') {
		return new ActiveXObject('Microsoft.XMLHTTP');
	} else {
		throw {
			name: 'XMLHttpRequestError',
			message: 'XMLHttpRequest not supported'
		};
	}
};

/**
 * Makes an asynchronous request over HTTP using XMLHttpRequest.
 * 
 * <p>It only supports application/json in both the request and response
 * bodies.</p>
 * 
 * @private
 * @param {String} method The HTTP method to use, e.g., 'GET'.
 * @param {String} uri The URI from which host and path is to be extracted.
 * @param {String} data The body to send with the request; an empty string,
 *   null or undefined for none.
 * @param {Function} callback A function to be called when the request has
 *   been completed.
 */
openapp.rest.makeRequest = function (method, uri, callback, link, data, mediaType) {
	// Requires the createXMLHttpRequest function
	params = params || {};
	var request = openapp.rest.createXMLHttpRequest();
	request.open(method, uri, true);
	request.setRequestHeader('Accept', 'application/json');
	data = data || "";
	if (data.length > 0 || method === 'POST' || method === 'PUT') {
		request.setRequestHeader('Content-Type', mediaType !==
		  'undefined' ? mediaType : 'application/json');
		request.setRequestHeader('Content-Length', data.length);
	}
	request.onreadystatechange = function () {
		if (request.readyState === 4) {
			var context = {
				data: JSON.parse(request.responseText),
				link: typeof response.headers.link !== "undefined" ? parseLinkHeader(response.headers.link[0]).rels : {}
			};
			if (response.headers.hasOwnProperty("location")) {
				context.uri = response.headers["location"][0];
			} else if (response.headers.hasOwnProperty("content-base")) {
				context.uri = response.headers["content-base"][0];
			} else if (context.link.hasOwnProperty("http://purl.org/dc/terms/subject")) {
				context.uri = context.link["http://purl.org/dc/terms/subject"].href;
			}
			if (response.headers.hasOwnProperty("content-location")) {
				context.contentUri = response.headers["content-location"][0];
			}
			if (response.headers.hasOwnProperty("content-type")
			  && response.headers["content-type"][0].split(";")[0] == "application/json") {
				context.data = gadgets.json.parse(context.data);
			}
			if (typeof response.data !== "undefined") {
				if (context.data.hasOwnProperty("")) {
					context.subject = context.data[""];
				} else {
					context.subject = context.data[context.uri];
				}
			}
			callback(context);
		}
	};
	request.send(data);
};

// If the gadgets.* API is available (OpenSocial), use it rather than
//  XMLHttpRequest
if (typeof gadgets !== 'undefined' && typeof gadgets.io !== 'undefined' &&
		typeof gadgets.io.makeRequest !== 'undefined') {
	var params = {};
	var linkHeader = "";
	if (typeof link !== "undefined") {
		for (rel in link) { if (link.hasOwnProperty(rel)) {
			if (linkHeader.length > 0) {
				linkHeader += ", ";
			}
			linkHeader += "<" + link[rel] + ">; rel=\"" + rel + "\"";
		}}
	}
	params[gadgets.io.RequestParameters.GET_FULL_HEADERS] = true;
	params[gadgets.io.RequestParameters.CONTENT_TYPE] = gadgets.io.ContentType.TEXT;
	params[gadgets.io.RequestParameters.AUTHORIZATION] = gadgets.io.AuthorizationType.OAUTH;
	params[gadgets.io.RequestParameters.OAUTH_SERVICE_NAME] = "space";
	params[gadgets.io.RequestParameters.OAUTH_USE_TOKEN] = "always";
	params[gadgets.io.RequestParameters.METHOD] = method;
	if (typeof data !== "undefined" && data !== null) {
		params[gadgets.io.RequestParameters.HEADERS] = params[gadgets.io.RequestParameters.HEADERS] || {};
		params[gadgets.io.RequestParameters.HEADERS]["content-type"] =
		  typeof mediaType !== "undefined" ? mediaType : "application/json";
		params[gadgets.io.RequestParameters.POST_DATA] = data;
	}
	if (linkHeader.length > 0) {
		params[gadgets.io.RequestParameters.HEADERS] = params[gadgets.io.RequestParameters.HEADERS] || {};
		params[gadgets.io.RequestParameters.HEADERS]["link"] = linkHeader;
	}
	gadgets.io.makeRequest(uri, function (response) {
		\$("#personalizeHideButton").click(function(){
			\$("#personalizeComplete").css("display", "none");
		});
		if (response.oauthApprovalUrl) {
			var popup = shindig.oauth.popup({
				destination: response.oauthApprovalUrl,
				windowOptions: "width=450,height=500",
				onOpen: function() { 
					\$("#personalize").css("display", "none");
					\$("#personalizeDone").css("display", "block");
				},
				onClose: function() {
					\$("#personalizeDone").css("display", "none");
					\$("#personalizeComplete").css("display", "block");
					init();
				}
			});
			\$("#personalizeButton").click(popup.createOpenerOnClick());
			\$("#personalizeDoneButton").click(popup.createApprovedOnClick());
			\$("#personalizeDenyButton").click(function(){
				\$("#personalize").css("display", "none");
			});
			\$("#personalize").css("display", "block");
		} else if (response.oauthError) {
			\$("#personalizeMessage").text(
			  "The authorization was not completed successfully. (" + response.oauthError + ")");
			\$("#personalizeComplete").css("display", "block");
		} else {
			\$("#personalizeMessage").text(
			  "You have now granted authorization. To revoke authorization, go to your Privacy settings.");
			var context = {
				data: response.data,
				link: typeof response.headers.link !== "undefined" ? parseLinkHeader(response.headers.link[0]).rels : {}
			};
			if (response.headers.hasOwnProperty("location")) {
				context.uri = response.headers["location"][0];
			} else if (response.headers.hasOwnProperty("content-base")) {
				context.uri = response.headers["content-base"][0];
			} else if (context.link.hasOwnProperty("http://purl.org/dc/terms/subject")) {
				context.uri = context.link["http://purl.org/dc/terms/subject"].href;
			}
			if (response.headers.hasOwnProperty("content-location")) {
				context.contentUri = response.headers["content-location"][0];
			}
			if (response.headers.hasOwnProperty("content-type")
			  && response.headers["content-type"][0].split(";")[0] == "application/json") {
				context.data = gadgets.json.parse(context.data);
			}
			if (typeof response.data !== "undefined") {
				if (context.data.hasOwnProperty("")) {
					context.subject = context.data[""];
				} else {
					context.subject = context.data[context.uri];
				}
			}
			callback(context);
		}
	}, params);
}

var openapp = openapp || {};
openapp.resource = openapp.resource || {};

openapp.resource.get = function(uri, callback, link) {
	return openapp.rest.makeRequest("GET", uri, callback,
		link || { "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate": openapp.ns.rest + "info" });
};

openapp.resource.post = function(uri, callback, link, data, mediaType) {
	return openapp.rest.makeRequest("POST", uri, callback, link, data, mediaType);
};

openapp.resource.put = function(uri, callback, link, data, mediaType) {
	return openapp.rest.makeRequest("PUT", uri, callback, link, data, mediaType);
};

openapp.resource.del = function(uri, callback, link) {
	return openapp.rest.makeRequest("DELETE", uri, callback, link);
};

openapp.resource.in = function(context) {
	return {
		sub: function(relation) {
			var link = {};
			return {
				control: function(key, value) {
					link[key] = value;
					return this;
				},
				type: function(value) {
					return this.control(openapp.ns.rdf + "type", value);
				},
				seeAlso: function(value) {
					return this.control(openapp.ns.rdfs + "seeAlso", value);
				},
				list: function() {
					var result = [];
					var subs = context.subject[relation], sub, subject;
					if (typeof subs === "undefined") {
						return result;
					}
					subfor: for (var i = 0; i < subs.length; i++) {
						sub = subs[i];
						subject = context.data[sub.value]
						for (key in link) { if (link.hasOwnProperty(key)) {
							if (!subject.hasOwnProperty(key) || subject[key][0].value !== link[key]) {
								continue subfor;
							}
						}}
						result.push({
							data: context.data,
							link: {},
							uri: sub.value,
							subject: subject
						});
					}
					return result;
				},
				create: function(callback) {
					if (!context.link.hasOwnProperty(relation)) {
						throw "The context does not support the requested relation";
					}
					var postUri = context.link[relation].href;
					openapp.resource.post(postUri, function(context){
						callback(context);
					}, link);
				}
			};
		},
		metadata: function() {
			return openapp.resource.in(context).as(openapp.ns.rest + "metadata");
		},
		representation: function() {
			return openapp.resource.in(context).as(openapp.ns.rest + "representation");
		},
		as: function(topic) {
			return {
				get: function(callback) {
					openapp.resource.get(context.uri, function(content){
						callback(content);
					}, { "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate": topic });
				},
				mediaType: function(mediaType) {
					var type = mediaType;
					var data = null;
					return {
						string: function(string) {
							data = string;
							return this;
						},
						json: function(json) {
							data = gadgets.json.stringify(json);
							return this;
						},
						put: function(callback) {
							openapp.resource.put(context.uri, function(content){
								callback(content);
							}, { "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate": topic }, data, type);							
						}
					};
				},
				string: function(string) {
					return this.mediaType("text/plain").string(string);
				},
				json: function(json) {
					return this.mediaType("application/json").json(json);
				},
				graph: function() {
					var graph = {}
					var subj = "";
					return {
						subject: function(subject) {
							subj = subject;
							return this;
						},
						resource: function(predicate, object) {
							graph[subj] = graph[subj] || {};
							graph[subj][predicate] = graph[subj][predicate] || [];
							graph[subj][predicate].push({ value: object, type: "uri" });
							return this;
						},
						literal: function(predicate, literal, lang, datatype) {
							graph[subj] = graph[subj] || {};
							graph[subj][predicate] = graph[subj][predicate] || [];
							graph[subj][predicate].push({ value: literal, type: "literal", lang: lang, datatype: datatype });
							return this;
						},
						put: function(callback) {
							openapp.resource.put(context.uri, function(content){
								callback(content);
							}, { "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate": topic }, gadgets.json.stringify(graph));
						}
					};
				}
			};
		},
		properties: function() {
			var result = {};
			for (pred in context.subject) { if (context.subject.hasOwnProperty(pred)) {
				result[pred] = context.subject[pred][0].value;
			}}
			return result;
		},
		string: function() {
			if (typeof context.data === "string") {
				return context.data;
			} else {
				return gadgets.json.stringify(context.data);
			}
		},
		json: function() {
			if (typeof context.data === "string") {
				return null;
			} else {
				return context.data;
			}
		},
		followSeeAlso: function() {
			var seeAlso = context.subject[openapp.ns.rdfs + "seeAlso"];
			if (typeof seeAlso !== "undefined") {
				seeAlso = seeAlso[0].value;
				
				// Ugly reasoning about whether to follow the reference
				var slashes = 0;
				for (var i = 0; i < seeAlso.length && i < context.uri.length && seeAlso.charAt(i) === context.uri.charAt(i); i++) {
					if (seeAlso.charAt(i) === "/") {
						slashes++;
					}
				}
				var totalSlashes = slashes;
				for (; i < seeAlso.length; i++) {
					if (seeAlso.charAt(i) === "/") {
						totalSlashes++;
					}
				}
				if (slashes < 3 || totalSlashes > 4) {
					return this;
				}

				return openapp.resource.in({
					data: context.data,
					link: {},
					uri: seeAlso,
					subject: context.data[seeAlso]
				});
			} else {
				return this;
			}
		}
	};
};
