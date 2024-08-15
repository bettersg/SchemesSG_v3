if (window.location.search.indexOf('query') == 1) {
    $(document).ready(setTimeout(function () {
        $('html, body').animate({
            scrollTop: $("#scrollhere").offset().top
        }, 400);
    },800)
    );

    //var newURL = location.href.split("?")[0]
    //window.history.pushState('object', document.title, newURL)

}
//if (window.location.search.indexOf('query') == 1) {$("#filler")[0].scrollIntoView()}