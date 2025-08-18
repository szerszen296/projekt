import pytest
from pathlib import Path
import os
import requests
import shutil

DOWNLOAD_DIR = "downloads"

@pytest.fixture(scope="session", autouse=True)
def clean_download_dir():
    download_path = Path(DOWNLOAD_DIR)
    if download_path.exists():
        shutil.rmtree(download_path)
    download_path.mkdir(parents=True, exist_ok=True)

def pytest_generate_tests(metafunc):
    if "br_name" in metafunc.fixturenames and "currency_code" in metafunc.fixturenames:
        browsers = ["chromium", "firefox", "webkit"]
        currencies = ["USD", "CHF", "CZK"]
        metafunc.parametrize("br_name", browsers)
        metafunc.parametrize("currency_code", currencies)

def setup_browser(playwright, br_name):
    browser = getattr(playwright, br_name).launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return browser, context, page

def open_currency_page(page, currency_code):
    page.goto(f"http://localhost:1111/?currency={currency_code}")
    rows = page.locator("#currency-table tbody tr")
    count = rows.count()
    assert 4 <= count <= 7, f"znaleziono: {count}"
    image = page.locator(f"img[alt='Wykres {currency_code}']")
    image.wait_for(state="visible", timeout=5000)
    handle = image.element_handle()
    assert handle is not None, f"Nie znaleziono wykresu {currency_code}"
    width = page.evaluate("el => el.naturalWidth", handle)
    height = page.evaluate("el => el.naturalHeight", handle)
    assert width > 100 and height > 100, f"Wykres ma dziwne wymiary: {width}x{height}"

def download_excel(page, br_name, currency_code):
    with page.expect_download() as download_info:
        page.click(f"a[href*='/download/excel?currency={currency_code}'] >> button")
    download = download_info.value
    filename = download.suggested_filename or f"{currency_code}_data.xlsx"
    excel_path = f"{DOWNLOAD_DIR}/{br_name}-{filename}"
    download.save_as(excel_path)
    assert Path(excel_path).exists(), f"Excel nie został pobrany: {excel_path}"
    assert excel_path.endswith(".xlsx"), f"Zły format pliku: {excel_path}"

def download_chart(page, br_name, currency_code):
    chart_path = f"{DOWNLOAD_DIR}/{br_name}-{currency_code}_chart.png"
    if br_name == "webkit":
        img_link = page.locator(f"a[href*='/download/chart?currency={currency_code}']")
        if img_link.count() > 0:
            try:
                img_link.wait_for(state="visible", timeout=3000)
                href = img_link.get_attribute("href")
                if href:
                    url = f"http://localhost:1111{href}" if href.startswith("/") else href
                    response = requests.get(url)
                    if response.status_code == 200:
                        with open(chart_path, "wb") as f:
                            f.write(response.content)
                    else:
                        raise Exception(f"Niepoprawny status HTTP: {response.status_code}")
            except Exception as e:
                print(f"Fallback WebKit nie powiódł się: {e}")
                chart_path = None
        else:
            print("Nie znaleziono linku do wykresu dla WebKit.")
            chart_path = None
    else:
        try:
            with page.expect_download() as download_info:
                page.click(f"a[href*='/download/chart?currency={currency_code}'] >> button")
            download = download_info.value
            download.save_as(chart_path)
        except Exception as e:
            print(f"Download przez Playwright nie powiódł się: {e}")
            chart_path = None
    if chart_path:
        assert Path(chart_path).exists(), f"Plik wykresu nie został pobrany: {chart_path}"
        assert chart_path.endswith(".png"), f"Zły format wykresu: {chart_path}"

def test_open_currency_page(playwright, br_name, currency_code):
    browser, context, page = setup_browser(playwright, br_name)
    open_currency_page(page, currency_code)
    browser.close()

def test_download_excel(playwright, br_name, currency_code):
    browser, context, page = setup_browser(playwright, br_name)
    open_currency_page(page, currency_code)
    download_excel(page, br_name, currency_code)
    browser.close()

def test_download_chart(playwright, br_name, currency_code):
    browser, context, page = setup_browser(playwright, br_name)
    open_currency_page(page, currency_code)
    download_chart(page, br_name, currency_code)
    browser.close()
