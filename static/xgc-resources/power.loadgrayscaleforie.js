$(function () {
    'use strict';

    var grayscaleConfig = window.POWER_GRAYSCALE_CONFIG;
    if (!grayscaleConfig) {
        return;
    }

    var startDateTime = new Date(grayscaleConfig.StartDateTime);
    var endDateTime = new Date(grayscaleConfig.EndDateTime);
    var nowDate = new Date();

    if (grayscaleConfig.Enabled &
        nowDate.getTime() >= startDateTime.getTime() &
        nowDate.getTime() <= endDateTime.getTime() &
        checkSiteScope() & checkPageScope()) {
        var navStr = navigator.userAgent.toLowerCase();
        if (navStr.indexOf("msie 10.0") !== -1 || navStr.indexOf("rv:11.0") !== -1) {
            $.when($.ajax()).then(function () {
                grayscale($("html"));
            });

            $('.mainNav li a').hover(
                function () {
                    $(this).css("background", "#545454");
                },
                function () {
                    $(this).css("background", "#585858");
                });

            subMenuFixed = true;
            var subMenuTop = $(".topNav").offset().top;
            $(window)
                .scroll(function () {
                    if (subMenuFixed) {
                        if ($(window).scrollTop() >= subMenuTop) {
                            $(".topNav").addClass("topNav-fixed");
                            $(".topNav").css("background", "#585858");
                        } else {
                            $(".topNav").removeClass("topNav-fixed");
                            $(".topNav").css("background", "");
                        }
                    }
                });
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
})