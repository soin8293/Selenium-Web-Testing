"""Small page-object layer for the public SauceDemo test sandbox."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.saucedemo.com"
PASSWORD = "secret_sauce"


class BasePage:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def accessibility_smoke_issues(self) -> list[str]:
        """Check a narrow set of machine-testable page accessibility basics."""
        issues = []
        lang = self.driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
        if not lang:
            issues.append("document has no language")
        if not self.driver.title.strip():
            issues.append("document has no title")

        unnamed = self.driver.execute_script(
            """
            return Array.from(document.querySelectorAll('input, button, a'))
              .filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
              })
              .filter(el => !(
                el.getAttribute('aria-label') ||
                el.getAttribute('aria-labelledby') ||
                el.getAttribute('placeholder') ||
                el.getAttribute('title') ||
                el.value ||
                el.innerText.trim() ||
                el.querySelector('img[alt]')
              ))
              .map(el => el.outerHTML.slice(0, 120));
            """
        )
        issues.extend(f"interactive element has no accessible name: {item}" for item in unnamed)
        return issues


class LoginPage(BasePage):
    def open(self):
        self.driver.get(BASE_URL)
        self.wait.until(EC.visibility_of_element_located((By.ID, "user-name")))
        return self

    def login(self, username: str = "standard_user", password: str = PASSWORD):
        self.driver.find_element(By.ID, "user-name").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()
        return self

    def error_text(self) -> str:
        return self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h3[data-test='error']"))
        ).text


class InventoryPage(BasePage):
    def wait_until_loaded(self):
        self.wait.until(EC.url_contains("inventory"))
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='title']")))
        return self

    def add_items(self, count: int = 1):
        buttons = self.driver.find_elements(By.CLASS_NAME, "btn_inventory")
        if len(buttons) < count:
            raise AssertionError(f"Expected at least {count} inventory items")
        for button in buttons[:count]:
            button.click()
        return self

    def open_cart(self):
        self.driver.find_element(By.CSS_SELECTOR, "[data-test='shopping-cart-link']").click()
        return CartPage(self.driver, self.wait).wait_until_loaded()


class CartPage(BasePage):
    def wait_until_loaded(self):
        self.wait.until(EC.url_contains("cart"))
        return self

    def checkout(self):
        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='checkout']"))
        ).click()
        return CheckoutPage(self.driver, self.wait).wait_until_loaded()


class CheckoutPage(BasePage):
    def wait_until_loaded(self):
        self.wait.until(EC.url_contains("checkout-step-one"))
        return self

    def enter_customer(self, first: str = "", last: str = "", postal: str = ""):
        self.driver.find_element(By.ID, "first-name").send_keys(first)
        self.driver.find_element(By.ID, "last-name").send_keys(last)
        self.driver.find_element(By.ID, "postal-code").send_keys(postal)
        return self

    def continue_checkout(self):
        self.driver.find_element(By.ID, "continue").click()
        return self

    def error_text(self) -> str:
        return self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h3[data-test='error']"))
        ).text

    def finish(self):
        self.wait.until(EC.url_contains("checkout-step-two"))
        self.wait.until(EC.element_to_be_clickable((By.ID, "finish"))).click()
        return CompletePage(self.driver, self.wait)


class CompletePage(BasePage):
    def heading(self) -> str:
        return self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h2.complete-header"))
        ).text
