# Selenium-Web-Testing

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](#)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green)](#)
[![CI](https://github.com/yourname/Selenium-Web-Testing/actions/workflows/ci.yml/badge.svg)](#)

Automated functional tests for **Saucedemo.com** using Python + Selenium.

## Setup
```bash
pip install -r requirements.txt
# no manual ChromeDriver download: webdriver-manager fetches it
```
## Run locally
```bash
python web_test.py
```
Two tests execute:
1. **Positive flow** – log in (`standard_user/secret_sauce`), add items, checkout, complete order.  
2. **Negative flow** – blank first-name on checkout, assert error.

Screenshots for each step save to `screenshots/`.  
GitHub Actions runs the same tests headless on every push.

MIT License.
