import pytest

from uniswap_universal_router_decoder import TransactionSpeed
from uniswap_universal_router_decoder.utils import compute_gas_fees


@pytest.mark.parametrize(
    "trx_speed, block_identifier, expected_priority_fee, expected_max_fee_per_gas",
    (
        (TransactionSpeed.SLOW, 19371376, 51749500, 267500297642),
        (TransactionSpeed.AVERAGE, 19371376, 1336613173, 268785161315),
        (TransactionSpeed.FAST, 19371376, 2500000000, 269948548142),
        (TransactionSpeed.FASTER, 19371376, 3000000000, 270448548142),
        (TransactionSpeed.FAST, 19874484, 2500000000, 11746497877),
        (TransactionSpeed.FASTER, 19874484, 3000000000, 12246497877),
        (TransactionSpeed.FAST, 12965000, 1, 1500000001),  # EIP-1559 went live at block 12965000
    )
)
def test_compute_gas_fees(trx_speed, block_identifier, expected_priority_fee, expected_max_fee_per_gas, w3):
    priority_fee, max_fee_per_gas = compute_gas_fees(w3, trx_speed, block_identifier)
    assert priority_fee == expected_priority_fee
    assert max_fee_per_gas == expected_max_fee_per_gas
