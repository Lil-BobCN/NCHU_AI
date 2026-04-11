/**
 * 此文件的头部注释
 */

/*global jQuery: false, window: false */

(function ($) {
    'use strict';

    var pe,
        tools;

    pe = window.pe = {};

    tools = {
        /**
         * 判断要加的链接符是?还是&
         * @param {} url 
         * @returns {} 
         */
        connect: function (url) {
            var connect = "?";
            if (url.indexOf("?") > -1) {
                connect = "&";
            }
            return connect;
        },
        /**
         * 不同的浏览器分割hash码
         * @param {} url 
         * @returns {} 
         */
        diffBrowserSplitHash: function (hash) {
            var hashStr = "";
            if (hash.indexOf("#/") > -1) {
                hashStr = hash.split("#/")[1];
            } else if (hash.indexOf("##") > -1) {
                hashStr = hash.split("##")[1];
            }
            return hashStr;
        },
        /**
         * 特殊处理state参数

         * @param {} url 
         * @returns {} 
         */
        FilterStateSpecialChar: function (stateParam) {
            if (stateParam.substring(0, 1) === "/") {
                return stateParam.substring(1);
            }

            return stateParam;
        },
        /**
         * 合并Url的参数。
         * @param {string} url 要合并参数的Url
         * @param {Object<string,object>} param 参数 ，使用键值对对象。
         * @returns {string} 合并完成后的js
         */
        connectUrl: function (url, param) {
            var querystring = url.split('?')[1] || '';
            var params = [];
            if (querystring) {
                params = querystring.split('&');
            }

            if (param) {
                for (var item in param) {
                    if (param.hasOwnProperty(item)) {
                        params.push(item + '=' + param[item]);
                    }
                }
            }

            return url.split('?')[0] + '?' + params.join('&');
        },

        /**
        * 生成一组随机的Id号码
        * @param len 长度
        * @param radix   参数
        * @returns {string}  id号码
        */
        uuid: function (len, radix) {
            len = len || 8;
            radix = radix || 2;
            var CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                .split(''); // UNDONE [2014-4-17] [] 变量小写命名。这里为什么要把CHARS变量赋值给chars，而不直接用CHARS。
            var chars = CHARS,
                uuid = [],
                i;
            radix = radix || chars.length;
            if (len) {
                for (i = 0; i < len; i++) {
                    uuid[i] = chars[0 | Math.random() * radix];
                }
            } else {
                var r;
                uuid[8] = uuid[13] = uuid[18] = uuid[23] = '-';
                uuid[14] = '4';
                for (i = 0; i < 36; i++) {
                    if (!uuid[i]) {
                        r = 0 | Math.random() * 16;
                        uuid[i] = chars[(i == 19) ? (r & 0x3) | 0x8 : r];
                    }
                }
            }
            return uuid.join('');
        },
        errorResultHandler: {
            'NotAuthenticated': function (result) {
                window.top.location.href = result.LogOnUrl;

                return '';
            },

            'NotAuthorized': function (result) {
                return '您没有权限查看所请求的内容';
            }

        },
        RegexHelper: {
            Url: /(http:\/)?\/[^\/]+/

        },
        /**
        * 裁剪字符串
        * @param str {string} 要剪裁的字符串
        * @param n {Number} 剪裁的长度
        * @returns {string}  剪裁好的字符串。
        */
        truncateStr: function (str, n) { // UNDONE [2014-4-17] [] 函数命名不要使用简写；变量命名问题；变量统一在代码块开头命名，还是就近命名（变量i）？
            var r = /[^\x00-\xff]/g;
            var i;
            if (str.replace(r, 'mm').length <= n) {
                return str;
            }
            // n = n - 3;    
            var m = Math.floor(n / 2);
            for (i = m; i < str.length; i++) {
                if (str.substr(0, i).replace(r, 'mm').length >= n) {
                    return str.substr(0, i) + '...';
                }
            }

            return str;
        },
        HTMLEncode: function (text) {
            return $('<div/>').text(text).html();
        },
        HTMLDecode: function (text) {
            return $('<div/>').html(text).text();
        },
        /*
         * 给url增加当前的hash值
         * @param url {string} 要增加hash值的url
         * @return {string} 增加了hash值得url
         */
        AddCurrentHash: function (url) {
            if (!!url) {
                var hash = 'state=' + window.location.hash.replace(/^#*/, '');
                hash = hash.replace("%20", "+");
                url += (/\?/.test(url) ? '&' : '?') + hash;
            }
            return url;
        },

        /**
         * 路径操作助手。
         */
        PathHelperUtils: {
            /**
            * 路径上传目录替换符转换为上传目录， 处理兼容情况。
            * @param {string} path 原路径。
            * @param {string} symbol
            * @param {string} uploadDirectory
            * @return {string} 返回结果。
            */
            ReplacePathSymbolForShow: function (path, symbol, uploadDirectory) {
                if (path && symbol && uploadDirectory) {
                    path = path.TrimStartReplace("~");
                    uploadDirectory = uploadDirectory.TrimStartReplace("~");

                    if (path.indexOf(symbol) == 0) {
                        var uploadPathPrefix = ""; //// 上传目录前缀，默认是空字符串。
                        path = uploadPathPrefix + uploadDirectory + path.substring(symbol.length);
                    }
                }

                return path;
            },
            /**
            * 路径上传目录替换符转换为上传目录， 处理兼容情况。
            * @param {string} path 原路径。
            * @param {string} symbol 上传目录替换符。
            * @param {string} uploadVirtualPath 上传虚拟路径。
             * @param {object} regExp 正则表达式RegExp对象，如果传入则使用传入的，否则使用内部正则表达式的。
            * @return {string} 返回结果。
            */
            ReplaceContentSymbolForShow: function (path, symbol, uploadVirtualPath, regExp) {
                var regexString = "((src|href)\\s*=\\s*(\"|\'))\\$?\\/(\\/|\\w|\\.|\\{|\\})*";
                if (path && symbol && uploadVirtualPath) {
                    path = path.TrimStartReplace("~");
                    uploadVirtualPath = uploadVirtualPath.TrimStartReplace("~");

                    if (!regExp) {
                        regExp = new RegExp(regexString, 'gi');
                    }

                    path = path.replace(regExp, function (match, p1) {
                        var value = match;
                        if (match && p1 && match.indexOf(p1) == 0) {
                            var attributeValue = match.substring(p1.length);
                            attributeValue = attributeValue.ReplacePathSymbolForShow(symbol, uploadVirtualPath);
                            value = p1.concat(attributeValue);
                        }

                        return value;
                    });
                }

                return path;
            },
            TrimStartReplace: function (orignal, target) {
                if (orignal && target && orignal.length >= target.length) {
                    while (orignal && orignal.indexOf(target) == 0) {
                        orignal = orignal.substring(target.length);
                    }
                }

                return orignal;
            }
        },
        EncryptBase64ForJs: function (original) { return window.btoa(window.encodeURIComponent(original)); },
        DecryptBase64ForJs: function (value) { return window.decodeURIComponent(window.atob(value)); }
    };

    pe.tools = tools;

    //object .create
    if (typeof Object.create !== 'function') {
        Object.create = function (o) {
            var f = function () {};
            f.prototype = o;

            return new f();
        };
    }

    //Function method

    if (typeof Function.method !== 'function') {
        Function.prototype.method = function (name, func) {
            this.prototype[name] = func;
            return this;
        };
    }

    pe.messager = {
        sendMessage: function (frame, eventName, sendData) {
            var $iframe = $(frame);
            var data = {
                event: 'power.' + eventName,
                data: sendData
            };
            frame.contentWindow.postMessage(JSON.stringify(data), '*');
        }
    };

    /**
     * 替换路径中的上传占位符。
     * @param {string} symbol 目录替换符。
     * @param {any} uploadDirectory 上传虚拟目录路径。
     * @return {string} 结果。
     */
    String.prototype.ReplacePathSymbolForShow = function (symbol, uploadDirectory) {
        var path = this;
        return pe.tools.PathHelperUtils.ReplacePathSymbolForShow(path, symbol, uploadDirectory);
    };

    /**
     * 替换内容中的上传站位符。
     * @param {string} symbol 目录替换符。
     * @param {string} uploadpath 上传虚拟目录路径。
     * @param {object} regExp 自定义正则。如果传入则使用传入的，如果没有则使用默认的。
     * @return {string} 结果。
     */
    String.prototype.ReplaceContentSymbolForShow = function (symbol, uploadpath, regExp) {
        var content = this;
        return pe.tools.PathHelperUtils.ReplaceContentSymbolForShow(content, symbol, uploadpath, regExp);
    };

    String.prototype.TrimStartReplace = function (target) {
        var orignal = this;
        return pe.tools.PathHelperUtils.TrimStartReplace(orignal, target);
    };
}(jQuery));