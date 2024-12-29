import pytest
from web3 import Web3

from uniswap_universal_router_decoder import RouterCodec


rpc_endpoint_address = "https://ethereum-rpc.publicnode.com"


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
