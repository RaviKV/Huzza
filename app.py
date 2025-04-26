import subprocess
import sys

def install_and_import(package, module=None):
    try:
        if module:
            __import__(module)
        else:
            __import__(package)
    except ImportError:
        print(f"Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Required packages
required_packages = [
    ("fastapi", None),
    ("uvicorn", None),
    ("jinja2", None),
    ("python-multipart", None),
    ("playwright", None)
]

for pkg, mod in required_packages:
    install_and_import(pkg, mod or pkg)

# Special case: install browsers for Playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright
    
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
async def scan(request: Request, platform: str = Form(...), username: str = Form(...), password: str = Form(...)):
    # Start Playwright session
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless browser
        context = browser.new_context()
        page = context.new_page()

        result = {}

        if platform.lower() == "facebook":
            page.goto("https://www.facebook.com/login")
            page.fill('input[name="email"]', username)
            page.fill('input[name="pass"]', password)
            page.click('button[name="login"]')
            page.wait_for_timeout(5000)

            # After login, navigate to privacy checkup
            try:
                page.goto("https://www.facebook.com/privacy/checkup/")
                page.wait_for_timeout(3000)

                # Quick basic checks: (expand later for full checks)
                public_posts = "Public" in page.content()
                profile_visibility = "Friends" in page.content()

                score = 10
                if public_posts:
                    score -= 5
                if not profile_visibility:
                    score -= 3

                color = "Green" if score >= 8 else "Amber" if score >=5 else "Red"

                analysis = f"Privacy Score: {score}/10 ({color}) based on your Facebook settings."

                recommendations = []
                if public_posts:
                    recommendations.append("Change post visibility to 'Friends Only'.")
                if not profile_visibility:
                    recommendations.append("Review your profile privacy settings.")

                if score == 10:
                    recommendations.append("Your settings are strong. Keep monitoring.")

                result = {
                    "score": score,
                    "color": color,
                    "analysis": analysis,
                    "recommendations": recommendations
                }

            except Exception as e:
                result = {
                    "error": str(e),
                    "message": "Could not access privacy settings. Please check manually."
                }

            context.close()
            browser.close()

        else:
            result = {"error": "Instagram support coming soon!"}

    return templates.TemplateResponse("form.html", {"request": request, "result": result})

