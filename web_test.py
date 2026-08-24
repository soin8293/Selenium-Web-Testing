"""Functional and accessibility-smoke tests for the public SauceDemo sandbox."""

from __future__ import annotations

import os
import time
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from pages import InventoryPage, LoginPage

SHOT_DIR = Path("screenshots")
SHOT_DIR.mkdir(exist_ok=True)
CURRENT_SHOTS: list[Path] = []


def snap(driver, label: str) -> None:
    path = SHOT_DIR / f"{label}_{time.strftime('%Y%m%d-%H%M%S')}.png"
    driver.save_screenshot(str(path))
    CURRENT_SHOTS.append(path)
    print(f"[PASS] Screenshot saved: {path}")


class BaseTest(unittest.TestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            },
        )
        options.add_argument("--incognito")
        options.add_argument(
            "--disable-features=PasswordManagerEnableNotificationUI,PasswordLeakDetection,AutofillAssistant"
        )
        if os.getenv("CI"):
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1280,800")

        self.driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=options,
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        driver = getattr(self, "driver", None)
        if driver:
            driver.quit()

    def login_standard(self) -> InventoryPage:
        LoginPage(self.driver, self.wait).open().login()
        return InventoryPage(self.driver, self.wait).wait_until_loaded()


class TestCheckout(BaseTest):
    def test_checkout_positive(self):
        checkout = self.login_standard().add_items(2).open_cart().checkout()
        complete = checkout.enter_customer("QA", "Bot", "00000").continue_checkout().finish()
        self.assertIn("Thank you", complete.heading())
        snap(self.driver, "positive_pass")

    def test_checkout_missing_first_name(self):
        checkout = self.login_standard().add_items(1).open_cart().checkout()
        checkout.enter_customer(last="Bot", postal="00000").continue_checkout()
        self.assertIn("First Name", checkout.error_text())
        snap(self.driver, "missing_first_name")


class TestAuthentication(BaseTest):
    def test_locked_out_user_is_rejected(self):
        login = LoginPage(self.driver, self.wait).open().login("locked_out_user")
        self.assertIn("locked out", login.error_text().lower())


class TestAccessibilitySmoke(BaseTest):
    def test_accessibility_smoke_records_known_empty_cart_name_gap(self):
        login = LoginPage(self.driver, self.wait).open()
        self.assertEqual(login.accessibility_smoke_issues(), [])
        login.login()
        inventory = InventoryPage(self.driver, self.wait).wait_until_loaded()
        issues = inventory.accessibility_smoke_issues()
        self.assertEqual(len(issues), 1)
        self.assertIn("shopping_cart_link", issues[0])


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    try:
        import imageio.v2 as imageio

        if len(CURRENT_SHOTS) >= 2:
            frames = [imageio.imread(path) for path in CURRENT_SHOTS]
            imageio.mimsave("demo.gif", frames, duration=2500, loop=0)
            print(f"[PASS] demo.gif created from {len(frames)} frames")
    except Exception as exc:
        print(f"[!] GIF build failed - {exc}")

    if not os.getenv("CI"):
        for path in CURRENT_SHOTS:
            path.unlink(missing_ok=True)

    raise SystemExit(0 if program.result.wasSuccessful() else 1)
