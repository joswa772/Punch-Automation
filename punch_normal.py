import os
from sys import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
import time
from datetime import datetime
import logging
import tempfile
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import requests
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager

load_dotenv()

# Debug: Check if .env file is being loaded
print("🔍 Debug: Checking environment variables...")
print(f"SERVER from env: {os.getenv('SERVER')}")
print(f"EMPCODE from env: {os.getenv('EMPCODE')}")
print(f"PASSWORD from env: {os.getenv('PASSWORD')}")

URL = os.getenv("NORMAL_URL")
SERVER = os.getenv("SERVER")
EMPCODE = os.getenv("EMPCODE")
PASSWORD = os.getenv("PASSWORD")


# Load Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_with_screenshot(msg, screenshot_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": msg}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"❗ Telegram error: {e}")


# Check if environment variables are loaded
if not all([URL, SERVER, EMPCODE, PASSWORD]):
    missing_vars = []
    if not URL: missing_vars.append("NORMAL_URL")
    if not SERVER: missing_vars.append("SERVER")
    if not EMPCODE: missing_vars.append("EMPCODE")
    if not PASSWORD: missing_vars.append("PASSWORD")
    
    print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file")
    exit(1)

print(f"✅ Environment variables loaded successfully")
print(f"URL: {URL}")
print(f"Server: {SERVER}")
print(f"User Code (EMPCODE): {EMPCODE}")
print(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}")
print(f"SITE_URL: {os.getenv('SITE_URL')}")

# Create logs and screenshots directories if they don't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

log_file = f"logs/punch_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
logging.basicConfig(filename='logs/punch_log.txt', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

logging.info("Punch process started.")

logging.info("Login successful")
logging.info("Clicked Punch In")
logging.info("Punch process completed.")


if datetime.now().weekday() == 6:
    print("Today is Sunday. Skipping punch.")
    exit()

def debug_page_elements(driver):
    """Debug function to help identify form elements on the page"""
    print("🔍 Debugging page elements...")
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")
    
    # Look for ALL input fields
    print("\n📝 ALL INPUT FIELDS FOUND:")
    try:
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, elem in enumerate(all_inputs):
            name_attr = elem.get_attribute('name') or 'NO_NAME'
            id_attr = elem.get_attribute('id') or 'NO_ID'
            type_attr = elem.get_attribute('type') or 'NO_TYPE'
            placeholder_attr = elem.get_attribute('placeholder') or 'NO_PLACEHOLDER'
            print(f"   Input {i+1}: name='{name_attr}', id='{id_attr}', type='{type_attr}', placeholder='{placeholder_attr}'")
    except Exception as e:
        print(f"❌ Error finding all inputs: {e}")
    
    # Look for common form field selectors
    print("\n🎯 SPECIFIC SELECTORS:")
    selectors_to_try = [
        "input[name='server']", "input[id='server']", "input[placeholder*='server']",
        "input[name='user']", "input[name='usercode']", "input[name='email']", "input[name='mobile']",
        "input[id='user']", "input[id='usercode']", "input[id='email']", "input[id='mobile']",
        "input[placeholder*='User Code']", "input[placeholder*='User Mobile']", "input[placeholder*='User Email']",
        "input[name='password']", "input[type='password']", "input[id='password']"
    ]
    
    for selector in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"✅ Found {len(elements)} element(s) with selector: {selector}")
                for i, elem in enumerate(elements):
                    print(f"   Element {i+1}: name='{elem.get_attribute('name')}', id='{elem.get_attribute('id')}', type='{elem.get_attribute('type')}'")
        except Exception as e:
            print(f"❌ Error with selector {selector}: {e}")
    
    # Look for buttons
    print("\n🔘 ALL BUTTONS FOUND:")
    button_selectors = ["button", "input[type='submit']", "input[type='button']"]
    for selector in button_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"✅ Found {len(elements)} button(s) with selector: {selector}")
                for i, elem in enumerate(elements):
                    print(f"   Button {i+1}: text='{elem.text}', value='{elem.get_attribute('value')}', type='{elem.get_attribute('type')}'")
        except Exception as e:
            print(f"❌ Error with button selector {selector}: {e}")

