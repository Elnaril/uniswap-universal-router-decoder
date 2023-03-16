import pytest

from uniswap_universal_router_decoder import RouterCodec


@pytest.fixture
def codec():
    return RouterCodec()
