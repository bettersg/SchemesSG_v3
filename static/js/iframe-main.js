$(function(){
    if ($(window).width() >= 767) {
    $('#iframe-holder').html("");
    $('#iframe-holder').css('height', "133vw")
    $('#iframe-holder').append(
        '<div class="col-xl-12 google-data-studio"><iframe src="https://datastudio.google.com/embed/reporting/e8187b37-7af2-4166-b61a-eb54446bb86c/page/v0CAC" frameborder="0" style="border:0" allowfullscreen></iframe></div>'
    )}
    if ($(window).width() < 767) {
        $('#iframe-holder').html("");
        $('#iframe-holder').css('height', "150vw")
        $('#iframe-holder').append(
            '<div class="col-xl-12 google-data-studio"><iframe src="https://datastudio.google.com/embed/reporting/e9511193-d184-432c-9db7-12061cd74d93/page/0V2DC" frameborder="0" style="border:0" allowfullscreen></iframe></div>'
        )}
});


/* $(window).on('resize',function(){
    if ($(window).width() >= 767) {
    $('#iframe-holder').html("");
    $('#iframe-holder').append(
        '<div class="col-xl-12 google-data-studio"><iframe width="1200" height="600" src="https://datastudio.google.com/embed/reporting/5621beb1-3a1e-486b-9121-66f25382eab0/page/v0CAC" frameborder="0" style="border:0" allowfullscreen></iframe></div>'
    )}
    if ($(window).width() < 767) {
        $('#iframe-holder').html("");
        $('#iframe-holder').append(
            '<div class="col-xl-12 google-data-studio"><iframe width="600" src="https://datastudio.google.com/embed/reporting/e9511193-d184-432c-9db7-12061cd74d93/page/0V2DC" frameborder="0" style="border:0" allowfullscreen></iframe></div>'
        )}
}); */