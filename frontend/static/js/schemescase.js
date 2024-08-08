const scriptURLschemescase = 'https://script.google.com/macros/s/AKfycbyqGHt2p224ebUahB6XDOgxtru9fvXm3YonCKcPus--p8e57TFB/exec'
const schemescase = document.getElementById("schemescase")
schemescase.addEventListener('submit', e => {
    e.preventDefault()
    $("#schemescase-submit").html("Submitting...");
    fetch(scriptURLschemescase, { method: 'POST', body: new FormData(schemescase) })
        .then(response => window.location.replace("gotit.html"))
        .catch(error => console.error('Error!', error.message))
})
