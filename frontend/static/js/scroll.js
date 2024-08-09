$(document).ready(function (){
    $("#clicktoscroll").click(function (){
        $('html, body').animate({
            scrollTop: $("#schemespal").offset().top
        }, 400);
    });
});