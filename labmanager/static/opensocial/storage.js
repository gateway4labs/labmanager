var SG_PRODUCTION = true;

function reportStarted(labName, labURL, labSessionId) {
    var initialMetadata, labResourceType;
    labResourceType = "labResource";

    initialMetadata = {
        "id": "",
        "published": "",
        "actor": {
            "objectType": "person",
            "id": "unknown",
            "displayName": "unknown"
        },
        "target": {
            "objectType": labResourceType,
            "id": labSessionId,
            "displayName": "unnamed"
        },
        "generator": {
            "objectType": "application",
            "url": labURL,
            "id": "unknown",
            "displayName": labName
        },
        "provider": {
            "objectType": "ils",
            "url": window.location.href,
            "id": "unknown",
            "inquiryPhase": "unknown",
            "inquiryPhaseId": "unknown",
            "inquiryPhaseName": "unknown",
            "displayName": "unknown"
        }
    };

    // replace with ".GoLabMetadataHandler" in production context
    var currentMetadataHandlerClass;
    var loggingTarget;
    if (SG_PRODUCTION) {
        currentMetadataHandlerClass = window.golab.ils.metadata.GoLabMetadataHandler;
        loggingTarget = "opensocial";
    } else {
        currentMetadataHandlerClass = window.golab.ils.metadata.LocalMetadataHandler;
        loggingTarget = "console";
    }

    new currentMetadataHandlerClass(initialMetadata, function(error, metadataHandler) {
        if (error) {
            return console.error("failed to create metadataHandler: " + error);
        } else {
            window.actionLogger = new window.ut.commons.actionlogging.ActionLogger(metadataHandler);
            window.actionLogger.setLoggingTarget(loggingTarget);
            window.actionLogger.logApplicationStarted();
        }
    });
}
