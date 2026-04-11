(function ($) {
    var appId,
        timeStamp,
        nonceStr,
        signature,
        imgUrl,
        title,
        desc;

    if (isWeiXinBrowser() && checkWeixinShareEnable()) {
        if (typeof window.WeixinJSBridge == "undefined") {
            $(document).on('WeixinJSBridgeReady', function () {
                getWeixinShareParameters();
            });
        }
        else {
            getWeixinShareParameters();
        }
    }

    function setImgUrl() {
        imgUrl = $('meta[name="Image"]').attr("content");
    }

    function setTitle() {
        title = $('meta[name="ArticleTitle"]').attr('content') || $('meta[name="ColumnName"]').attr('content');
    }

    function setDesc() {
        desc = $('meta[name="Description"]').attr('content');
    }

    function getWeixinShareParameters() {
        setImgUrl();
        setTitle();
        setDesc();
        if (imgUrl || title || desc) {
            var currentsiteinfoData = $("#currentsiteinfo").data();
            var siteHomeUrl = currentsiteinfoData.siteajaxrequestprefix;
            $.ajax({
                type: "get",
                url: siteHomeUrl + "weixin/home/AjaxGetWeixinShareParameters",
                dataType: 'json',
                async: false,
                data: { currentUrl: getSharedUrl() },
                success: function (data) {
                    if (data !== false) {
                        appId = data.appId;
                        timeStamp = data.timestamp;
                        nonceStr = data.nonceStr;
                        signature = data.signature;
                        setWxConfig();
                    }
                }
            });
        }
    }

    function setWxConfig() {
        wx.config({
            debug: false, // 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
            appId: appId, // 必填，公众号的唯一标识
            timestamp: timeStamp, // 必填，生成签名的时间戳
            nonceStr: nonceStr, // 必填，生成签名的随机串
            signature: signature, // 必填，签名
            jsApiList: [
                'checkJsApi',
                'updateAppMessageShareData',
                'updateTimelineShareData',
                'onMenuShareTimeline',
                'onMenuShareAppMessage',
                'onMenuShareQQ',
                'onMenuShareWeibo',
                'hideMenuItems',
                'showMenuItems',
                'hideAllNonBaseMenuItem',
                'showAllNonBaseMenuItem',
                'translateVoice',
                'startRecord',
                'stopRecord',
                'onRecordEnd',
                'playVoice',
                'pauseVoice',
                'stopVoice',
                'uploadVoice',
                'downloadVoice',
                'chooseImage',
                'previewImage',
                'uploadImage',
                'downloadImage',
                'getNetworkType',
                'openLocation',
                'getLocation',
                'hideOptionMenu',
                'showOptionMenu',
                'closeWindow',
                'scanQRCode',
                'chooseWXPay',
                'openProductSpecificView',
                'addCard',
                'chooseCard',
                'openCard'
            ]
        });

        wx.error(function (res) {
            console.log(res);
            console.warn('微信验证失败，分享功能无法正常使用！');
        });

        wx.ready(function () {
            wx.updateAppMessageShareData({
                title: title,
                desc: desc,
                imgUrl: imgUrl,
                link: window.location.href
            });

            wx.updateTimelineShareData({
                title: title,
                desc: desc,
                imgUrl: imgUrl,
                link: window.location.href
            });
        });
    }

    function isWeiXinBrowser() {
        var userAgent = window.navigator.userAgent.toLowerCase();
        if (userAgent.match(/MicroMessenger/i) == 'micromessenger') {
            return true;
        } else {
            return false;
        }
    }
    function checkWeixinShareEnable() {
        var siteId = $("meta[name=SiteId]").attr("content");
        var weixinShareItem = window.POWER_WEIXINSHARE_CONFIG && window.POWER_WEIXINSHARE_CONFIG.WeixinShareItems && window.POWER_WEIXINSHARE_CONFIG.WeixinShareItems[siteId];
        return weixinShareItem;
    }

    function getSharedUrl() {
        var hrefUrl = location.href;
        var query = location.search;
        if (query) {
            if (query.indexOf('SessionVerify=') > -1) {
                return location.origin + location.pathname;
            }
        }
        return hrefUrl;
    }
})(jQuery);