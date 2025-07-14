function startVoiceChat() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "hi-IN";
  recognition.start();

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    document.getElementById("voice-response").innerText = "Thinking...";

    fetch("/voice-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: transcript })
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("voice-response").innerText = data.response;
        speakText(data.response); // 🔊 ElevenLabs voice
      });
  };
}

function speakText(text) {
  fetch("/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  })
    .then(res => res.blob())
    .then(blob => {
      const audio = document.getElementById("audio");
      audio.src = URL.createObjectURL(blob);
      audio.play();
    });
}
