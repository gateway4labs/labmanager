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

function Laboratory(url, elementName) {
    
    this.url = url;

    if (elementName == undefined) {
        this.elementName = DEFAULT_ROOT_ELEMENT;
    } else {
        this.elementName = elementName;
    }

    this.load = function(laboratoryId, onerror) {

        var xmlhttp     = getXmlHttpObject();
        var elementName = this.elementName;

        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4) {
                var root = document.getElementById(elementName);

                if(root == null) {
                    alert("lms4labs.js misconfigured. Either create a " + DEFAULT_ROOT_ELEMENT + " value or pass an argument");
                    return;
                }

                var response = xmlhttp.responseText;

                var htmlCode;
                if (response.indexOf('http') == 0) {
                    htmlCode = "ok";
                } else if (response.indexOf('error:') == 0) {
                    htmlCode = "<h1>Error</h1><p>" + response.substring('error:'.length) + "</p>";
                } else {
                    if(onerror == undefined) {
                        htmlCode = "Unknown error. The following code was returned: " + response;
                    } else {
                        onerror(xmlhttp.responseText);
                        return;
                    }
                }
                root.innerHTML = htmlCode;
            }
        };

        var requestPayload = "{ \"action\" : \"reserve\", \"experiment\" : \"" + laboratoryId.replace(/\"/g, '\\"') + "\" }";

        xmlhttp.open("POST", this.url, true);
        xmlhttp.setRequestHeader('Content-Type', 'application/json');
        xmlhttp.send(requestPayload);
    };
}
