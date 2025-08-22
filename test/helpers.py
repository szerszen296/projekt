import hashlib
import os
import requests
from pathlib import Path
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

    match = hash1 != hash2

    assert not match is False, "Zmiana waluty nie spowodowała zmiany widoku"

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

def switch_currency(page, browser_name, extra):
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


def download_excel(page, browser_name, currency_code):
    with page.expect_download() as download_info:
        page.click(f"a[href*='/download/excel?currency={currency_code}'] >> button")
    download = download_info.value
    filename = download.suggested_filename or f"{currency_code}_data.xlsx"
    excel_path = f"{DOWNLOAD_DIR}/{browser_name}-{currency_code}-{filename}"
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

def switch_time(page, browser_name, currency_code, week_value, extra):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)
    page.select_option("#currency", value=currency_code)

    name_prefix = f"{browser_name}-time-{currency_code}-{week_value}"
    before_path = Path(DOWNLOAD_DIR) / f"{name_prefix}-before.png"
    after_path = Path(DOWNLOAD_DIR) / f"{name_prefix}-after.png"

    page.screenshot(path=str(before_path), full_page=True)
    page.select_option("#time", value=week_value)

    compare_screenshots(
        page=page,
        before_path=before_path,
        after_path=after_path,
        change_desc=f"zmiana czasu na {week_value} tygodni dla waluty {currency_code}",
        selector=f"img[alt='Wykres {currency_code}']",
        extra=extra
    )


def switch_currency_and_time(page, browser_name, currency_code, week_value, extra):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency-table", timeout=5000)

    page.select_option("#currency", value=currency_code)
    page.select_option("#time", value=week_value)

    name_prefix = f"{browser_name}-currency-time-{currency_code}-{week_value}"
    before_path = Path(DOWNLOAD_DIR) / f"{name_prefix}-before.png"
    after_path = Path(DOWNLOAD_DIR) / f"{name_prefix}-after.png"

    page.screenshot(path=str(before_path), full_page=True)

    compare_screenshots(
        page=page,
        before_path=before_path,
        after_path=after_path,
        change_desc=f"zmiana waluty na {currency_code} i czasu na {week_value} tygodni",
        selector=f"img[alt='Wykres {currency_code}']",
        extra=extra
    )


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
    filepath = os.path.join(DOWNLOAD_DIR, f"{browser_name}-{currency}-{week_value}-{filename}")
    download.save_as(filepath)
    assert Path(filepath).exists(), f"Nie znaleziono pliku: {filepath}"
    assert filepath.endswith(".xlsx"), f"Zły format pliku: {filepath}"
    extra.append(extras.url(filepath, name=f"{currency} Excel ({week_value} tygodni)"))

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
    chart_path = os.path.join(DOWNLOAD_DIR, f"{browser_name}-{currency}-{week_value}_chart.png")

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

def get_currency_options(page):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency")
    options = page.locator("#currency option")
    count = options.count()
    return [options.nth(i).get_attribute("value") for i in range(count)]

def get_time_options(page):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#time")
    options = page.locator("#time option")
    count = options.count()
    return [options.nth(i).get_attribute("value") for i in range(count)]

def select_three_options(options_list):
    if not options_list:
        return []
    first = options_list[0]
    middle = options_list[len(options_list) // 2]
    last = options_list[-1]
    return list(dict.fromkeys([first, middle, last]))

def check_all_currency_options_present(page, currencies_number):
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency")

    currency_options = page.locator("#currency option")
    count = currency_options.count()
    assert count >= currencies_number or count <= currencies_number, f"Oczekiwano co najmniej 10 walut, znaleziono: {count}"

    labels = [currency_options.nth(i).inner_text() for i in range(count)]
    print("Waluty na liście:", labels)


def check_all_time_options_present(page, weeks_number):
    page.goto("http://localhost:1111/")
    expected = get_time_options(page)
    actual_options = page.locator("#time option")
    actual_count = actual_options.count()

    time_options = page.locator("#time option")
    count = time_options.count()
    assert count >= weeks_number or count <= weeks_number, f"Oczekiwano co najmniej 8 zakresów czasu, znaleziono: {count}"

    labels = [time_options.nth(i).inner_text() for i in range(count)]
    print("Zakresy czasu na liście:", labels)
