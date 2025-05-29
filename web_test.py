"""
web_test.py – Functional tests for SauceDemo using Selenium 4.

Flows
-----
1. Positive checkout (happy path)  → expect order completion.
2. Negative checkout (missing first name) → expect validation error.

Outputs
-------
* PNG screenshots saved in screenshots/<name>_<timestamp>.png
* demo.gif auto-generated from those PNGs (requires imageio)

Run
---
python web_test.py
"""

import os
import time
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.saucedemo.com"
USER, PW = "standard_user", "secret_sauce"
SHOT_DIR = Path("screenshots")
SHOT_DIR.mkdir(exist_ok=True)
CURRENT_SHOTS: list[Path] = []   # screenshots created in this run


# ---------------- helpers ------------------------------------------------ #
def ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def snap(driver: webdriver.Chrome, label: str) -> None:
    """Save a screenshot and print its path."""
    fname = SHOT_DIR / f"{label}_{ts()}.png"
    driver.save_screenshot(str(fname))
    CURRENT_SHOTS.append(fname)
    print(f"[✓] Screenshot saved → {fname}")


# ---------------- base fixture ------------------------------------------- #
class BaseTest(unittest.TestCase):
    """Shared driver setup, teardown, and common steps."""

    def setUp(self):
        opts = webdriver.ChromeOptions()

        # Disable every password-manager / leak-detection UI
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        }
        opts.add_experimental_option("prefs", prefs)
        opts.add_argument(
            "--disable-features="
            "PasswordManagerEnableNotificationUI,"
            "PasswordLeakDetection,AutofillAssistant"
        )
        opts.add_argument("--incognito")  # Incognito = password manager OFF

        if os.getenv("CI"):  # headless on GitHub Actions
            opts.add_argument("--headless=new")

        self.driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=opts,
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    # ------------ reusable steps ---------------- #
    def login(self):
        d = self.driver
        d.get(BASE_URL)
        d.find_element(By.ID, "user-name").send_keys(USER)
        d.find_element(By.ID, "password").send_keys(PW)
        d.find_element(By.ID, "login-button").click()
        self.wait.until(EC.title_contains("Swag Labs"))

    def add_items(self, n: int = 1):
        for btn in self.driver.find_elements(By.CLASS_NAME, "btn_inventory")[:n]:
            btn.click()

    def open_cart(self):
        self.driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        self.wait.until(EC.url_contains("cart"))

    def click_checkout(self):
        self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-test="checkout"]')
            )
        ).click()


# ---------------- tests --------------------------------------------------- #
class TestPositiveFlow(BaseTest):
    def test_checkout_positive(self):
        self.login()
        self.add_items(2)
        self.open_cart()
        self.click_checkout()

        d = self.driver
        d.find_element(By.ID, "first-name").send_keys("QA")
        d.find_element(By.ID, "last-name").send_keys("Bot")
        d.find_element(By.ID, "postal-code").send_keys("00000")
        d.find_element(By.ID, "continue").click()
        self.wait.until(EC.element_to_be_clickable((By.ID, "finish"))).click()

        # Assert order complete
        self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h2.complete-header"))
        )
        snap(d, "positive_pass")


class TestNegativeFlow(BaseTest):
    def test_checkout_missing_first_name(self):
        self.login()
        self.add_items(1)  # need ≥1 item so checkout button exists
        self.open_cart()
        self.click_checkout()

        d = self.driver
        # leave first-name blank
        d.find_element(By.ID, "last-name").send_keys("Bot")
        d.find_element(By.ID, "postal-code").send_keys("00000")
        d.find_element(By.ID, "continue").click()

        err = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h3[data-test='error']"))
        )
        self.assertIn("First Name", err.text)
        snap(d, "negative_fail")


# ---------------- main ---------------------------------------------------- #
if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)

    try:
        import imageio

        if len(CURRENT_SHOTS) >= 2:
            frames = [imageio.imread(p) for p in CURRENT_SHOTS]
            imageio.mimsave(
                "demo.gif",
                frames,
                duration=2500,  # seconds per frame
                loop=0         # infinite loop
            )
            print(f"[✓] demo.gif created from {len(frames)} frames (looping)")
        else:
            print("[!] Not enough screenshots – GIF skipped")
    except Exception as e:
        print(f"[!] GIF build failed – {e}")
    import shutil
    for p in CURRENT_SHOTS:
        try: p.unlink()
        except FileNotFoundError:
            pass

