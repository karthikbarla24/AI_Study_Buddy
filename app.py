from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import sqlite3
import os
from datetime import datetime

load_dotenv()
app = Flask(__name__)

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            topic TEXT,
            score INTEGER,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/explain", methods=["POST"])
def explain():
    try:
        data = request.get_json()
        topic = data.get("topic", "")
        lang = data.get("language", "English")

        prompt = (
            f"Act as a professional tutor. Explain '{topic}' in simple {lang} language. "
            f"You MUST write the entire explanation in {lang}. "
            "Do not use asterisks (*). Use clear headings followed by a colon. "
            "Use short bullet points and include one real-life example."
        )

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return jsonify({"response": chat_completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"System Error: {str(e)}"})

@app.route("/questions", methods=["POST"])
def questions():
    try:
        data = request.get_json()
        topic = data.get("topic", "")
        lang = data.get("language", "English")

        # Forces exactly 20 TECHNICAL questions about the user's topic
        prompt = (
            f"Generate exactly 20 most important technical exam questions about '{topic}' in {lang}. "
            f"You MUST write both questions and answers in {lang}. "
            "Format your response exactly like this: "
            "Questions: [List all 20 technical questions here] "
            "||| "
            "Answers: [List all 20 corresponding technical answers here]"
        )

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        return jsonify({"response": chat_completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"System Error: {str(e)}"})
@app.route("/save", methods=["POST"])
def save():
    try:
        data = request.get_json()
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO progress (student_name, topic, score, date) VALUES (?, ?, ?, ?)", 
                 (data.get("name"), data.get("topic"), 100, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return jsonify({"message": "Progress Saved Successfully!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/progress/<name>")
def progress(name):
    try:
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT topic, score, date FROM progress WHERE student_name=?", (name,)).fetchall()
        conn.close()
        
        return jsonify({"progress": [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({"progress": [], "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)