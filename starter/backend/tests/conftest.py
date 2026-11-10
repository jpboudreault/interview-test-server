import pytest

from tax_calculator import create_app
from tax_calculator.config import Config


class TestConfig(Config):
    TESTING = True
    TAX_API_URL = "http://tax-api.test"


@pytest.fixture
def client():
    return create_app(TestConfig).test_client()
