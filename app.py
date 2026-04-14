from dotenv import load_dotenv
import os
import sqlite3
import json
import pandas as pd
import re
from datetime import datetime, timedelta
from openai import OpenAI
import sounddevice as sd
from scipy.io.wavfile import write
import pyttsx3

# ---------- LOAD ENV ----------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- TTS ----------
engine = pyttsx3.init()

def speak(text):
    print("\n🔊", text)
    engine.say(text)
    engine.runAndWait()

# ---------- INR FORMAT ----------
def format_inr(amount):
    return f"₹{amount:,.0f}"

# ---------- RECORD AUDIO ----------
def record_audio(filename="input.wav", duration=5, fs=44100):
    print("\n🎤 Speak your command...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, audio)

# ---------- SPEECH TO TEXT ----------
def speech_to_text():
    record_audio()
    with open("input.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )
    print("📝 You said:", transcript.text)
    return transcript.text.lower()

# ---------- DB SETUP ----------
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    amount INTEGER,
    category TEXT,
    date TEXT
)
""")
conn.commit()

# ---------- INTRO ----------
speak("Hi, I am Hanks, your AI financial assistant. Tell me your expense or ask for a report.")

# ---------- GET COMMAND ----------
user_input = speech_to_text()


# ===================== REPORT =========================

if "report" in user_input:

    df = pd.read_sql_query("SELECT * FROM expenses", conn)

    if df.empty:
        speak("No data available yet")

    else:
        df["date"] = pd.to_datetime(df["date"])
        today = datetime.today().date()

        if "today" in user_input:
            df = df[df["date"].dt.date == today]

        elif "week" in user_input:
            week_ago = today - timedelta(days=7)
            df = df[df["date"].dt.date >= week_ago]

        elif "month" in user_input:
            month_ago = today - timedelta(days=30)
            df = df[df["date"].dt.date >= month_ago]

        if df.empty:
            speak("No data for selected period")

        else:
            total = df["amount"].sum()
            by_category = df.groupby("category")["amount"].sum().to_dict()

            formatted_total = format_inr(total)

            report = f"Total spending is {formatted_total}. "

            if by_category:
                top_cat = max(by_category, key=by_category.get)
                report += f"Highest spending is on {top_cat}. "

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Give short financial insights and saving advice in Indian Rupees."
                    },
                    {"role": "user", "content": report}
                ]
            )

            speak(response.choices[0].message.content)

# ================= ADD EXPENSE ========================

else:

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Extract amount, category (Food, Transport, Shopping, Bills, Other), and date (YYYY-MM-DD). Return ONLY JSON."
            },
            {"role": "user", "content": user_input}
        ]
    )

    data = response.choices[0].message.content

    try:
        cleaned = re.sub(r"```json|```", "", data).strip()
        parsed = json.loads(cleaned)

        parsed["category"] = parsed["category"].capitalize()

        cursor.execute(
            "INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
            (parsed["amount"], parsed["category"], parsed["date"])
        )
        conn.commit()

        speak(f"Added ₹{parsed['amount']} for {parsed['category']}")

    except Exception as e:
        print("❌ Error:", data)
        speak("Sorry, I could not understand that")

# ---------- CLOSE DB ----------
conn.close()