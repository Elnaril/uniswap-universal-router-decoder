import asyncio
import json

import aiohttp
import pytest
import requests
from web3 import (
    AsyncHTTPProvider,
    AsyncWeb3,
    Web3,
)
from web3.providers.rpc.utils import ExceptionRetryConfiguration

from uniswap_universal_router_decoder import (
    AsyncRouterCodec,
    RouterCodec,
)


rpc_endpoint_address = "https://mainnet.gateway.tenderly.co"


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
    retry_config = ExceptionRetryConfiguration(
        errors=(json.decoder.JSONDecodeError, ConnectionError, requests.HTTPError, requests.Timeout,),
        retries=10,
    )
    return Web3(Web3.HTTPProvider(rpc_endpoint_address, exception_retry_configuration=retry_config))


@pytest.fixture
def async_w3():
    retry_config = ExceptionRetryConfiguration(
        errors=(json.decoder.JSONDecodeError, ConnectionError, aiohttp.ClientError, asyncio.TimeoutError,),
        retries=10,
    )
    return AsyncWeb3(AsyncHTTPProvider(rpc_endpoint_address, exception_retry_configuration=retry_config))


@pytest.fixture
def async_codec():
    return AsyncRouterCodec()


@pytest.fixture
def async_codec_rpc():
    return AsyncRouterCodec(rpc_endpoint=rpc_endpoint_address)