def punch_normal(force_punch_type=None):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options
    )
    driver.get(URL)
    driver.maximize_window()
    logging.info('Started punch automation and opened URL.')


    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    wait = WebDriverWait(driver, 30)

    try:
        # --- Login Section ---
        server_field = wait.until(EC.presence_of_element_located((By.NAME, "DBServer")))
        print("✅ Found server field (DBServer)")
        server_field.clear()
        time.sleep(1)
        server_field.send_keys(SERVER)
        print(f"   Entered server value: {SERVER}")

        user_field = wait.until(EC.presence_of_element_located((By.NAME, "EmployeeCode")))
        print("✅ Found user field (EmployeeCode)")
        user_field.clear()
        time.sleep(1)
        user_field.send_keys(EMPCODE)
        print(f"   Entered employee code: {EMPCODE}")
        
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        print("✅ Found password field (Password)")
        password_field.clear()
        time.sleep(1)
        password_field.send_keys(PASSWORD)
        print("   Entered password.")

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
        print("✅ Found Login button, clicking...")
        login_button.click()
        print("⏳ Waiting for page to load after login...")
        time.sleep(8)
        print(f"Current URL after login attempt: {driver.current_url}")
        print(f"Current page title after login attempt: {driver.title}")

        try:
            master_menu = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Master")))
            print("✅ Found 'Master' menu, clicking...")
            master_menu.click()
            time.sleep(3)
            print(f"Current URL after clicking Master: {driver.current_url}")
            print(f"Current page title after clicking Master: {driver.title}")

            punch_submenu = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Punch")))
            print("✅ Found 'Punch' submenu, clicking...")
            punch_submenu.click()
            time.sleep(5)
            print(f"Current URL after clicking Punch: {driver.current_url}")
            print(f"Current page title after clicking Punch: {driver.title}")

        except Exception as e:
            print(f"❌ Error navigating to Master -> Punch: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"screenshots/navigation_error_{timestamp}.png")
            driver.quit()
            return

        punch_type = None

        if force_punch_type:
            if force_punch_type.lower() == "in":
                punch_type = "Punch In"
                print("🕒 Forcing Punch In due to 'force_punch_type' parameter.")
            elif force_punch_type.lower() == "out":
                punch_type = "Punch Out"
                print("🕒 Forcing Punch Out due to 'force_punch_type' parameter.")
            else:
                print(f"⚠️ Invalid 'force_punch_type' provided: {force_punch_type}. Proceeding with time-based check.")
        
        if not punch_type:
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            current_time = f"{current_hour:02d}:{current_minute:02d}"
            print(f"🕐 Current time: {current_time}")

            if (current_hour == 8 and current_minute >= 55) or (current_hour == 9 and current_minute <= 5):
                punch_type = "Punch In"
                print(f"🕐 Time is {current_time} - Within Punch In window")
            elif current_hour == 18 and 0 <= current_minute <= 30:
                punch_type = "Punch Out"    
                print(f"🕐 Time is {current_time} - Within Punch Out window")

        if punch_type is None:
            msg = f"⏳Normal punch Time is not within Period. Skipping punch on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            print(msg)
            screenshot = f"screenshots/normal_skipped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot)
            send_telegram_with_screenshot(msg, screenshot)
            driver.quit()
            return
        
        # --- Modified Punch Button & Screenshot Section ---
        try:
            punch_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{punch_type}')]")
            punch_button.click()
            print(f"✅ {punch_type} button clicked")

            try:
                wait.until(
                    EC.any_of(
                        EC.invisibility_of_element(punch_button),
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'toast') or contains(text(), 'success')]"))
                    )
                )
            except:
                print("⚠️ No confirmation change detected, continuing anyway.")

        except:
            try:
                punch_button = driver.find_element(By.XPATH, f"//input[@value='{punch_type}']")
                punch_button.click()
                print(f"✅ {punch_type} input button clicked")
                try:
                    wait.until(EC.invisibility_of_element(punch_button))
                except:
                    print("⚠️ No confirmation change detected, continuing anyway.")
            except:
                print(f"❌ Could not find {punch_type} button")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                driver.save_screenshot(f"screenshots/punch_button_error_{timestamp}.png")
                driver.quit()
                raise

        time.sleep(2)  # Small buffer to ensure UI updates
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = f"screenshots/normal_{punch_type.replace(' ', '_').lower()}_{timestamp}.png"
        driver.save_screenshot(screenshot)
        print(f"📸 Screenshot saved: {screenshot}")
        logging.info(f"Successful {punch_type} for normal punch. Screenshot saved.")
        msg = f"✅ NORMAL {punch_type} successful  on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_telegram_with_screenshot(msg, screenshot)

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"screenshots/error_{timestamp}.png")
        msg = f"❌ Normal Punch FAILED at {datetime.now().strftime('%Y-%m-%d %H:%M')}\nError: {str(e)}"
        send_telegram_with_screenshot(msg, screenshot)
    finally:
        driver.quit()
        logging.info('Browser closed.')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run normal punch automation.")
    parser.add_argument("--force", type=str, choices=["in", "out"], help="Force punch type (in or out) ignoring time windows.")
    args = parser.parse_args()
    
    punch_normal(force_punch_type=args.force)
