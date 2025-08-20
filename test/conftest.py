import pytest
import shutil
import os
import subprocess
import signal
import time
from pathlib import Path

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


@pytest.fixture(autouse=True)
def clean_download_dir():
    """
    Przed każdym testem usuń zawartość katalogu downloads.
    """
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield



@pytest.fixture(params=["USD", "CHF", "CZK"])
def currency_code(request):
    return request.param

@pytest.fixture(params=["1", "4", "8"])
def week_value(request):
    return request.param

@pytest.fixture
def extra():
    return []
