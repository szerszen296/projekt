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

@pytest.fixture(scope="session", autouse=True)
def server():
    server_process = None
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

def test_open_currency_page(page, currency_code):
    url = f"http://localhost:1111/?currency={currency_code}"
    page.goto(url)
    assert_currency_page_loaded(page, currency_code)

def test_switch_page(page, currency_code, extra):
    switch_page(page, currency_code, extra=extra)

def test_switch_currency(playwright, browser_name, extra):
    switch_currency(playwright, browser_name, extra)

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

def test_switch_currency_and_time(playwright, browser_name, dynamic_currency_codes, dynamic_week_values, extra):
    for currency in dynamic_currency_codes:
        for week_value in dynamic_week_values:
            switch_currency_and_time(playwright, browser_name, currency, week_value, extra)

def test_switch_time(playwright, browser_name, dynamic_currency_codes, dynamic_week_values, extra):
    for currency in dynamic_currency_codes:
        for week_value in dynamic_week_values:
            switch_time(playwright, browser_name, currency, week_value, extra)

def test_download_excel_for_week(page, browser_name, dynamic_currency_codes, dynamic_week_values, extra):
    for currency in dynamic_currency_codes:
        for week_value in dynamic_week_values:
            download_excel_for_currency_and_week(page, currency, week_value, browser_name, extra)

def test_download_chart_for_week(page, browser_name, dynamic_currency_codes, dynamic_week_values, extra):
    for currency in dynamic_currency_codes:
        for week_value in dynamic_week_values:
            download_chart_for_currency_and_week(page, currency, week_value, browser_name, extra)

