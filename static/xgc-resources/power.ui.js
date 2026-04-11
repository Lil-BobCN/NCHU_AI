/**
 * 此文件的头部注释
 */

/*global jQuery: false */

(function ($) {
    'use strict';

    pe.ui = {};
    var $home = window.top.pe.home;
    var frameHistory = function (frameName) {
        this.frameName = frameName;
        this.records = [];
    };

    frameHistory.prototype = {
        frameName: '',
        add: function (url) {
            this.records.push(url);
        },
        back: function () {
            this.records.pop();
            var src = this.records.pop();
            window.top.$('iframe[data-historian=' + this.frameName + ']').prop('src', src);
        }
    };

    var history = function () {
        var ele;
        if (window.top.pe.ui.history) {
            ele = window.top.pe.ui.history;
        } else {
            window.top.pe.ui.history = ele = {};
        }

        this.records = ele;
    };

    history.prototype = {
        records: null,
        frame: function (name) {
            if (name in this.records) {
                return this.records[name];
            } else {
                var fh = new frameHistory(name);
                this.records[name] = fh;

                return fh;
            }
        }
    };

    pe.ui.historian = function () {
        return new history();
    };

    function bindNewTabLink() {
        $('body')
            .on('click',
                'a',
                function (e) {
                    var $this = $(this),
                        url = $this.prop('href');
                    if (url && ($this.is("[data-tabs-target='_blank']") || e.ctrlKey)) {
                        $home.tabs.addTab(url);
                        return false;
                    }

                    return true;
                });

    }

    $(function () {
        $(".btn.disabled")
            .click(function () {
                return false;
            });
        $('.history-back')
            .each(function (i, n) {
                var frame = $home.currentFrame(),
                    self = $(this);
                if (pe.ui.historian().frame(frame.attr('data-historian')).records.length < 1) {
                    self.addClass('disabled');
                    self.on('click', function (e) { return false; });
                } else {
                    self.on('click',
                        function (e) {
                            var $home = window.top.pe.home,
                                frame = $home.currentFrame();
                            pe.ui.historian().frame(frame.attr('data-historian')).back();

                            return false;
                        });
                }

            });

        bindNewTabLink();
    });

    $('.unselect').on('selectstart', function (e) { return false; }).attr('unselectable', 'on');

    $.each($('a[data-confirm]'),
        function () {
            var $this = $(this);
            var placement = 'bottom';
            if ($this.data('placement')) {
                placement = $this.data('placement');
            }
            var message = $this.attr('data-confirm');
            $this.confirmation({
                placement: placement,
                title: message,
                btnOkLabel: '确定',
                btnCancelLabel: '取消',
                popout: false,
                onConfirm: function (event, element) {
                    var href = $(element).attr('href');
                    if (href) {
                        window.location.href = href;
                    } else {
                        var confirm = $this.data("onConfirm");
                        if (confirm) {
                            confirm();
                        }
                    }

                }
            });
        });



    var videoElements = [];
    /*
    videoSrc：视频地址
    succeedFunc：获取视频帧成功后回调
    errorFunc：获取视频帧失败后回调
    imgWidth：生成图片宽度
    imgHeight：生成图片高度
    */
    pe.ui.VideoCover = function (videoSrc, succeedFunc, errorFunc, imgWidth, imgHeight) {
        if (videoSrc) {
            var videoElement = document.createElement("VIDEO");
            videoElement.src = videoSrc;
            videoElement.muted = true;
            videoElement.autoplay = true;   // 视频一定要设置自动播放，否则抓出来的封面不是白的就是透明的
            videoElement.setAttribute("crossOrigin", 'anonymous');
            videoElement.setAttribute('playsinline', '');
            videoElement.setAttribute('webkit-playsinline', ''); //这个属性是内联播放，避免在ios中，ios会劫持播放器，自动弹出播放界面
            videoElement.addEventListener("loadeddata", function() {
                try {
                    var videoWidth = videoElement.videoWidth, videoHeight = videoElement.videoHeight;  // 获取video的宽高
                    // var maxLength = videoWidth > videoHeight ? videoWidth : videoHeight;
                    // 固定视频缩略图生成比例
                    var imgWidth = 800;
                    var imgHeight = 450;
                    var x = 0, y = 0, width = 0, height = 0;
                    // 计算缩小后图片的宽高以及canvas绘制的位置信息
                    if (videoWidth / videoHeight >= 1.5) {
                        width = imgWidth;
                        height = videoHeight * (imgWidth / videoWidth);
                        x = 0;
                        y = (imgHeight - height) / 2;
                    } else {
                        height = imgHeight;
                        width = videoWidth * (imgHeight / videoHeight);
                        y = 0;
                        x = (imgWidth - width) / 2;
                    }
                    var canvas = document.createElement("canvas");
                    canvas.width = imgWidth;
                    canvas.height = imgHeight;
                    var ctx = canvas.getContext("2d");
                    ctx.fillStyle = "#000";
                    ctx.fillRect(0, 0, imgWidth, imgHeight);
                    ctx.drawImage(videoElement, x, y, width, height);
                    var src = canvas.toDataURL("image/jpeg"); // 完成base64图片的创建
                    if (succeedFunc) { succeedFunc(src) }
                    // 清空video对象
                    videoElements.splice($.inArray(videoElement, videoElements), 1);
                    videoElement = null;
                } catch (e) {
                    if (errorFunc) { errorFunc() }
                }
            })
            videoElement.addEventListener("error", function () {
                if (errorFunc) { errorFunc() }
            });
            videoElements.push(videoElement);   // 存储video对象防止回收
        }
    }

    // 针对前台视频列表页视频封面的帧初始化
    $(function () {
        $(".video-showcover img").each(function () {
            var $imgDiv = $(this),
                videoSrc = $imgDiv.data('videourlforcoverimage');
            pe.ui.VideoCover(videoSrc,
                function (src) { $imgDiv.attr('src', src); },
                function () { $imgDiv.attr('src', '/content/_common/base/img/nopic.gif'); }
            )
        });

        $("video").each(function () {
            var $videoDiv = $(this),
                videoSrc = this.src;
            $videoDiv.attr('webkit-playsinline', '');
            $videoDiv.attr('playsinline', '');
            $videoDiv.attr('preload', 'auto');
            if ($videoDiv.attr('poster')) {
                return;
            }
            pe.ui.VideoCover(videoSrc,
                function (src) { $videoDiv.attr('poster', src); },
                function () { $videoDiv.attr('poster', '/content/_common/base/img/nopic.gif'); }
            )
        })
    });

    /**
     * HTML标签XSS过滤
     *
     * @param {String} html
     * @return {String}
     */
    pe.ui.filterXSS = function (html) {
        return filterXSS(html, {
            onIgnoreTagAttr: function (tag, name, value, isWhiteAttr) {
                if (name === 'class' ||
                    name === 'hidefocus' ||
                    name.substr(0, 5) === 'data-' ||
                    name.substr(0, 7) === 'action-'
                ) {
                    return name + '="' + filterXSS.escapeAttrValue(value) + '"'; // 通过内置的escapeAttrValue函数来对属性值进行转义
                }
            }
        });
    }

    /**
     * String字符串XSS过滤
     *
     * @param {String} string
     * @return {String}
     */
    pe.ui.filterStringXSS = function (string) {
        return filterXSS(string, {
            whiteList: {},        // 白名单为空，表示过滤所有标签
            stripIgnoreTag: true,      // 过滤所有非白名单标签的HTML
            stripIgnoreTagBody: ['script'] // script标签较特殊，需要过滤标签中间的内容
        }).replace(/'/g, "").replace(/"/g, "");
    }

    $(function () {
        // 查看原图
        $(".swp-tool a[class='swpt-full-tip']").on("click", function () {
            var url = "";
            $("ul.swp-hd-list>li").each(function () {
                var that = $(this);
                if ($(that).hasClass("current")) {
                    url = $(that).find(".swp-img>img").attr("src");
                    return false;
                }
            });

            if (url) {
                window.open(url, "_blank");
            }
        });
    });
}(jQuery));