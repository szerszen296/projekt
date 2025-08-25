import pytest
import os
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
    setup_browser,
    check_all_currency_options_present,
    check_all_time_options_present
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def test_open_currency_page_dynamic(page, dynamic_currency_codes):
    for currency_code in dynamic_currency_codes:
        url = f"http://localhost:1111/?currency={currency_code}"
        page.goto(url)
        assert_currency_page_loaded(page, currency_code)

def test_switch_page_dynamic(page, dynamic_currency_codes, extra):
    for currency_code in dynamic_currency_codes:
        switch_page(page, currency_code, extra=extra)

def test_switch_currency(page, browser_name, extra):
    switch_currency(page, browser_name, extra)

def test_switch_currency_and_time(page, browser_name, currency, week, extra):
    switch_currency_and_time(page, browser_name, currency, week, extra)

def test_switch_time(page, browser_name, dynamic_currency_codes, week, extra):
    for currency in dynamic_currency_codes:
        switch_time(page, browser_name, currency, week, extra)

def test_download_chart_for_week(page, browser_name, currency, week, extra):
    download_chart_for_currency_and_week(page, currency, week, browser_name, extra)

def test_download_excel_for_week(page, browser_name, currency, week, extra):
    download_excel_for_currency_and_week(page, currency, week, browser_name, extra)

def test_all_currency_options_present(page, currencies_number):
    check_all_currency_options_present(page, currencies_number)

def test_all_time_options_present(page, weeks_number):
    check_all_time_options_present(page, weeks_number)
