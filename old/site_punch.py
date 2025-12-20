import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


load_dotenv()

URL = os.getenv("SITE_URL")
SERVER = os.getenv("SERVER")
EMPCODE = os.getenv("EMPCODE")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SCREENSHOT_DIR = "screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def send_telegram_with_screenshot(msg, screenshot_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": msg}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"❗ Telegram error: {e}")

def punch_site():
    firefox_options = Options()
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--disable-gpu')
    firefox_options.add_argument('--no-sandbox')
    firefox_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Firefox(service=Service(executable_path=GeckoDriverManager().install(), service_args=['--connect-timeout', '60']), options=firefox_options)
    wait = WebDriverWait(driver, 40)

    try:
        driver.get(URL)
        print("🌐 Opened login page.")
        time.sleep(10)

        driver.find_element(By.NAME, "dbname").clear()
        driver.find_element(By.NAME, "dbname").send_keys(SERVER)
        driver.find_element(By.NAME, "userName").clear()
        driver.find_element(By.NAME, "userName").send_keys(EMPCODE)
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(text(),'LOGIN')]").click()

        wait.until(EC.url_changes(URL))
        time.sleep(15)

        driver.find_element(By.XPATH, "//li[@id='modules']").click()
        time.sleep(3)

        wait.until(EC.presence_of_element_located((By.ID, "dynmodule")))
        hrms_li = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='dynmodule']//li[@id='modules_0']")))
        driver.execute_script("arguments[0].click();", hrms_li)
        time.sleep(5)

        wait.until(EC.presence_of_element_located((By.ID, "searchcommonoverall")))
        time.sleep(2)

        driver.execute_script("arguments[0].click();", wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[span[normalize-space(text())='Transaction']]")
        )))

        time.sleep(2)

        driver.execute_script("arguments[0].click();", wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[normalize-space(text())='Attendance']")
        )))

        time.sleep(2)

        driver.execute_script("arguments[0].click();", wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[normalize-space(text())='Site Punch In Out']")
        )))

        time.sleep(3)

        wait.until(EC.element_to_be_clickable((By.ID, "s2id_SiteId"))).click()
        time.sleep(1)

        driver.find_element(By.XPATH, "//div[@id='select2-drop']//input").send_keys("CAI Mahindra")
        time.sleep(2)

        cai_div = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[@class='select2-result-label']//td[contains(text(), 'CAI Mahindra')]/ancestor::div[@class='select2-result-label']"
        )))
        driver.execute_script("arguments[0].click();", cai_div)
        time.sleep(2)

        now = datetime.now()
        hour, minute = now.hour, now.minute
        punch_type = None

        if hour == 9 and 0 <= minute <= 5:
            punch_type = "Punch In"
        elif hour == 18 and 5 <= minute <= 10:
            punch_type = "Punch Out"

        if punch_type:
            punch_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[contains(text(), '{punch_type}')]")
            ))
            punch_button.click()
            time.sleep(2)

            ss_path = os.path.join(SCREENSHOT_DIR, f"site_{punch_type.replace(' ', '_').lower()}_{now.strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(ss_path)

            msg = f"✅ {punch_type} successful on {now.strftime('%Y-%m-%d %H:%M')}"
            print(msg)
            send_telegram_with_screenshot(msg, ss_path)
        else:
            ss_path = os.path.join(SCREENSHOT_DIR, f"site_skipped_{now.strftime('%Y%m%d_%H%M%S')}.png")
            driver.save_screenshot(ss_path)
            msg = f"⏳ Site punch Time is not within Period. Skipped on {now.strftime('%Y-%m-%d %H:%M')}"
            print(msg)
            send_telegram_with_screenshot(msg, ss_path)

    except Exception as e:
        ss_path = os.path.join(SCREENSHOT_DIR, f"site_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        driver.save_screenshot(ss_path)
        msg = f"❌ Punch FAILED at {datetime.now().strftime('%Y-%m-%d %H:%M')}\nError: {e}"
        print(msg)
        send_telegram_with_screenshot(msg, ss_path)

    finally:
        driver.quit()
        print("🧹 Browser closed.")

if __name__ == "__main__":
    punch_site()
