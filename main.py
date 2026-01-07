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

def get_next_ias_topic(gs_paper):
    """Scrapes Next IAS for the current day's news articles."""
    today_str = datetime.datetime.now().strftime("%d-%m-%Y")
    url = f"https://www.nextias.com/ca/current-affairs/{today_str}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Next IAS titles are usually in h2/h3 or specific containers
        # Adjust selector if site structure changes
        headlines = soup.find_all(['h2', 'h3'])
        topics = [h.get_text().strip() for h in headlines if len(h.get_text()) > 15]
        
        return ", ".join(topics[:3]) if topics else f"Latest {gs_paper} developments"
    except Exception as e:
        print(f"Scrape error: {e}")
        return f"Recent issues in {gs_paper}"

def generate_upsc_content():
    day = datetime.datetime.now().strftime("%A")
    schedule = {
        "Monday": "GS-1 (History, Geography, Indian Society)",
        "Tuesday": "GS-2 (Polity, Governance, International Relations)",
        "Wednesday": "GS-3 (Economy, S&T, Environment, Security)",
        "Thursday": "GS-4 (Ethics, Integrity, Aptitude)"
    }
    gs_paper = schedule.get(day)
    if not gs_paper: return None

    topic_context = get_next_ias_topic(gs_paper)
    
    # Logic for GS-4 Case Studies vs GS 1-3 direct questions
    system_role = "You are a UPSC Senior Faculty and Subject Matter Expert."
    user_prompt = f"""
    Context: {topic_context}
    Paper: {gs_paper}

    Task:
    1. Create one UPSC Mains Question (150-250 words).
    2. Provide a detailed Model Answer with these headers:
       - **INTRODUCTION**
       - **BODY** (Use subheadings and bullet points. Include relevant DATA, CASE STUDIES, or GOVT SCHEMES)
       - **CONCLUSION** (Way forward)

    STRICT RULES:
    - NO TABLES. Use bullet points for comparisons.
    - For GS-4, always frame it as an ethical case study or a value-based question.
    - Format for Telegram (use **Bold** for headers).
    """

    response = client.chat.completions.create(
        model="gpt-4o", # Or "gpt-4-turbo" / "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            requests.post(url, json={"chat_id": CHAT_ID, "text": text[i:i+4000], "parse_mode": "Markdown"})
    else:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    content = generate_upsc_content()
    if content:
        send_to_telegram(content)
