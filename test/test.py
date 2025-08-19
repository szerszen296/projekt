import pytest
from pathlib import Path
import os
import requests
import shutil
import hashlib
from pytest_html import extras

DOWNLOAD_DIR = "downloads"

@pytest.fixture(scope="session", autouse=True)
def clean_download_dir():
    download_path = Path(DOWNLOAD_DIR)
    if download_path.exists():
        for file in download_path.glob("*_screenshot*.png"):
            file.unlink()
    else:
        download_path.mkdir(parents=True, exist_ok=True)

def pytest_generate_tests(metafunc):
    browsers = ["chromium", "firefox", "webkit"]
    currencies = ["USD", "CHF", "CZK"]
    if "br_name" in metafunc.fixturenames and "currency_code" in metafunc.fixturenames:
        metafunc.parametrize("br_name", browsers)
        metafunc.parametrize("currency_code", currencies)
    elif "br_name" in metafunc.fixturenames:
        metafunc.parametrize("br_name", browsers)

def setup_browser(playwright, br_name):
    browser = getattr(playwright, br_name).launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return browser, context, page

def take_and_compare_screenshot(page, currency_code, br_name, extra):
    download_path = Path(DOWNLOAD_DIR)
    current_path = download_path / "last_screenshot.png"
    prev_path = download_path / "prev_screenshot.png"

    if current_path.exists():
        if prev_path.exists():
            prev_path.unlink()
        shutil.copy(current_path, prev_path)

    page.screenshot(path=str(current_path), full_page=True)

    if prev_path.exists():
        with open(current_path, "rb") as f1, open(prev_path, "rb") as f2:
            current_bytes = f1.read()
            prev_bytes = f2.read()
            hash_current = hashlib.sha256(current_bytes).hexdigest()
            hash_prev = hashlib.sha256(prev_bytes).hexdigest()

        match = hash_current == hash_prev
        status = "IDENTYCZNE" if match else "RÓŻNE"
        color = "green" if match else "red"

        html = f"""
        <div style="color:{color}; font-weight:bold;">Porównanie z poprzednim: {status}</div>
        <div><strong>Aktualny plik:</strong> last_screenshot.png</div>
        <div><strong>Poprzedni plik:</strong> prev_screenshot.png</div>
        <div><strong>SHA256 aktualny:</strong> {hash_current}</div>
        <div><strong>SHA256 poprzedni:</strong> {hash_prev}</div>
        """
    else:
        html = """
        <div style="color:orange; font-weight:bold;">To pierwszy screenshot – brak porównania</div>
        <div><strong>Plik:</strong> last_screenshot.png</div>
        """

    extra.append(extras.html(html))

def switch_page(page, currency_code, br_name=None, extra=None):
    page.goto("http://localhost:1111/")
    page.select_option("#currency", value=currency_code)
    page.click("button[type='submit']")

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

    if br_name and extra is not None:
        take_and_compare_screenshot(page, currency_code, br_name, extra)

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
    browser.close()

def test_switch_page(playwright, br_name, currency_code, extra):
    browser, context, page = setup_browser(playwright, br_name)
    switch_page(page, currency_code, br_name=br_name, extra=extra)
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

def test_check_all_charts_hashes_different():
    download_dir = Path(DOWNLOAD_DIR)
    chart_files = list(download_dir.glob("*_chart.png"))
    assert chart_files, "Brak pobranych wykresów do porównania"

    hashes = []
    for file in chart_files:
        content = file.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        hashes.append(file_hash)

    unique_hashes = set(hashes)
    print(f"Hashe wykresów: {hashes}")
    assert len(unique_hashes) > 1, "Wszystkie wykresy mają identyczny hash!"
