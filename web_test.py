import unittest, os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.saucedemo.com"
USER, PW = "standard_user", "secret_sauce"
SS_DIR = "screenshots"

def now():
    return time.strftime("%Y%m%d-%H%M%S")

def shot(driver, name):
    driver.save_screenshot(os.path.join(SS_DIR, f"{name}_{now()}.png"))

class BaseTest(unittest.TestCase):
    def setUp(self):
        opts = webdriver.ChromeOptions()
        if os.getenv("CI"): opts.add_argument("--headless=new")
        self.driver = webdriver.Chrome(
            options=opts,
            service=webdriver.chrome.service.Service(
                ChromeDriverManager().install()))
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def login(self):
        d = self.driver
        d.get(BASE_URL)
        d.find_element(By.ID, "user-name").send_keys(USER)
        d.find_element(By.ID, "password").send_keys(PW)
        d.find_element(By.ID, "login-button").click()
        self.wait.until(EC.title_contains("Swag Labs"))

class TestPositiveFlow(BaseTest):
    def test_checkout_positive(self):
        self.login()
        d = self.driver
        # add first two items
        for btn in d.find_elements(By.CLASS_NAME, "btn_inventory")[:2]:
            btn.click()
        d.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        d.find_element(By.ID, "checkout").click()
        d.find_element(By.ID, "first-name").send_keys("QA")
        d.find_element(By.ID, "last-name").send_keys("Bot")
        d.find_element(By.ID, "postal-code").send_keys("00000")
        d.find_element(By.ID, "continue").click()
        d.find_element(By.ID, "finish").click()
        self.assertIn("complete", d.current_url)
        shot(d, "positive_pass")

class TestNegativeFlow(BaseTest):
    def test_checkout_missing_first_name(self):
        self.login()
        d = self.driver
        d.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        d.find_element(By.ID, "checkout").click()
        d.find_element(By.ID, "last-name").send_keys("Bot")
        d.find_element(By.ID, "postal-code").send_keys("00000")
        d.find_element(By.ID, "continue").click()
        err = self.wait.until(EC.visibility_of_element_located(
            (By.CLASS_NAME, "error-message-container")))
        self.assertIn("First Name", err.text)
        shot(d, "negative_fail")

if __name__ == "__main__":
    os.makedirs(SS_DIR, exist_ok=True)
    unittest.main(verbosity=2)
