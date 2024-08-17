var url = "http://127.0.0.1:8000/chatbot";

function scrollToBottom() {
  var div = document.getElementById("chatwindow");
  div.scrollTop = div.scrollHeight;
}

async function getChatResponse(userInput) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: userInput }),
  });

  const result = await response.json();
  return result;
}

let temp = document.getElementById("temp");
let index = 0;
function displayNextLetter() {
  scrollToBottom();
  if (index < message.length) {
    temp.innerHTML = temp.innerHTML + message[index];
    index++;
    setTimeout(displayNextLetter, 30);
  } else {
    temp.removeAttribute("id");
    sendBtn.disabled = false;
    userInputArea.disabled = false;
  }
}
