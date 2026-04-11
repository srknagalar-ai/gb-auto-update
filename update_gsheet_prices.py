from __future__ import annotations

import os
import json
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright

WORKSHEET_NAME = "ALL-IN-ONE"
BUY_CELL = "B2"
SELL_CELL = "B3"
TIME_CELL = "B4"
URL = "https://www.enucuzgb.com/rise-online-mobile/gb?d=1"


def text_to_numbers(values):
    nums = []
    for v in values:
        try:
            n = float(v.strip().replace(",", "."))
            if n > 0:
                nums.append(n)
        except Exception:
            pass
    return nums


def fetch_prices():
    last_error = None

    for _ in range(3):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 1200},
            )

            try:
                page.goto(URL, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(10000)

                page.wait_for_selector(".highlight-min", timeout=30000)
                page.wait_for_selector(".highlight-max", timeout=30000)

                sell_values = page.locator(".highlight-min").all_inner_texts()
                buy_values = page.locator(".highlight-max").all_inner_texts()

                sell_numbers = text_to_numbers(sell_values)
                buy_numbers = text_to_numbers(buy_values)

                if not sell_numbers:
                    raise RuntimeError(f"GB satış bulunamadı | sell_values={sell_values}")
                if not buy_numbers:
                    raise RuntimeError(f"GB alış bulunamadı | buy_values={buy_values}")

                sell_price = min(sell_numbers)
                buy_price = max(buy_numbers)

                return buy_price, sell_price

            except Exception as exc:
                last_error = exc
            finally:
                browser.close()

    raise RuntimeError(f"Fiyat çekilemedi: {last_error}")


def update_google_sheet(buy_price, sell_price):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds_json = os.environ["GOOGLE_CREDS"]
    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(os.environ["SPREADSHEET_ID"])
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    worksheet.update_acell(BUY_CELL, buy_price)
    worksheet.update_acell(SELL_CELL, sell_price)
    worksheet.update_acell(TIME_CELL, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def main():
    buy_price, sell_price = fetch_prices()
    update_google_sheet(buy_price, sell_price)
    print(f"Tamamlandı | Alış: {buy_price} | Satış: {sell_price}")


if __name__ == "__main__":
    main()
