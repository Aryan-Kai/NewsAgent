from google import genai
from dotenv import find_dotenv,load_dotenv
import os
from firecrawl import Firecrawl
import json
import datetime
import resend

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
resend.api_key = os.getenv("RESEND_API_KEY")

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
    return newsletter_draft

def send_newsletter_email(newsletter_markdown):
     """

     Sends the drafted newsletter as clean HTML email.
     """

     html_body = f"""
     <html>
     <body style="font-family: sans-serif;line-height:1.6;color:#333;max-width:600px;margin:auto;">
     <h2 style="color:#007bff;">Your AI Tech Scout Update</h2>
     <p style="color:#666;">Generated on {datetime.datetime.now().strftime("%B %d, %Y, %I:%M %p")}</p>
     <hr style="border:0;border-top:1px solid #eee;"/>
     <div style="white-space:pre-wrap;">
     {newsletter_markdown}
     </div>
     <footer style="margin-top:20px;font-size:12px;color:#999;">
     Sent by your AI Agent
     </footer>
     </body>
     </html>
     """

     try:
          params = {
               "from":"onboarding@resend.dev",
               "to":[os.getenv("MY_EMAIL")],
               "subject":f"AI Newsletter: {len(newsletter_markdown.splitlines())}",
               "html":html_body
          }

          email = resend.Emails.send(params)
          print(f"Email sent successfully. ID:{email['id']}")
          return True
     except Exception as e:
          print(f"Failed to send Email. {e}")
          return False

if __name__ == "__main__":
     raw_content = run_scout()
     prompt = f"Create a professional newsletter from this content: {raw_content}"

     newsletter_text = client.models.generate_content(
          model="gemini-2.5-flash",
          contents=prompt
     ).text

     send_newsletter_email(newsletter_text)