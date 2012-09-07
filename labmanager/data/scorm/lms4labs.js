function getXmlHttpObject() {
    var xmlhttp = false;
    /*@cc_on
    @if (@_jscript_version >= 5)
    try{
        xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
    }catch(e){
        try{
            xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
        }catch(E){
            xmlhttp = false;
        }
    }
    @else
        xmlhttp = false;
    @end @*/
	if(!xmlhttp && typeof XMLHttpRequest != 'undefined'){
		try{
			xmlhttp = new XMLHttpRequest();
		}catch(e){
			xmlhttp = false;
		}
	}
	return xmlhttp;
}

var DEFAULT_ROOT_ELEMENT = 'lms4labs_root';
var lms4labs_paths = {
    'requests'     : 'lms4labs/lms/forward',
    'authenticate' : 'lms4labs/lms/authenticate'
};

var lms4labs_templates = {
    'reserve-success' : "<div align=\"center\" class=\"well alert alert-success\"><h2>Experiment reserved</h2> <br/> <a class=\"btn\" href=\"%(URL)s\" target=\"_blank\">Run experiment</a></div>",
    'authenticate-success' : "<div align=\"center\" class=\"well alert alert-success\"><h2>Authenticated</h2> <br/> <a class=\"btn\" href=\"%(URL)s\" target=\"_blank\">Open LMS Manager</a></div>",
    'error'   : "<div align=\"center\" class=\"well alert\"><h2>Error</h2><br/><p>%(TEXT)s</p></div>",
    'unknown-error' : "<div align=\"center\" class=\"well alert alert-error\"><h2>Unknown error</h2> <br/> The following code was returned: %(TEXT)s</div>"
};

function Laboratory(baseurl, extension, elementName) {

    if(baseurl == undefined)
        this.baseurl = "/";
    else
        this.baseurl = baseurl;

    if(extension == undefined)
        this.extension = "/";
    else
        this.extension = extension;

    if (elementName == undefined)
        this.elementName = DEFAULT_ROOT_ELEMENT;
    else
        this.elementName = elementName;

    var root = document.getElementById(this.elementName);
    if(root == null) {
        alert("lms4labs.js misconfigured. Either create a " + DEFAULT_ROOT_ELEMENT + " value or pass an argument");
        return;
    }

    this.handleError = function(xmlhttp, response, url) {
        if (xmlhttp.status == 404) {
            if(onerror == undefined) {
                return lms4labs_templates['error'].replace('%(TEXT)s', "Page <a href=\"" + url + "\">" + url + "</a> does not exist");
            } else {
                onerror(xmlhttp.responseText, root);
                return null;
            }
        } else if (response.indexOf('error:') == 0) {
            if(onerror == undefined) {
                var errorMessage = response.substring('error:'.length);
                return lms4labs_templates['error'].replace('%(TEXT)s', errorMessage);
            } else {
                onerror(xmlhttp.responseText, root);
                return null;
            }
        } else {
            if(onerror == undefined) {
                var errorMessage = xmlhttp.responseText;
                return lms4labs_templates['unknown-error'].replace('%(TEXT)s', errorMessage);
            } else {
                onerror(xmlhttp.responseText, root);
                return null;
            }
        }
    }

    this.load = function(laboratoryId, onerror) {

        var xmlhttp     = getXmlHttpObject();
        var lab = this;

        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4) {
                var response = xmlhttp.responseText;

                var htmlCode = null;
                if (response.indexOf('http') == 0) {
                    htmlCode = lms4labs_templates['reserve-success'].replace('%(URL)s', response);
                } else {
                    htmlCode = lab.handleError(xmlhttp, response, url);
                }
                if(htmlCode != null)
                    root.innerHTML = htmlCode;
            }
        };

        var requestPayload = "{ \"action\" : \"reserve\", \"experiment\" : \"" + laboratoryId.replace(/\"/g, '\\"') + "\" }";

        var url = this.baseurl + lms4labs_paths['requests'] + this.extension;

        xmlhttp.open("POST", url, true);
        xmlhttp.setRequestHeader('Content-Type', 'application/json');
        xmlhttp.send(requestPayload);
    };

    this.authenticate = function(onerror) {

        var xmlhttp     = getXmlHttpObject();
        var lab = this;
        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4) {
                var response = xmlhttp.responseText;

                var htmlCode = null;
                if (response.indexOf('http') == 0) {
                    htmlCode = lms4labs_templates['authenticate-success'].replace('%(URL)s', response);
                } else {
                    htmlCode = lab.handleError(xmlhttp, response, url);
                }
                if(htmlCode != null)
                    root.innerHTML = htmlCode;
            }
        };

        var url = this.baseurl + lms4labs_paths['authenticate'] + this.extension;
        xmlhttp.open("GET", url, true);
        xmlhttp.send(null);
    };

}
