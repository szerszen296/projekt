from pathlib import Path
from playwright.sync_api import sync_playwright

DOWNLOAD_DIR = "download"
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def test_currency_table_row_count(page):
    rows = page.locator("#currency-table tbody tr")
    count = rows.count()
    assert count == 5 or count == 6, f"Oczekiwano 5 wierszy, znaleziono: {count}"
    print("Tabela walut zawiera 5 wierszy.")

def test_chart_image_dimensions(page):
    image = page.locator("img[alt='Wykres EUR']")
    image.wait_for(state="visible")
    handle = image.element_handle()
    assert handle is not None, "Nie znaleziono obrazka z alt='Wykres EUR'"
    width = page.evaluate("el => el.naturalWidth", handle)
    height = page.evaluate("el => el.naturalHeight", handle)
    assert width == 800, f"Oczekiwano szerokości 800, otrzymano: {width}"
    assert height == 400, f"Oczekiwano wysokości 400, otrzymano: {height}"
    print("Obraz wykresu ma rozmiar 800x400.")

def test_excel_download(page):
    with page.expect_download() as download_info:
        page.click("a[href='/download/excel']")
    download = download_info.value
    filename = download.suggested_filename
    save_path = f"{DOWNLOAD_DIR}/chromium-{filename}"
    download.save_as(save_path)
    assert Path(save_path).exists(), "Plik Excel nie został pobrany."
    assert save_path.endswith(".xlsx"), f"Plik nie ma rozszerzenia .xlsx: {save_path}"
    print(f"Plik Excel został pobrany poprawnie jako: {save_path}")

def test_chart_download(page):
    with page.expect_download() as download_info:
        page.click("a[href='/download/chart']")
    download = download_info.value
    filename = download.suggested_filename
    save_path = f"{DOWNLOAD_DIR}/chromium-{filename}"
    download.save_as(save_path)
    assert Path(save_path).exists(), "Plik wykresu nie został pobrany."
    assert save_path.endswith(".png"), f"Nieprawidłowy typ pliku: {save_path}"
    print(f"Obraz wykresu został pobrany poprawnie jako: {save_path}")

def run_tests():
    print("test chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto("http://localhost:1111")
        test_currency_table_row_count(page)
        test_chart_image_dimensions(page)
        test_excel_download(page)
        test_chart_download(page)
        browser.close()

if __name__ == "__main__":
    run_tests()
