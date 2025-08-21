import pytest
import os
from pathlib import Path
from pytest_html import extras

from helpers import (
    assert_currency_page_loaded,
    switch_page,
    switch_currency,
    switch_time,
    switch_currency_and_time,
    download_excel_for_currency_and_week,
    download_chart_for_currency_and_week,
    CURRENCIES,
    WEEK_VALUES,
    time_dropdown_has_8_weeks_option,
    currency_dropdown_has_all_expected_options
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

def test_switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra):
    switch_currency_and_time(playwright, browser_name, currency_code, week_value, extra)

def test_switch_time(playwright, browser_name, currency_code, week_value, extra):
    switch_time(playwright, browser_name, currency_code, week_value, extra)

@pytest.mark.parametrize("currency", CURRENCIES)
@pytest.mark.parametrize("week_value", WEEK_VALUES)
def test_download_excel_for_week(page, currency, week_value, browser_name, extra):
    download_excel_for_currency_and_week(page, currency, week_value, browser_name, extra)

@pytest.mark.parametrize("currency", CURRENCIES)
@pytest.mark.parametrize("week_value", WEEK_VALUES)
def test_download_chart_for_week(page, currency, week_value, browser_name, extra):
    download_chart_for_currency_and_week(page, currency, week_value, browser_name, extra)

def test_time_dropdown_has_8_weeks(playwright, browser_name):
    time_dropdown_has_8_weeks_option(playwright, browser_name)

def test_currency_dropdown_has_all_expected_options(playwright, browser_name):
    currency_dropdown_has_all_expected_options(playwright, browser_name)
