const scriptURLadd = 'https://script.google.com/macros/s/AKfycbzc8abpu0k4c9zs3ELG4aRY0HkjZksEIMQbam2sA31C4kqFzrwU/exec'
const formadd = document.getElementById("add-listing")
formadd.addEventListener('submit', e => {
    e.preventDefault()
    $("#addlist-submit").html("Submitting...");
    fetch(scriptURLadd, { method: 'POST', body: new FormData(formadd) })
        .then(response => window.location.replace("gotit.html"))
        .catch(error => console.error('Error!', error.message))
})

const scriptURLedit = 'https://script.google.com/macros/s/AKfycbyXWqdWuzjOgOyiF46jY_LuGk9u0dzDpFnBgWSvQoGu2IBg4Q8/exec'
const formedit = document.getElementById("edit-listing")
formedit.addEventListener('submit', e => {
    e.preventDefault()
    $("#editlist-submit").html("Submitting...");
    fetch(scriptURLedit, { method: 'POST', body: new FormData(formedit) })
        .then(response => window.location.replace("gotit.html"))
        .catch(error => console.error('Error!', error.message))
})

const scriptURLfeedback = 'https://script.google.com/macros/s/AKfycbwN3CXj_MHbWqSU_HuoIMUbjrPFZc0WKKs6d0HLiW2qXZ0ih_5G/exec'
const feedback = document.getElementById("feedback")
feedback.addEventListener('submit', e => {
    e.preventDefault()
    $("#feedback-submit").html("Submitting...");
    fetch(scriptURLfeedback, { method: 'POST', body: new FormData(feedback) })
        .then(response => window.location.replace("gotit.html"))
        .catch(error => console.error('Error!', error.message))
})