import pytest
import shutil
import os
import subprocess
import signal
import time
from pathlib import Path
from helpers import SUPPORTED_CURRENCIES, SUPPORTED_WEEK_VALUES

DOWNLOAD_DIR = Path("downloads")

@pytest.fixture(scope="session", autouse=True)
def server():
    proc = subprocess.Popen(
        ["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    time.sleep(2)
    yield
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    proc.wait()

@pytest.fixture(scope="session", autouse=True)
def ensure_download_dir():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session", autouse=True)
def clean_download_dir():
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield

@pytest.fixture(params=SUPPORTED_CURRENCIES)
def currency_code(request):
    return request.param

@pytest.fixture(params=SUPPORTED_WEEK_VALUES)
def week_value(request):
    return request.param

@pytest.fixture
def extra():
    return []
