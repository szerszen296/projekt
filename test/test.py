import os
from playwright.sync_api import sync_playwright

def test_currency_table_row_count(page):
    rows = page.locator("#currency-table tbody tr")
    count = rows.count()
    assert count == 6, f"Oczekiwano 5 wierszy, znaleziono: {count}"
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
    tmp_path = download.path()
    assert tmp_path and os.path.exists(tmp_path), "Plik Excel nie został pobrany."
    filename = download.suggested_filename
    assert filename.endswith(".xlsx"), f"Plik nie ma rozszerzenia .xlsx: {filename}"
    print(f"Plik Excel został pobrany poprawnie jako: {filename}")

def test_chart_download(page):
    with page.expect_download() as download_info:
        page.click("a[href='/download/chart']")
    download = download_info.value
    tmp_path = download.path()
    assert tmp_path and os.path.exists(tmp_path), "Plik wykresu nie został pobrany."
    filename = download.suggested_filename
    assert any(filename.endswith(ext) for ext in [".png"]), f"Nieprawidłowy typ pliku: {filename}"
    print(f"Obraz wykresu został pobrany poprawnie jako: {filename}")

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless=True dla Linux
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto("http://localhost:1111", wait_until="networkidle")
        test_currency_table_row_count(page)
        test_chart_image_dimensions(page)
        test_excel_download(page)
        test_chart_download(page)
        browser.close()

if __name__ == "__main__":
    run_tests()
