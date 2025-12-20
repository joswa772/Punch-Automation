import os
import platform
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service

# Load .env variables
load_dotenv()
URL = os.getenv("SITE_URL")
SERVER = os.getenv("SERVER")
EMPCODE = os.getenv("EMPCODE")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(filename='logs/punch_log.txt', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def send_telegram_with_screenshot(msg, screenshot_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": msg}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"❗ Telegram error: {e}")


if datetime.now().weekday() == 6:
    print("Today is Sunday. Skipping punch.")
    exit()


def punch_site(force_punch_type=None):
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
    wait = WebDriverWait(driver, 30)

    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    try:
        driver.get(URL)
        print("🌐 Opened login page.")
        time.sleep(5)

        driver.find_element(By.NAME, "dbname").clear()
        driver.find_element(By.NAME, "dbname").send_keys(SERVER)
        driver.find_element(By.NAME, "userName").clear()
        driver.find_element(By.NAME, "userName").send_keys(EMPCODE)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        driver.find_element(By.XPATH, "//button[contains(text(),'LOGIN')]").click()
        print("🔓 Login submitted.")
        wait.until(EC.url_changes(URL))
        print("✅ Login successful. URL changed.")
        time.sleep(20)

        grid_icon = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@id='modules']")))
        grid_icon.click()
        print("🧭 Clicked grid/menu launcher.")
        time.sleep(2)

        wait.until(EC.presence_of_element_located((By.ID, "dynmodule")))
        hrms_li = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='dynmodule']//li[@id='modules_0']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", hrms_li)
        time.sleep(1)
        hrms_li.click()
        print("📂 Clicked HRMS module.")
        time.sleep(2)

        transaction = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[span[normalize-space(text())='Transaction']]")
        ))
        transaction.click()
        print("📂 Clicked Transaction")
        time.sleep(2)

        attendance = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[normalize-space(text())='Attendance']")
        ))
        attendance.click()
        print("🕑 Clicked Attendance")
        time.sleep(2)

        punch_in_out = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[normalize-space(text())='Site Punch In Out']")
        ))
        punch_in_out.click()
        print("📌 Clicked Site Punch In Out")
        time.sleep(2)

        # --- Select CAI Mahindra ---
        site_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "s2id_SiteId")))
        site_dropdown.click()
        print("📍 Site dropdown clicked")
        time.sleep(1)

        search_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='select2-drop']//input")))
        search_box.clear()
        search_box.send_keys("CAI Mahindra")
        print("⌨️ Typed 'CAI Mahindra' in search box")
        time.sleep(1)

        cai_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'select2-result-label')]//td[contains(text(), 'CAI Mahindra')]")))
        cai_option.click()
        print("🏢 Selected CAI Mahindra site")
        time.sleep(1)

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
            msg = f"⏳ Site punch Time is not within Period. Skipping punch on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            print(msg)
            screenshot = f"screenshots/site_skipped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot)
            send_telegram_with_screenshot(msg, screenshot)
            driver.quit()
            return

        # --- Punch Button Handling ---
        try:
            if punch_type == "Punch In":
                punch_button = wait.until(EC.presence_of_element_located((By.ID, "PunchInBTN")))
            else:
                punch_button = wait.until(EC.presence_of_element_located((By.ID, "PunchOutBTN")))

            # ✅ Check if button is enabled
            if punch_button.is_enabled():
                punch_button.click()
                print(f"✅ {punch_type} button clicked")

                # Wait for confirmation (toast or button state change)
                try:
                    wait.until(
                        EC.any_of(
                            EC.invisibility_of_element(punch_button),
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'toast') or contains(text(), 'success')]"))
                        )
                    )
                except:
                    print("⚠️ No confirmation detected, continuing anyway.")

            else:
                print(f"⚠️ {punch_type} button is disabled. Skipping.")
                msg = f"⚠️ {punch_type} button is disabled on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                screenshot = f"screenshots/disabled_{punch_type.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot)
                send_telegram_with_screenshot(msg, screenshot)
                return

        except Exception as e:
            print(f"❌ Could not interact with {punch_type} button: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"screenshots/punch_button_error_{timestamp}.png")
            driver.quit()
            raise

        time.sleep(2)  # Small buffer to ensure UI updates
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = f"screenshots/site_{punch_type.replace(' ', '_').lower()}_{timestamp}.png"
        driver.save_screenshot(screenshot)
        print(f"📸 Screenshot saved: {screenshot}")
        logging.info(f"Successful {punch_type} for Site Punch. Screenshot saved.")
        msg = f"✅ Site {punch_type} successful on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_telegram_with_screenshot(msg, screenshot)

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"screenshots/error_{timestamp}.png")
        msg = f"❌ Site Punch FAILED at {datetime.now().strftime('%Y-%m-%d %H:%M')}\nError: {str(e)}"
        send_telegram_with_screenshot(msg, screenshot)
    finally:
        driver.quit()
        logging.info('Browser closed.')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run normal punch automation.")
    parser.add_argument("--force", type=str, choices=["in", "out"], help="Force punch type (in or out) ignoring time windows.")
    args = parser.parse_args()

    punch_site(force_punch_type=args.force)
