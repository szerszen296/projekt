import pytest

@pytest.fixture(params=["USD", "CHF", "CZK"])
def currency_code(request):
    return request.param

@pytest.fixture(params=["1", "4", "8"])
def week_value(request):
    return request.param

@pytest.fixture
def extra():
    return []
