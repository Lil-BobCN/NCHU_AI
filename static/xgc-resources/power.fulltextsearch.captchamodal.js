var _pallback = function () { };
$(function () {
    $("[data-id=search]").click(function () {
        this
        if ($("#js-ticket-search").val() == "" && $("#js-ticketId-search").val() == "") {
            $('#captchaticketvalid-search')[0].className = "field-validation-error";
            searchCaptchaCallback();
            return;
        }
        else {
            $('#captchaticketvalid-search')[0].className = "field-validation-valid";
            closeModal();
            _pallback();
        }
    });

    $(".close").click(function () {
        closeModal();
    });

    $('#SearchValidateCode')
        .keydown(function (e) {
            e = window.event || e;
            if (e.keyCode == 13) {
                var $this = $(this);
                var keyword = encodeURIComponent($this.val());
                if (keyword) {
                    $("[data-id=search]").trigger("click");
                }
            }
        });

    searchCaptchaCallback()
});

function validateCode(pallback, validateKeywordEmpty) {
    if ((validateKeywordEmpty == undefined || validateKeywordEmpty) && ($("input[name=wd]").val() == "" && $("input[name=wdh]").val() == "") && $('#isadvancesearch').val() == "false") {
        alert("请输入关键词");
        return;
    }

    _pallback = pallback;
    var url = $(".search").attr("data-val-captcha-visible-url");
    $.ajax({
        type: "get",
        url: url,
        dataType: 'text',
        async: false,
        cache: false,
        success: function (data) {
            if (data == "True" && $("#VolidateCodeDiv,.modal-backdrop").length > 0) {
                // 不必弹出验证码。
                // openModal();
                SimCaptcha.SetSuccessCallBack("js-btn-verify-search",function(){
                    $("[data-id=search]").click();
                })
                $("#js-btn-verify-search").attr("captcha-after","js-btn-verify-search");
                $("#js-btn-verify-search").click();
                searchCaptchaCallback();

                $.refreshCsrf();
            } else {
                closeModal();
                _pallback();
            }
        }
    });
}

function openModal() {
    $("#VolidateCodeDiv,.modal-backdrop").show();
    $(".field-validation-error").html("");
    $("#SearchValidateCode").val("");
    $("body").addClass("modal-open");
    $("#VolidateCodeDiv .validationcode img").trigger("click");
}

function closeModal() {
    $("#VolidateCodeDiv,.modal-backdrop").hide();
    $("body").removeClass("modal-open");
}

function refreshValidateCode() {
    searchCaptchaCallback()
}

function searchCaptchaCallback() {
    if (document.getElementById("js-btn-verify-search") == null) {
        return;
    }
    $("#js-btn-verify-search").val("点击验证");
    $("#js-ticket-search").val(null);
    $("#js-ticketId-search").val(null);
    if ($("#js-btn-verify-search")[0]) {
        $("#js-btn-verify-search")[0].className = "btn btn-default";
    }
    // 点击验证
    window.searchSimCaptcha = new SimCaptcha({
        element: document.getElementById("js-btn-verify-search"),
        appId: "00000000",
        callback: function (res) {
            // 点触验证码
            if (res.code === 0) {
                $("#js-btn-verify-search").val("验证通过");
                $("#js-btn-verify-search")[0].className = "btn btn-success";
                $("#js-btn-verify-search").prop("onclick", null);
                $("#js-ticket-search").val(res.ticket);
                $("#js-ticketId-search").val(res.ticketId);
                if ($('#captchaticketvalid-search')[0]) {
                    $('#captchaticketvalid-search')[0].className = "field-validation-valid";
                }
            }
        },
        baseUrl: "/"
    });
}