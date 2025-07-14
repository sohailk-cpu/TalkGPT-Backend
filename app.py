from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import requests, os, uuid, datetime, json
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from io import BytesIO

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'super-secret-key'
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

users = {}
user_memory = {}

USERS_FILE = 'users.json'

# 🔄 Load saved users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)

# 🔐 User class
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# 🔹 Pages
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/voice')
def voice_page():
    return render_template('voice.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

# 🔹 Auth
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "error": "Missing username or password"})

    if username in users:
        return jsonify({"success": False, "error": "Username already exists"})

    users[username] = {"password": password}
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    return jsonify({"success": True})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users and users[username]['password'] == password:
        login_user(User(username))
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid credentials"})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# 🔹 History
@app.route('/history')
@login_required
def history():
    user_id = current_user.id
    history = user_memory.get(user_id, [])
    return render_template("history.html", history=history)

# 🔹 Chat (Text only)
@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '')
    user_id = current_user.id if current_user.is_authenticated else session.get('user_id') or str(uuid.uuid4())
    session['user_id'] = user_id
    reply = get_groq_response(user_msg, user_id)
    return jsonify({'response': reply})

# 🔹 Voice Chat (From mic)
@app.route('/voice-chat', methods=['POST'])
def voice_chat():
    user_msg = request.json.get('message', '')
    user_id = session.get('user_id') or str(uuid.uuid4())
    session['user_id'] = user_id
    reply = get_groq_response(user_msg, user_id)
    return jsonify({'response': reply})

# 🔹 AI Response
def get_groq_response(message, user_id):
    message = message.lower()

    if any(word in message for word in ["date", "day today", "aaj ka din", "aaj kya din", "today date", "what day today"]):
        now = datetime.datetime.now()
        return f"Aaj ka din hai: {now.strftime('%A, %d %B %Y')}"

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    memory = user_memory.get(user_id, [])
    memory.append({"role": "user", "content": message})

    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "system", "content": "You are TalkGPT, a helpful assistant created by Sohail."}] + memory[-5:]
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        result = res.json()
        if "choices" not in result:
            return "⚠️ AI response not received. Check your API key."
        content = result['choices'][0]['message']['content']
        memory.append({"role": "assistant", "content": content})
        user_memory[user_id] = memory
        return content
    except Exception as e:
        print("❌ Error:", e)
        return "Sorry, I couldn't connect to the AI service."

# 🔊 Voice Speak (ElevenLabs)
@app.route('/speak', methods=['POST'])
def speak():
    text = request.json.get("text", "")
    eleven_api_key = os.getenv("ELEVEN_API_KEY") or "sk-c3a9d12363dc718e73a610d853b3544c520be8c95c1adb67"
    voice_id = "LQqGm0gT4pft0DECaryn"

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": eleven_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.7
            }
        }

        res = requests.post(url, headers=headers, json=data)
        if res.status_code != 200:
            return jsonify({"error": "Voice generation failed"}), 500
        return send_file(BytesIO(res.content), mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔄 Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
