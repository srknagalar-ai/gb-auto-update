from __future__ import annotations

from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright

SPREADSHEET_ID = "1ZxLqP19OUmZalIvhQpV7jiA_uJQg-bzxHTDxp3--z7I"
WORKSHEET_NAME = "ALL-IN-ONE"
CREDENTIALS_FILE = "C:/Users/Serkan/Desktop/credentials.json"
URL = "https://www.enucuzgb.com/rise-online-mobile/gb?d=1"

BUY_CELL = "B2"
SELL_CELL = "B3"
TIME_CELL = "B4"


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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)

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
        finally:
            browser.close()


def update_google_sheet(buy_price, sell_price):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    worksheet.update_acell(BUY_CELL, buy_price)
    worksheet.update_acell(SELL_CELL, sell_price)
    worksheet.update_acell(TIME_CELL, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def main():
    buy_price, sell_price = fetch_prices()
    update_google_sheet(buy_price, sell_price)
    print(f"Tamamlandı | GB Alış: {buy_price} | GB Satış: {sell_price}")


if __name__ == "__main__":
    main()
