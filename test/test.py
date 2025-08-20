import pytest
import os
from pathlib import Path
from pytest_html import extras

from helpers import (
    assert_currency_page_loaded,
    switch_page,
    switch_currency,
    download_excel,
    download_chart,
    switch_time,
    switch_currency_and_time,
    download_excel_for_currency_and_week,
    download_chart_for_currency_and_week
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def test_open_currency_page(page, currency_code):
    url = f"http://localhost:1111/?currency={currency_code}"
    page.goto(url)
    assert_currency_page_loaded(page, currency_code)


def test_switch_page(page, currency_code, extra):
    switch_page(page, currency_code, extra=extra)


def test_switch_currency(playwright, browser_name, extra):
    switch_currency(playwright, browser_name, extra)


def test_download_excel(page, currency_code, browser_name, extra):
    switch_page(page, currency_code, extra=extra)
    download_excel(page, browser_name, currency_code)

    filename = f"{browser_name}-{currency_code}_data.xlsx"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Excel"))


def test_download_chart(page, currency_code, browser_name, extra):
    switch_page(page, currency_code, extra=extra)
    download_chart(page, browser_name, currency_code)

    filename = f"{browser_name}-{currency_code}_chart.png"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if Path(filepath).exists():
        extra.append(extras.url(filepath, name=f"{currency_code} Wykres"))


def test_switch_time(page, currency_code, week_value, extra):
    switch_time(page, week_value, currency_code, extra=extra)


def test_switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra):
    switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra)


@pytest.mark.parametrize("currency", ["USD", "CHF", "CZK"])
def test_download_excel_8_weeks(page, currency, browser_name, extra):
    download_excel_for_currency_and_week(page, currency, "8", browser_name, extra)


@pytest.mark.parametrize("currency", ["USD", "CHF", "CZK"])
def test_download_chart_8_weeks(page, currency, browser_name, extra):
    download_chart_for_currency_and_week(page, currency, "8", browser_name, extra)
