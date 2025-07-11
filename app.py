from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Optional if frontend is separate

OPENROUTER_API_KEY = "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"  # ← apni API key yahan daal

@app.route("/ask", methods=["POST"])
def ask():
    user_prompt = request.json.get("prompt", "")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openchat/openchat-3.5-1210",
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
