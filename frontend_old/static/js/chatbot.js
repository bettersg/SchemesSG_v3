function scrollToBottom() {
    var div = document.getElementById("chatwindow");
    div.scrollTop = div.scrollHeight;
}

async function getChatResponse(userInput) {
    const response = await fetch("/chatbot", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data: userInput })
    });

    const result = await response.json();
    return result;
}

let temp = document.getElementById('temp');
let index = 0;

// Deprecated(?)
// function displayNextLetter() {
//   scrollToBottom();
//   if (index < message.length) {
//     temp.innerHTML = temp.innerHTML + message[index];
//     index++;
//     setTimeout(displayNextLetter, 30);
//   } else {
//     temp.removeAttribute("id");
//     sendBtn.disabled = false;
//     userInputArea.disabled = false;
//   }
// }
