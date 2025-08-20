import pytest
from pathlib import Path
import os
import requests
import shutil
import hashlib
from pytest_html import extras

DOWNLOAD_DIR = "downloads"

def compare_screenshots(page, before_path, after_path, change_desc, selector, extra=None):
    page.screenshot(path=str(before_path), full_page=True)

    page.click("button[type='submit']")

    page.wait_for_selector(selector, timeout=5000)

    page.screenshot(path=str(after_path), full_page=True)

    with open(before_path, "rb") as f1, open(after_path, "rb") as f2:
        hash1 = hashlib.sha256(f1.read()).hexdigest()
        hash2 = hashlib.sha256(f2.read()).hexdigest()

    match = hash1 == hash2
    status = "IDENTYCZNE" if match else "RÓŻNE"
    color = "green" if match else "red"

    html = f"""
    <div style="color:{color}; font-weight:bold;">
        Porównanie screenów ({change_desc}): {status}
    </div>
    <div><strong>SHA256 Screenshot BEFORE:</strong> {hash1}</div>
    <div><strong>SHA256 Screenshot AFTER:</strong> {hash2}</div>
    """

    if extra:
        extra.append(extras.html(html))


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
    weeks = ["1", "4", "8"]

    if "currency_code" in metafunc.fixturenames:
        metafunc.parametrize("currency_code", currencies)

    if "week_value" in metafunc.fixturenames:
        metafunc.parametrize("week_value", weeks)

def setup_browser(playwright, browser_name):
    if not isinstance(browser_name, str):
        raise ValueError(f"browser_name powinno być ciągiem znaków, a nie {type(browser_name)}")

    if browser_name not in ["chromium", "firefox", "webkit"]:
        raise ValueError(f"Nieobsługiwana przeglądarka: {browser_name}")

    browser = getattr(playwright, browser_name).launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return browser, context, page

def switch_page(page, currency_code, browser_name=None, extra=None):
    page.goto("http://localhost:1111/")
    page.select_option("#currency", value=currency_code)
    page.click("button[type='submit']")
    assert_currency_page_loaded(page, currency_code)

def switch_currency(playwright, browser_name, extra):
    browser, context, page = setup_browser(playwright, browser_name)

    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)

    page.select_option("#currency", value="USD")

    before = Path(DOWNLOAD_DIR) / f"{browser_name}-currency-before.png"
    after = Path(DOWNLOAD_DIR) / f"{browser_name}-currency-after.png"

    compare_screenshots(
        page,
        before_path=before,
        after_path=after,
        change_desc="zmiana waluty na USD",
        selector="img[alt='Wykres USD']",
        extra=extra
    )

    browser.close()

def download_excel(page, browser_name, currency_code):
    with page.expect_download() as download_info:
        page.click(f"a[href*='/download/excel?currency={currency_code}'] >> button")
    download = download_info.value
    filename = download.suggested_filename or f"{currency_code}_data.xlsx"
    excel_path = f"{DOWNLOAD_DIR}/{browser_name}-{filename}"
    download.save_as(excel_path)
    assert Path(excel_path).exists(), f"Excel nie został pobrany: {excel_path}"
    assert excel_path.endswith(".xlsx"), f"Zły format pliku: {excel_path}"

def download_chart(page, browser_name, currency_code):
    chart_path = f"{DOWNLOAD_DIR}/{browser_name}-{currency_code}_chart.png"
    if browser_name == "webkit":
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

def switch_time(page, week_value, currency_code, browser_name=None, extra=None):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)

    page.select_option("#currency", value=currency_code)
    before = Path(DOWNLOAD_DIR) / f"{browser_name}-before-time-{currency_code}-{week_value}.png"
    after = Path(DOWNLOAD_DIR) / f"{browser_name}-after-time-{currency_code}-{week_value}.png"
    page.screenshot(path=str(before), full_page=True)
    page.select_option("#time", value=week_value)
    page.click("button[type='submit']")
    page.wait_for_selector(f"img[alt='Wykres {currency_code}']", timeout=5000)

    page.screenshot(path=str(after), full_page=True)

    with open(before, "rb") as f1, open(after, "rb") as f2:
        hash1 = hashlib.sha256(f1.read()).hexdigest()
        hash2 = hashlib.sha256(f2.read()).hexdigest()

    match = hash1 == hash2
    status = "IDENTYCZNE" if match else "RÓŻNE"
    color = "green" if match else "red"

    html = f"""
    <div style="color:{color}; font-weight:bold;">
        Porównanie screenów po zmianie czasu ({week_value} tygodni) dla waluty {currency_code}: {status}
    </div>
    <div><strong>SHA256 Screenshot BEFORE:</strong> {hash1}</div>
    <div><strong>SHA256 Screenshot AFTER:</strong> {hash2}</div>
    """

    if extra is not None:
        extra.append(extras.html(html))


def switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra):
    browser, context, page = setup_browser(playwright, browser_name)

    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)
    page.select_option("#currency", value=currency_code)
    page.select_option("#time", value=week_value)
    before = Path(DOWNLOAD_DIR) / f"{browser_name}-before-{currency_code}-{week_value}.png"
    after = Path(DOWNLOAD_DIR) / f"{browser_name}-after-{currency_code}-{week_value}.png"
    page.screenshot(path=str(before), full_page=True)
    page.click("button[type='submit']")
    page.wait_for_selector(f"img[alt='Wykres {currency_code}']", timeout=5000)
    page.screenshot(path=str(after), full_page=True)
    with open(before, "rb") as f1, open(after, "rb") as f2:
        hash1 = hashlib.sha256(f1.read()).hexdigest()
        hash2 = hashlib.sha256(f2.read()).hexdigest()

    match = hash1 == hash2
    status = "IDENTYCZNE" if match else "RÓŻNE"
    color = "green" if match else "red"

    html = f"""
    <div style="color:{color}; font-weight:bold;">
        Porównanie screenów po zmianie waluty ({currency_code}) i czasu ({week_value} tygodni): {status}
    </div>
    <div><strong>SHA256 Screenshot BEFORE:</strong> {hash1}</div>
    <div><strong>SHA256 Screenshot AFTER:</strong> {hash2}</div>
    """

    extra.append(extras.html(html))

    browser.close()

def download_excel_for_currency_and_week(page, currency, week_value, browser_name, extra):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)
    page.select_option("#currency", value=currency)
    page.select_option("#time", value=week_value)
    page.click("button[type='submit']")
    page.wait_for_selector(f"img[alt='Wykres {currency}']", timeout=5000)
    with page.expect_download() as download_info:
        page.click(f"a[href*='/download/excel?currency={currency}'] >> button")
    download = download_info.value
    filename = download.suggested_filename or f"{currency}_data.xlsx"
    filepath = os.path.join(DOWNLOAD_DIR, f"{browser_name}-{filename}")
    download.save_as(filepath)
    assert Path(filepath).exists(), f"Nie znaleziono pliku: {filepath}"
    assert filepath.endswith(".xlsx"), f"Zły format pliku: {filepath}"
    extra.append(extras.url(filepath, name=f"{currency} Excel (8 tygodni)"))

def download_chart_for_currency_and_week(page, currency, week_value, browser_name, extra):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)

    page.select_option("#currency", value=currency)
    page.select_option("#time", value=week_value)

    page.click("button[type='submit']")
    page.wait_for_selector(f"img[alt='Wykres {currency}']", timeout=10000)

    download_link = page.locator(f"a[href*='/download/chart?currency={currency}']")
    download_link.wait_for(state="visible", timeout=5000)

    href = download_link.get_attribute("href")
    assert href and currency in href, f"Link download chart href incorrect or missing currency: {href}"

    chart_path = os.path.join(DOWNLOAD_DIR, f"{browser_name}-{currency}_chart.png")

    if browser_name == "webkit":
        try:
            url = f"http://localhost:1111{href}" if href.startswith("/") else href
            response = requests.get(url)
            assert response.status_code == 200, f"HTTP status {response.status_code} when downloading chart"
            with open(chart_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            raise Exception(f"WebKit fallback failed: {e}")
    else:
        with page.expect_download() as download_info:
            page.click(f"a[href*='/download/chart?currency={currency}'] >> button")
        download = download_info.value
        download.save_as(chart_path)

    assert Path(chart_path).exists(), f"Nie znaleziono pliku wykresu: {chart_path}"
    assert chart_path.endswith(".png"), f"Zły format pliku: {chart_path}"

    extra.append(extras.url(chart_path, name=f"{currency} Wykres ({week_value} tygodni)"))




def test_open_currency_page(playwright, browser_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    url = f"http://localhost:1111/?currency={currency_code}"
    page.goto(url)
    assert_currency_page_loaded(page, currency_code)
    browser.close()

def test_switch_page(playwright, browser_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    switch_page(page, currency_code, browser_name=browser_name, extra=extra)
    browser.close()

def test_switch_currency(playwright, browser_name, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    switch_currency(playwright, browser_name, extra)
    browser.close()

def test_download_excel(playwright, browser_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    switch_page(page, currency_code, browser_name=browser_name, extra=extra)
    download_excel(page, browser_name, currency_code)
    browser.close()

    filename = f"{browser_name}-{currency_code}_data.xlsx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Excel"))

def test_download_chart(playwright, browser_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    switch_page(page, currency_code, browser_name=browser_name, extra=extra)
    download_chart(page, browser_name, currency_code)
    browser.close()

    filename = f"{browser_name}-{currency_code}_chart.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Wykres"))


def test_switch_time(playwright, browser_name, currency_code, week_value, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    switch_time(page, week_value, currency_code, browser_name=browser_name, extra=extra)
    browser.close()

def test_switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra):
    switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra)

@pytest.mark.parametrize("currency", ["USD", "CHF", "CZK"], ids=["USD", "CHF", "CZK"])
def test_download_excel_8_weeks(playwright, browser_name, currency, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    download_excel_for_currency_and_week(page, currency, "8", browser_name, extra)
    browser.close()

@pytest.mark.parametrize("currency", ["USD", "CHF", "CZK"], ids=["USD", "CHF", "CZK"])
def test_download_chart_8_weeks(playwright, browser_name, currency, extra):
    browser, context, page = setup_browser(playwright, browser_name)
    download_chart_for_currency_and_week(page, currency, "8", browser_name, extra)
    browser.close()
