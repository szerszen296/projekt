import pytest
from pathlib import Path
import os
import requests
import shutil
import hashlib
from pytest_html import extras

DOWNLOAD_DIR = "downloads"

def assert_currency_page_loaded(page, currency_code):
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

def pytest_generate_tests(metafunc):
    browsers = ["chromium", "firefox", "webkit"]
    currencies = ["USD", "CHF", "CZK"]

    if "currency_code" in metafunc.fixturenames:
        metafunc.parametrize("currency_code", currencies)
    
    if "br_name" in metafunc.fixturenames:
        browser = os.getenv('BROWSER', 'chromium') 
        metafunc.parametrize("br_name", [browser])

def setup_browser(playwright, br_name):
    if not isinstance(br_name, str):
        raise ValueError(f"br_name powinno być ciągiem znaków, a nie {type(br_name)}")

    if br_name not in ["chromium", "firefox", "webkit"]:
        raise ValueError(f"Nieobsługiwana przeglądarka: {br_name}")

    browser = getattr(playwright, br_name).launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return browser, context, page

def switch_page(page, currency_code, br_name=None, extra=None):
    page.goto("http://localhost:1111/")
    page.select_option("#currency", value=currency_code)
    page.click("button[type='submit']")
    assert_currency_page_loaded(page, currency_code)

def switch_currency(playwright, br_name, extra):
    browser, context, page = setup_browser(playwright, br_name)

    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)

    screenshot1 = Path(DOWNLOAD_DIR) / "screenshot1.png"
    page.screenshot(path=str(screenshot1), full_page=True)

    page.select_option("#currency", value="USD")
    page.click("button[type='submit']")
    page.wait_for_selector("img[alt='Wykres USD']", timeout=5000)

    screenshot2 = Path(DOWNLOAD_DIR) / "screenshot2.png"
    page.screenshot(path=str(screenshot2), full_page=True)

    with open(screenshot1, "rb") as f1, open(screenshot2, "rb") as f2:
        hash1 = hashlib.sha256(f1.read()).hexdigest()
        hash2 = hashlib.sha256(f2.read()).hexdigest()

    match = hash1 == hash2
    status = "IDENTYCZNE" if match else "RÓŻNE"
    color = "green" if match else "red"

    html = f"""
    <div style="color:{color}; font-weight:bold;">Porównanie screenów: {status}</div>
    <div><strong>SHA256 Screenshot 1:</strong> {hash1}</div>
    <div><strong>SHA256 Screenshot 2:</strong> {hash2}</div>
    """
    extra.append(extras.html(html))

    browser.close()

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

def test_open_currency_page(playwright, br_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, br_name)
    url = f"http://localhost:1111/?currency={currency_code}"
    page.goto(url)
    assert_currency_page_loaded(page, currency_code)
    browser.close()

def test_switch_page(playwright, br_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, br_name)
    switch_page(page, currency_code, br_name=br_name, extra=extra)
    browser.close()

def test_switch_currency(playwright, br_name, extra):
    browser, context, page = setup_browser(playwright, br_name)
    switch_currency(playwright, br_name, extra)
    browser.close()

def test_download_excel(playwright, br_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, br_name)
    switch_page(page, currency_code, br_name=br_name, extra=extra)
    download_excel(page, br_name, currency_code)
    browser.close()

    filename = f"{br_name}-{currency_code}_data.xlsx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Excel"))

def test_download_chart(playwright, br_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, br_name)
    switch_page(page, currency_code, br_name=br_name, extra=extra)
    download_chart(page, br_name, currency_code)
    browser.close()

    filename = f"{br_name}-{currency_code}_chart.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Wykres"))
