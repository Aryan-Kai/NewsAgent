from google import genai
from dotenv import find_dotenv,load_dotenv
import os
from firecrawl import Firecrawl
import json
import datetime

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
fc = Firecrawl(api_key=FIRECRAWL_API_KEY)


TARGET_SITES = [
    "https://android-developers.googleblog.com/",
    "https://developer.android.com/news",
    "https://blog.google/products-and-platforms/platforms/android/"
]

STATE_FILE = "last_run.json"

def get_last_run_time():
     if os.path.exists(STATE_FILE):
           with open(STATE_FILE,"r") as f:
                  return json.load(f).get("timestamp")
     return "2026-03-20T00:00:00" #Defaulting to yesterday for now

def run_scout():
    last_run = get_last_run_time()
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"Agent starting----> Last run was: {last_run}")
    all_news_content = ""

    for url in TARGET_SITES:
        print(f"Scanning : {url}")
        results = fc.scrape(url,formats=["markdown","changeTracking"],only_main_content=True)

        status = results.change_tracking["changeStatus"]
        # if status in ["new","changed"]:
        all_news_content += f"\n--- SOURCE: {url} ---\n{results.markdown}\n"
        # else:
            # print(f"No new updates from: {url}")
    
    if not all_news_content:
         print("No new content posted today....")
         return
    
    prompt = f""" You are a professional tech curator. Today is {today}.
    I am giving you markdown content from several websites.
    
    TASK:
    1. Identify only the news,papers or posts published since {last_run}.
    2. For each relevant item, provide:
        - Title
        - Direct Link
        - A 1-sentence 'Why it matters' summary.
        
    If nothing is new,simply say 'No relevant updates'.
    
    CONTENT:
    {all_news_content}"""
    
    response = client.models.generate_content(model="gemini-2.5-flash",contents=prompt)

    newsletter_draft = response.text
    print(newsletter_draft)

if __name__ == "__main__":
     run_scout()