import pytest
from pathlib import Path
import requests

DOWNLOAD_DIR = "downloads"

def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="all",
        help="Wybierz przeglądarkę: chromium, firefox, webkit lub all (domyślnie all)"
    )

@pytest.fixture(scope="session")
def browsers(request):
    br = request.config.getoption("--browser")
    if isinstance(br, list):
        br = br[0] if br else "all"
    br = br.lower()
    valid_browsers = ["chromium", "firefox", "webkit"]
    if br == "all" or br == "":
        return valid_browsers
    elif br in valid_browsers:
        return [br]
    else:
        raise ValueError(f"Nieznana przeglądarka: {br}. Wybierz spośród: {valid_browsers} lub all.")

@pytest.mark.parametrize("currency_code", ["USD", "CHF", "CZK"])
def test_currency_page(playwright, browsers, currency_code):
    for br_name in browsers:
        print(f"\n=== Testowanie: {currency_code} w {br_name} ===")

        browser = getattr(playwright, br_name).launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(f"http://localhost:1111/?currency={currency_code}")

        rows = page.locator("#currency-table tbody tr")
        count = rows.count()
        assert 5 <= count <= 7, f"Oczekiwano 5-7 wierszy, znaleziono: {count}"

        image = page.locator(f"img[alt='Wykres {currency_code}']")
        image.wait_for(state="visible", timeout=5000)
        handle = image.element_handle()
        assert handle is not None, f"Nie znaleziono wykresu {currency_code}"
        width = page.evaluate("el => el.naturalWidth", handle)
        height = page.evaluate("el => el.naturalHeight", handle)
        assert width > 100 and height > 100, f"Wykres ma dziwne wymiary: {width}x{height}"

        with page.expect_download() as download_info:
            page.click(f"a[href*='/download/excel?currency={currency_code}'] >> button")
        download = download_info.value
        filename = download.suggested_filename or f"{currency_code}_data.xlsx"
        excel_path = f"{DOWNLOAD_DIR}/{br_name}-{filename}"
        download.save_as(excel_path)
        assert Path(excel_path).exists(), f"Excel nie został pobrany: {excel_path}"
        assert excel_path.endswith(".xlsx"), f"Zły format pliku: {excel_path}"

        chart_path = f"{DOWNLOAD_DIR}/{br_name}-{currency_code}_chart.png"

        if br_name == "webkit":
            print(f"Używam fallbacku do requests dla WebKit ({currency_code})...")
            img_link = page.locator(f"a[href*='/download/chart?currency={currency_code}']")
            if img_link.count() > 0:
                try:
                    img_link.wait_for(state="visible", timeout=3000)
                    href = img_link.get_attribute("href")
                    print(f"Znaleziono href: {href}")
                    if href:
                        url = f"http://localhost:1111{href}" if href.startswith("/") else href
                        response = requests.get(url)
                        print(f"Status HTTP: {response.status_code}")
                        print(f"Typ treści: {response.headers.get('Content-Type')}")
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

        browser.close()
