var styleHtml = "<style>body.showBrowserTipsSkip{height: 100%; padding: 0px; margin: 0px; overflow: hidden;}.browser-tips-wrap{position:fixed; _position: absolute; left:0; top:0; right:0; bottom:0; z-index:99999; width: 100%; height: 100%; margin: 0px; padding: 0px; display: none; }.browser-tips-wrap a{color:#333333; transition:0.5s; text-decoration: none;}.browser-tips-wrap a:hover{color:#cc9900}.browser-tips-wrap ul,.browser-tips-wrap li{margin:0px; padding:0px; list-style:none;}.browser-tips-wrap img{padding:0px; margin:0px; border:none; vertical-align:middle;}.browser-tips-wrap p{margin:0px; padding:0px; display:block;text-indent: 0; color:#333333}.browser-tips-wrap p.btw-box-txt-indent{text-indent: 2em}.browser-tips-wrap .btw-maks{position:absolute;left:0; top:0; right:0; bottom:0; height: 100%; width: 100%; background:#000000;  z-index:1; filter:alpha(opacity=50); opacity:0.5; }.browser-tips-wrap .btw-box{position:absolute;left:50%;top:50%;background:#ffffff;z-index:2;box-shadow: 0px 15px 8px rgba(0, 0, 0, 0.2);border-radius: 15px;width: 820px;height: 340px;margin-left: -450px;margin-top: -210px;box-sizing: content-box;padding: 40px;}.browser-tips-wrap .btw-box-txt{text-align:left; font-size:16px; line-height:30px;}.browser-tips-wrap .btw-box-txt p{text-align:left;font-size:16px;line-height: 40px;}.browser-tips-wrap .btw-box-browsers ul{overflow:hidden;display:block;padding-top: 40px;}.browser-tips-wrap .btw-box-browsers li{width:20%; float:left; text-align:center;}.browser-tips-wrap .btw-box-browsers li span{text-align:center; height:30px; line-height:30px; overflow:hidden; display:block; font-size:14px; }.browser-tips-wrap .btw-box-skip{text-align:right;padding-top: 60px;font-size:16px;}.browser-tips-wrap .btw-box-skip a.skip-btn{float: right; background: #337ab7; border: 1px solid #2e6da4; padding: 0 10px; color: #fff; text-decoration: none; user-select: none; border-radius: 4px;}.browser-tips-wrap .btw-box-skip a.skip-btn:hover{background-color: #286090; border-color: #204d74;}body.showBrowserTipsSkip .browser-tips-wrap{display: block; }</style>";
var browserTipsHtml = '<div class="browser-tips-wrap" id="browserTipsWrap"><div class="btw-box"><div class="btw-box-txt"><p>尊敬的用户，您好！</p><p class="btw-box-txt-indent">网站不支持您所使用的浏览器版本（可能会出现网页变形等问题）。为了更好地展示页面效果，请您使用以下浏览器（点击图标会跳转到相关浏览器的官方网站下载页面）。</p></div><div class="btw-box-browsers"><ul><li><a id="chromeUrl" href="https://www.google.cn/chrome/" target="_blank"><img src="/content/_common/base/img/icon-browser/br-chrome.png" alt="Chrome"><span>Chrome</span></a></li><li><a id="firefoxUrl" href="http://www.firefox.com.cn/" target="_blank"><img src="/content/_common/base/img/icon-browser/br-firefox.png" alt="Firefox"><span>Firefox</span></a></li><li><a id="edgeUrl" href="https://www.microsoft.com/zh-cn/edge" target="_blank"><img src="/content/_common/base/img/icon-browser/br-edge.png" alt="edge"><span>新Edge</span></a></li><li><a id="360Url" href="https://browser.360.cn/ee/" target="_blank"><img src="/content/_common/base/img/icon-browser/br-360.png" alt="360极速浏览器"><span>360极速浏览器</span></a></li><li><a id="qqUrl" href="https://browser.qq.com/" target="_blank"><img src="/content/_common/base/img/icon-browser/br-qq.png" alt="QQ浏览器"><span>QQ浏览器</span></a></li></ul></div><div class="btw-box-skip"><a href="javascript:closeUpdateBrowserTips();" class="skip-btn" id="browserTipsSkip">关闭提示</a></div></div><div class="btw-maks"></div></div>';
document.write(styleHtml + browserTipsHtml);
function updateBrowserTips() {
    function IEVersion() {
        var userAgent = navigator.userAgent;
        var isIE = userAgent.indexOf("compatible") > -1 && userAgent.indexOf("MSIE") > -1;
        var isEdge = userAgent.indexOf("Edge") > -1 && !isIE;
        var isIE11 = userAgent.indexOf("Trident") > -1 && userAgent.indexOf("rv:11.0") > -1;
        if (isIE) {
            var reIE = new RegExp("MSIE (\\d+\\.\\d+);");
            reIE.test(userAgent);
            var fIEVersion = parseFloat(RegExp["$1"]);
            if (fIEVersion == 7) {
                return 7
            } else if (fIEVersion == 8) {
                return 8
            } else if (fIEVersion == 9) {
                return 9
            } else if (fIEVersion == 10) {
                return 10
            } else {
                return 6
            }
        } else if (isEdge) {
            return "edge"
        } else if (isIE11) {
            return 11
        } else {
            return "notIE"
        }
    }
    function IsLowChromeOrFireFox() {
        var supportES6ChromeVersion = 80;
        var chromeVersion = getBrowserVersion("chrome");
        var chromeVersionNumber = chromeVersion.split(".")[0];
        if (chromeVersionNumber > 0 && chromeVersionNumber < supportES6ChromeVersion) {
            return true
        }
        var supportES6FireFoxVersion = 80;
        var firefoxVersion = getBrowserVersion("firefox");
        var firefoxVersionNumber = firefoxVersion.split(".")[0];
        if (firefoxVersionNumber > 0 && firefoxVersionNumber < supportES6FireFoxVersion) {
            return true
        }
        return false
    }
    function getBrowserVersion(browser) {
        if (!browser) {
            return "0"
        }
        var userAgent = navigator.userAgent.toLowerCase();
        var browserRegex = eval("/" + browser + "\\/([\\d.]+)/");
        var matchValue = userAgent.match(browserRegex);
        if (matchValue && matchValue.length == 2) {
            return matchValue[1]
        } else {
            return "0"
        }
    }
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(";");
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i].replace(" ", "");
            if (c.indexOf(name) == 0)
                return c.substring(name.length, c.length)
        }
        return ""
    }
    var ieVersion = window.updateBrowserTips.ieVersion = IEVersion();
    var isLowChromeOrFireFox = window.updateBrowserTips.isLowChromeOrFireFox = IsLowChromeOrFireFox();
    
    var notIE = ieVersion == "notIE";
    var browserTipsSkipCookie = getCookie("browserTipsSkip") == "true";
    if ((notIE && !isLowChromeOrFireFox) || browserTipsSkipCookie)
        return;
    showUpdateBrowserTips();
}

function showUpdateBrowserTips() {
    var bodyClass = "showBrowserTipsSkip";
    var body = document.getElementsByTagName("body")[0];
    body.className += " " + bodyClass
}

function hideUpdateBrowserTips() {
    var bodyClass = "showBrowserTipsSkip";
    var body = document.getElementsByTagName("body")[0];
    var bodyClassArr = body.className.split(" ");
    for (var i = 0; i < bodyClassArr.length; i++)
        bodyClassArr[i] === bodyClass && bodyClassArr.splice(i, 1);
    body.className = bodyClassArr.join(" ");
}

function closeUpdateBrowserTips() {
    var cookieDay = 7;
    var d = new Date();
    d.setTime(d.getTime() + cookieDay * 24 * 60 * 60 * 1000);
    var expires = "expires=" + d.toGMTString();
    document.cookie = "browserTipsSkip=true; " + expires + "; path=/";
    hideUpdateBrowserTips();
}

updateBrowserTips();