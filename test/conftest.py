import pytest
import shutil
import os
import subprocess
import signal
import time
import socket
from pathlib import Path
from helpers import CURRENCIES, WEEK_VALUES

DOWNLOAD_DIR = Path("downloads")

def is_port_in_use(port):
    """Sprawdza, czy port jest już zajęty (czy serwer działa)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

@pytest.fixture(scope="session", autouse=True)
def server():
    server_process = None
    port = 1111

    if not is_port_in_use(port):
        # Ścieżka do pliku app.py (jest poziom wyżej niż katalog test)
        app_path = Path(__file__).parent.parent / "app.py"

        # Uruchom serwer
        server_process = subprocess.Popen(
            ["python3", str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        time.sleep(2)  # Poczekaj aż serwer wystartuje

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

@pytest.fixture(params=CURRENCIES)
def currency_code(request):
    return request.param

@pytest.fixture(params=WEEK_VALUES)
def week_value(request):
    return request.param

@pytest.fixture
def extra():
    return []
