import pytest
from web3 import Web3


def test_get_default_deadline(codec):
    assert 79 < codec.get_default_deadline() - codec.get_default_deadline(100) < 81


def test_get_default_expiration(codec):
    assert -1 < codec.get_default_expiration() - codec.get_default_expiration(30*24*3600) < 1


def test_get_max_expiration(codec):
    assert codec.get_max_expiration() == 2**48 - 1


@pytest.mark.parametrize(
    "wallet, token, block_identifier, expected_result",
    (
        (Web3.to_checksum_address('0x1944922D86209F7e5F3c88F2B2b4A8e737BeA9b1'), Web3.to_checksum_address('0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'), 19881602, (1461501637330902918203684832716283019655932542975, 1718529375, 1)),  # noqa
        (Web3.to_checksum_address('0x1944922D86209F7e5F3c88F2B2b4A8e737BeA9b1'), Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'), 19881602, (0, 0, 0)),  # noqa
    )
)
def test_fetch_permit2_allowance(wallet, token, block_identifier, expected_result, codec_rpc):
    amount, expiration, nonce = codec_rpc.fetch_permit2_allowance(wallet, token, block_identifier=block_identifier)
    assert (amount, expiration, nonce) == expected_result
