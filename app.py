# app.py (نسخة محدثة بقاعدة بيانات SQLite)
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import sqlite3

app = Flask(__name__)
CORS(app)
openai.api_key = "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"
DB_NAME = "alahmdy_ai.db"
COST_PER_REQUEST = 5

# ---------- أدوات قاعدة البيانات ----------
def get_db():
    return sqlite3.connect(DB_NAME)


def get_user(username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT credits FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def update_credits(username, new_credits):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET credits=? WHERE username=?", (new_credits, username))
    conn.commit()
    conn.close()


def log_usage(username, action, cost):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO usage_logs (username, action, cost) VALUES (?, ?, ?)",
        (username, action, cost)
    )
    conn.commit()
    conn.close()

# ---------- الذكاء الاصطناعي ----------
def generate_content(topic, content_type, tone):
    prompt = f"""
    اكتب {content_type} باللغة العربية
    الموضوع: {topic}
    النبرة: {tone}
    يكون النص مناسب للسوق المصري وبأسلوب واضح وجذاب.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

# ---------- API ----------
@app.route("/api/write", methods=["POST"])
def write_ai():
    data = request.json
    username = data.get("user")

    user = get_user(username)
    if not user:
        return jsonify({"error": "المستخدم غير موجود"}), 404

    credits = user[0]
    if credits < COST_PER_REQUEST:
        return jsonify({"error": "الرصيد غير كافٍ"}), 403

    result = generate_content(
        data.get("topic"),
        data.get("content_type"),
        data.get("tone")
    )

    update_credits(username, credits - COST_PER_REQUEST)
    log_usage(username, "write", COST_PER_REQUEST)

    return jsonify({
        "result": result,
        "remaining_credits": credits - COST_PER_REQUEST
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
