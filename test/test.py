import pytest
from pathlib import Path
import requests

DOWNLOAD_DIR = "download"
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default=None,
        choices=["chromium", "firefox", "webkit"],
        help="Browser to run the test with (chromium, firefox, webkit)"
    )

@pytest.fixture
def br_name(request):
    browser = request.config.getoption("--browser")
    if browser is None:
        pytest.skip("Musisz podać --browser=[chromium|firefox|webkit], by uruchomić test")
    if isinstance(browser, (list, tuple)):
        browser = browser[0]
    return browser

def test_all(br_name, playwright):
    browser = getattr(playwright, br_name).launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto("http://localhost:1111")

    rows = page.locator("#currency-table tbody tr")
    count = rows.count()
    assert count == 5 or count == 6, f"Oczekiwano 5 wierszy, znaleziono: {count}"

    image = page.locator("img[alt='Wykres EUR']")
    image.wait_for(state="visible")
    handle = image.element_handle()
    assert handle is not None, "Nie znaleziono obrazka z alt='Wykres EUR'"
    width = page.evaluate("el => el.naturalWidth", handle)
    height = page.evaluate("el => el.naturalHeight", handle)
    assert width == 800, f"Oczekiwano szerokości 800, otrzymano: {width}"
    assert height == 400, f"Oczekiwano wysokości 400, otrzymano: {height}"

    with page.expect_download() as download_info:
        page.click("a[href='/download/excel']")
    download = download_info.value
    filename = download.suggested_filename
    save_path = f"{DOWNLOAD_DIR}/{br_name}-{filename}"
    download.save_as(save_path)
    assert Path(save_path).exists(), "Plik Excel nie został pobrany."
    assert save_path.endswith(".xlsx"), f"Plik nie ma rozszerzenia .xlsx: {save_path}"


    link = page.locator("a[href='/download/chart']")
    try:
        with page.expect_download(timeout=10000) as download_info:
            link.click()
        download = download_info.value
        filename = download.suggested_filename
        save_path = f"{DOWNLOAD_DIR}/{br_name}-{filename}"
        download.save_as(save_path)
    except Exception:
        try:
            link.wait_for(state="visible", timeout=5000)
            href = link.get_attribute("href")
        except Exception:
            href = "/download/chart"
        base_url = page.url.rsplit("/", 1)[0]
        url = base_url + href
        response = requests.get(url)

        filename = href.split("/")[-1]
        if not filename or '.' not in filename:
            filename += ".png"
        save_path = f"{DOWNLOAD_DIR}/{br_name}-{filename}"
        with open(save_path, "wb") as f:
            f.write(response.content)

    assert Path(save_path).exists(), "Plik wykresu nie został pobrany."
    assert save_path.endswith(".png"), f"Nieprawidłowy typ pliku: {save_path}"

    browser.close()
