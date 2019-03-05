var SG_PRODUCTION = true;

function reportStarted(labName, labURL, labSessionId) {
    var timezone_minutes = new Date().getTimezoneOffset();
    $.post(STATS_ADDRESS + "&timezone_minutes=" + timezone_minutes, {});
}

