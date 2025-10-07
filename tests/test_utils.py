import pytest
from web3.types import Wei

from uniswap_universal_router_decoder import TransactionSpeed
from uniswap_universal_router_decoder.utils import (
    compute_gas_fees,
    compute_sqrt_price_x96,
    convert_sqrt_price_x96,
)


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
    ),
)
def test_compute_gas_fees(trx_speed, block_identifier, expected_priority_fee, expected_max_fee_per_gas, w3):
    priority_fee, max_fee_per_gas = compute_gas_fees(w3, trx_speed, block_identifier)
    assert priority_fee == expected_priority_fee
    assert max_fee_per_gas == expected_max_fee_per_gas


@pytest.mark.parametrize(
    "sqrt_price_x96_input, expected_result",
    ((-1, 1.5930919111324523e-58), (0, 0.0), (1, 1.5930919111324523e-58), (79228162514264337593543950336, 1.0)),
)
def test_convert_sqrt_price_x96(sqrt_price_x96_input, expected_result):
    result = convert_sqrt_price_x96(sqrt_price_x96=sqrt_price_x96_input)
    assert result == expected_result


@pytest.mark.parametrize(
    "amount_0_input, amount_1_input, expected_result",
    (
        (Wei(1), Wei(0), 0),
        (Wei(1), Wei(1), 79228162514264337593543950336),
        (Wei(2), Wei(1), 56022770974786143748341366784),
        (Wei(2000000000000000000000000000000000000000000000000000000000), Wei(1), 1),
    ),
)
def test_compute_sqrt_price_x96(amount_0_input, amount_1_input, expected_result):
    result = compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)
    assert result == expected_result


@pytest.mark.parametrize("amount_0_input, amount_1_input", ((Wei(0), Wei(0)), (Wei(0), Wei(1))))
def test_compute_sqrt_price_x96_div_zero(amount_0_input, amount_1_input):
    with pytest.raises(ZeroDivisionError):
        compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)


@pytest.mark.parametrize("amount_0_input, amount_1_input", ((Wei(-1), Wei(1)), (Wei(1), Wei(-1))))
def test_compute_sqrt_price_x96_neg_wei(amount_0_input, amount_1_input):
    with pytest.raises(TypeError):
        compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)
