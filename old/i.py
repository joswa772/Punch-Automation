import os
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load .env variables
load_dotenv()
URL = os.getenv("NORMAL_URL")
SERVER = os.getenv("SERVER")
EMPCODE = os.getenv("EMPCODE")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Setup screenshot folder
os.makedirs("screenshots", exist_ok=True)

def send_telegram_with_screenshot(msg, screenshot_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": msg}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"❗ Telegram error: {e}")

def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def punch_normal(force_punch_type=None):
    if datetime.today().weekday() == 6:
        print("📅 Today is Sunday. Skipping punch.")
        return

    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(URL)
        driver.maximize_window()
        print("🌐 Opened punch page.")
        time.sleep(10)

        wait.until(EC.presence_of_element_located((By.NAME, "DBServer"))).send_keys(SERVER)
        wait.until(EC.presence_of_element_located((By.NAME, "EmployeeCode"))).send_keys(EMPCODE)
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']"))).click()
        time.sleep(15)
        print("🔓 Logged in.")

        time.sleep(10) # Added extra sleep for page to fully load after login
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Master"))).click()
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Punch"))).click()
        time.sleep(5)

        now = datetime.now()
        punch_type = None

        if force_punch_type:
            punch_type = "Punch In" if force_punch_type.lower() == "in" else "Punch Out"
            print(f"🕒 Forced: {punch_type}")
        else:
            hour, minute = now.hour, now.minute
            if hour == 9 and 0 <= minute <= 5:
                punch_type = "Punch In"
            elif hour == 18 and 5 <= minute <= 10:
                punch_type = "Punch Out"

        if punch_type is None:
            msg = f"⏳ Not in punch window. Skipped on {now.strftime('%Y-%m-%d %H:%M')}"
            print(msg)
            screenshot = f"screenshots/normal_skipped_{now.strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot)
            send_telegram_with_screenshot(msg, screenshot)
            return

        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{punch_type}')]"))).click()
        except:
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@value='{punch_type}']"))).click()

        msg = f"✅ {punch_type} successful (NORMAL) on {now.strftime('%Y-%m-%d %H:%M')}"
        print(msg)
        screenshot = f"screenshots/normal_{punch_type.replace(' ', '_').lower()}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot)
        send_telegram_with_screenshot(msg, screenshot)
        logging.info(msg)

    except Exception as e:
        msg = f"❌ Normal Punch FAILED at {datetime.now().strftime('%Y-%m-%d %H:%M')}\nError: {e}"
        print(msg)
        logging.error(msg)
        screenshot = f"screenshots/normal_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot)
        send_telegram_with_screenshot(msg, screenshot)

    finally:
        driver.quit()
        print("🧹 Browser closed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run normal punch automation.")
    parser.add_argument("--force", type=str, choices=["in", "out"], help="Force punch type (in or out)")
    args = parser.parse_args()
    punch_normal(force_punch_type=args.force)