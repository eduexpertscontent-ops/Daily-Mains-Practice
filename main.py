import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import datetime

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

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

def handle_welcome():
    """Sends the Welcome Message if it's the very first run."""
    if not os.path.exists("initialized.txt"):
        welcome_text = (
            "📢 **Welcome to the Daily Mains Answer Writing Initiative!**\n\n"
            "Targeting **2026**, this channel will now host a structured daily answer writing program. "
            "Every **Monday to Thursday at 5:00 PM**, you will receive a high-quality Mains question and a model answer.\n\n"
            "🗓️ **Weekly Schedule:**\n"
            "• Mon: GS-1 | Tue: GS-2 | Wed: GS-3 | Thu: GS-4\n\n"
            "📝 **What each Model Answer includes:**\n"
            "✅ **Introduction**: Concise and context-driven.\n"
            "✅ **The Body**: Subheadings and bullet points.\n"
            "✅ **Value Addition**: Real-time Data, Case Studies, and Examples.\n"
            "✅ **Conclusion**: Forward-looking and balanced.\n\n"
            "**First question arrives now!**"
        )
        send_to_telegram(welcome_text)
        with open("initialized.txt", "w") as f:
            f.write("initialized")

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
    
    # Header format updated as requested
    header = (
        "📘 **Daily Mains Answer Writing Practice**\n"
        f"📅 **Date**: {date_str}\n"
        f"🌟 **Motivational quote**: \"{quote}\"\n"
        "--- --- --- --- --- --- --- ---\n\n"
    )

    system_role = "You are a Senior Faculty specializing in Mains Answer Writing."
    user_prompt = (
        f"Context: {topic_context}\nPaper: {gs_paper}\n\n"
        "Task: Create a Mains Question and Model Answer.\n"
        "STRICT RULES:\n"
        "1. NO TABLES. Use bullet points.\n"
        "2. DO NOT MENTION 'UPSC'.\n"
        "3. Use headers: **INTRODUCTION**, **BODY**, and **CONCLUSION**.\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[{"role": "system", "content": system_role}, {"role": "user", "content": user_prompt}]
    )
    
    return header + response.choices[0].message.content

if __name__ == "__main__":
    handle_welcome() # Checks and sends welcome if first run
    content = generate_daily_post()
    if content:
        send_to_telegram(content)
