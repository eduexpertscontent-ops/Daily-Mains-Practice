import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import datetime
import sys

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 2026 Flagship Reasoning Model
OPENAI_MODEL = "gpt-5.2" 
client = OpenAI(api_key=OPENAI_API_KEY)

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            requests.post(url, json={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"})
    else:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def get_motivational_quote():
    quotes = [
        "The future depends on what you do today. – Mahatma Gandhi",
        "Success is the sum of small efforts, repeated day-in and day-out. – Robert Collier",
        "It always seems impossible until it's done. – Nelson Mandela",
        "Arise, awake, and stop not till the goal is reached. – Swami Vivekananda"
    ]
    return quotes[datetime.datetime.now().day % len(quotes)]

def get_next_ias_topic(gs_paper):
    today_str = datetime.datetime.now().strftime("%d-%m-%Y")
    url = f"https://www.nextias.com/ca/headlines-of-the-day/{today_str}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = soup.find_all(['h2', 'h3', 'td']) 
        topics = [h.get_text().strip() for h in headlines if len(h.get_text()) > 20]
        return ", ".join(topics[:3]) if topics else f"Latest {gs_paper} developments"
    except:
        return f"Recent issues in {gs_paper}"

def generate_daily_post():
    now = datetime.datetime.now()
    day = now.strftime("%A")
    date_str = now.strftime("%d %B %Y")
    
    schedule_map = {
        "Monday": "GS-1 (History / Geography / Society)",
        "Tuesday": "GS-2 (Polity / Governance / IR)",
        "Wednesday": "GS-3 (Economy / S&T / Environment / DM / Security)",
        "Thursday": "GS-4 (Ethics)"
    }
    gs_paper = schedule_map.get(day)
    if not gs_paper: return None

    topic_context = get_next_ias_topic(gs_paper)
    quote = get_motivational_quote()
    
    header = (
        "📘 **Daily Mains Answer Writing Practice**\n"
        f"📅 **Date**: {date_str}\n"
        f"🌟 **Motivational quote**: \"{quote}\"\n"
        "--- --- --- --- --- --- --- ---\n\n"
    )

    log(f"Generating Expert Mains Content using {OPENAI_MODEL}...")

    try:
        # UPDATED: Using the modern Responses API with reasoning effort control
        response = client.responses.create(
            model=OPENAI_MODEL,
            reasoning={"effort": "high"}, # High effort for PhD-level exam content
            input=[
                {
                    "role": "user", 
                    "content": (
                        f"Context: {topic_context}\nPaper: {gs_paper}\n\n"
                        "Task: Generate a 250-word Model Answer.\n"
                        "STRICT RULES:\n"
                        "- NO TABLES. Use bullet points.\n"
                        "- Highlight keywords in **bold**.\n"
                        "- Use sections: **QUESTION**, **INTRODUCTION**, **BODY**, and **CONCLUSION**.\n"
                        "- Justify with Real-world examples and recent data."
                    )
                }
            ]
        )
        
        # Responses API uses .output_text to access the final generated text
        return header + response.output_text

    except Exception as e:
        log(f"Error during generation: {e}")
        return None

if __name__ == "__main__":
    content = generate_daily_post()
    if content:
        send_to_telegram(content)
        log("Mains post sent successfully.")
