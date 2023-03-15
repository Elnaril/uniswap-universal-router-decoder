import pytest

from uniswap_universal_router_decoder.router_codec import RouterCodec


@pytest.fixture
def codec():
    return RouterCodec()
