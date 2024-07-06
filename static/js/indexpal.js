function handle_indexpal() {

    const scriptURLindexpal = 'https://script.google.com/macros/s/AKfycbwgKnPhUBHnlGJ3YudlSeaMfjUe9mPaI-N3Sbz9uar52oDDFf0/exec'
    const indexpalform = document.getElementById("indexpal")

    fetch(scriptURLindexpal, { method: 'POST', body: new FormData(indexpalform) })
        .then(response => console.log("Done!"))
        .catch(error => console.error('Error!', error.message));


    window.location = "schemespal.html?query=" + $('textarea#indexpal-text').val() + "&relevance=20"
}