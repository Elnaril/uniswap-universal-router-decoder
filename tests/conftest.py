import pytest
from web3 import (
    AsyncHTTPProvider,
    AsyncWeb3,
    Web3,
)

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    RouterCodec,
)


rpc_endpoint_address = "https://eth.drpc.org"


@pytest.fixture
def codec():
    return RouterCodec()


@pytest.fixture
def codec_rpc():
    return RouterCodec(rpc_endpoint=rpc_endpoint_address)


@pytest.fixture
def rpc_url():
    return rpc_endpoint_address


@pytest.fixture
def w3():
    return Web3(Web3.HTTPProvider(rpc_endpoint_address))


@pytest.fixture
def async_w3():
    return AsyncWeb3(AsyncHTTPProvider(rpc_endpoint_address))


@pytest.fixture
def async_codec():
    return AsyncRouterCodec()


@pytest.fixture
def async_codec_rpc():
    return AsyncRouterCodec(rpc_endpoint=rpc_endpoint_address)
