import pytest
import shutil
import os
import subprocess
import signal
import time
import socket
from pathlib import Path
from helpers import (
    assert_currency_page_loaded,
    switch_page,
    switch_currency,
    switch_time,
    switch_currency_and_time,
    download_excel_for_currency_and_week,
    download_chart_for_currency_and_week,
    get_currency_options,
    get_time_options,
    select_three_options,
    setup_browser
)

DOWNLOAD_DIR = Path("downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def is_port_in_use(port):
    """Sprawdza, czy port jest już zajęty (czy serwer działa)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

server_process = None

@pytest.fixture(scope="session", autouse=True)
def server():
    global server_process
    port = 1111

    if not is_port_in_use(port):
        app_path = Path(__file__).parent.parent / "app.py"

        server_process = subprocess.Popen(
            ["python3", str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        time.sleep(2)

    yield

    if server_process:
        try:
            if os.name == 'nt':
                server_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            server_process.wait(timeout=5)
        except Exception as e:
            print(f"Nie udało się zatrzymać serwera: {e}")

@pytest.fixture(scope="session", autouse=True)
def ensure_download_dir():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session", autouse=True)
def clean_download_dir():
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield

@pytest.fixture(scope="session")
def dynamic_currency_codes(playwright, browser_name):
    browser, context, page = setup_browser(playwright, browser_name)
    values = get_currency_options(page)
    browser.close()
    return select_three_options(values)

@pytest.fixture(scope="session")
def dynamic_week_values(playwright, browser_name):
    browser, context, page = setup_browser(playwright, browser_name)
    values = get_time_options(page)
    browser.close()
    return select_three_options(values)

@pytest.fixture(scope="session")
def currency_options(playwright, browser_name):
    browser, context, page = setup_browser(playwright, browser_name)
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#currency")

    options = page.locator("#currency option")
    count = options.count()
    all_values = [options.nth(i).get_attribute("value") for i in range(count)]
    browser.close()

    return select_three_options(all_values)

@pytest.fixture(scope="session")
def time_options(playwright, browser_name):
    browser, context, page = setup_browser(playwright, browser_name)
    page.goto("http://localhost:1111/")
    page.wait_for_selector("#time")

    options = page.locator("#time option")
    count = options.count()
    all_values = [options.nth(i).get_attribute("value") for i in range(count)]
    browser.close()

    return select_three_options(all_values)

def select_three_options(options_list):
    if not options_list:
        return []
    first = options_list[0]
    middle = options_list[len(options_list) // 2]
    last = options_list[-1]
    return list(dict.fromkeys([first, middle, last]))

def pytest_generate_tests(metafunc):
    global server_process
    port = 1111

    if not is_port_in_use(port):
        app_path = Path(__file__).parent.parent / "app.py"
        server_process = subprocess.Popen(
            ["python3", str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        time.sleep(2)

    if "currency" in metafunc.fixturenames or "week" in metafunc.fixturenames:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto("http://localhost:1111/")

            if "currency" in metafunc.fixturenames:
                all_currency_options = get_currency_options(page)
                selected_currencies = select_three_options(all_currency_options)
                metafunc.parametrize("currency", selected_currencies)

            if "week" in metafunc.fixturenames:
                all_time_options = get_time_options(page)
                selected_weeks = select_three_options(all_time_options)
                metafunc.parametrize("week", selected_weeks)

            browser.close()

@pytest.fixture(scope="function")
def browser(playwright, browser_name):
    browser, context, page = setup_browser(playwright, browser_name)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    yield page
    context.close()
