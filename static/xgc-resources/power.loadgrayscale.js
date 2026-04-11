$(function () {
    'use strict';
    var grayscaleStyle =
        'html{' +
        '  -webkit-filter: grayscale(100%);' +
        '  -moz-filter: grayscale(100%)!important;' +
        '  -ms-filter: grayscale(100%);' +
        '  -o-filter: grayscale(100%)!important;' +
        '  filter: grayscale(100%);' +
        '  filter: progid:DXImageTransform.Microsoft.BasicImage(grayscale = 1) \\9;' +
        '  filter: gray !important;' +
        '}';

    var grayscaleConfig = window.POWER_GRAYSCALE_CONFIG;
    if (!grayscaleConfig) {
        return;
    }

    var startDateTime = new Date(grayscaleConfig.StartDateTime);
    var endDateTime = new Date(grayscaleConfig.EndDateTime);
    var nowDate = new Date();

    var siteStyleCode = $("#currentsiteinfo").data("discolorationstylecode");
    grayscaleStyle = siteStyleCode || grayscaleConfig.StyleCode || grayscaleStyle;

    if (grayscaleConfig.Enabled &
        nowDate.getTime() >= startDateTime.getTime() &
        nowDate.getTime() <= endDateTime.getTime() &
        checkSiteScope() & checkPageScope()) {
        var navStr = navigator.userAgent.toLowerCase();
        if (navStr.indexOf("msie 10.0") == -1 || navStr.indexOf("rv:11.0") == -1) {
            $("head").append("<style>" + grayscaleStyle + "</style>");
        }
    }

    function checkSiteScope() {
        if (grayscaleConfig.SiteScope) {
            if (grayscaleConfig.SiteScope == 'AllSite') {
                return true;
            }

            if (grayscaleConfig.SiteScope == 'OnlyMain') {
                if ($("meta[name=SiteId]").attr("content") == '1') {
                    return true;
                }
            }

            if (grayscaleConfig.SiteScope == 'SpecifySite') {
                var siteId = $("meta[name=SiteId]").attr("content");
                if (grayscaleConfig.SpecifySites && grayscaleConfig.SpecifySites.includes(parseInt(siteId))) {
                    return true;
                }
            }

            return false;
        }

        return true;
    }

    function checkPageScope() {
        if (grayscaleConfig.PageScope) {
            if (grayscaleConfig.PageScope == 'AllPage') {
                return true;
            }

            if (grayscaleConfig.PageScope == 'OnlyHome') {
                if ($('meta[name=IsHome]').attr('content') == 'true' ||
                    $('meta[name=ColumnName]').attr('content') == '网站首页') {
                    return true;
                }
            }

            return false;
        }

        return true;
    }
});