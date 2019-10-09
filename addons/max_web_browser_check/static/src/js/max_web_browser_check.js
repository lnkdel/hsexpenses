var result = false;
var ua = navigator.userAgent;
if (ua.indexOf("Firefox") != -1 || ua.indexOf("Chrome") != -1 || ua.indexOf("Safari") != -1) {
    result = true;
}
if (!result) {
    window.location.href = '/max_web_browser_check/static/src/html/browser.html';
}
