import pytest
from web3.types import Wei

from uniswap_universal_router_decoder import TransactionSpeed
from uniswap_universal_router_decoder._constants import (
    MAX_TICK,
    MIN_SQRT_PRICE,
    MIN_TICK,
)
from uniswap_universal_router_decoder.utils import (
    compute_gas_fees,
    compute_liquidity,
    compute_sqrt_price_x96,
    convert_sqrt_price_x96,
    price_0_to_closest_tick,
    sqrt_price_x96_to_floor_tick,
    tick_to_prices,
    tick_to_sqrt_price_x96,
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
    )
)
def test_compute_gas_fees(trx_speed, block_identifier, expected_priority_fee, expected_max_fee_per_gas, w3):
    priority_fee, max_fee_per_gas = compute_gas_fees(w3, trx_speed, block_identifier)
    assert priority_fee == expected_priority_fee
    assert max_fee_per_gas == expected_max_fee_per_gas


def test_compute_gas_fees_exception(w3, mocker):
    mocker.patch.object(
            w3.eth,
            'get_block',
            return_value={}
        )
    with pytest.raises(ValueError):
        compute_gas_fees(w3)


@pytest.mark.parametrize(
    'sqrt_price_x96_input, expected_result',
    (
        (-1, 1.5930919111324523e-58),
        (0, 0.0),
        (1, 1.5930919111324523e-58),
        (79228162514264337593543950336, 1.0)
    )
)
def test_convert_sqrt_price_x96(sqrt_price_x96_input, expected_result):
    result = convert_sqrt_price_x96(sqrt_price_x96=sqrt_price_x96_input)
    assert result == expected_result


@pytest.mark.parametrize(
    'amount_0_input, amount_1_input, expected_result',
    (
        (Wei(1), Wei(0), 0),
        (Wei(1), Wei(1), 79228162514264337593543950336),
        (Wei(2), Wei(1), 56022770974786143748341366784),
        (Wei(2000000000000000000000000000000000000000000000000000000000), Wei(1), 1)
    )
)
def test_compute_sqrt_price_x96(amount_0_input, amount_1_input, expected_result):
    result = compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)
    assert result == expected_result


@pytest.mark.parametrize(
    'amount_0_input, amount_1_input',
    (
        (Wei(0), Wei(0)),
        (Wei(0), Wei(1))
    )
)
def test_compute_sqrt_price_x96_div_zero(amount_0_input, amount_1_input):
    with pytest.raises(ZeroDivisionError):
        compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)


@pytest.mark.parametrize(
    'amount_0_input, amount_1_input',
    (
        (Wei(-1), Wei(1)),
        (Wei(1), Wei(-1))
    )
)
def test_compute_sqrt_price_x96_neg_wei(amount_0_input, amount_1_input):
    with pytest.raises(TypeError):
        compute_sqrt_price_x96(amount_0=amount_0_input, amount_1=amount_1_input)


def test_sqrt_price_x96_to_floor_tick():
    tick = -322379
    sqrt_price_x96 = 7922816251426433400832
    assert sqrt_price_x96_to_floor_tick(sqrt_price_x96) == tick


@pytest.mark.parametrize(
    'tick, expected_sqrt_price_x96, expected_exception',
    (
        (
            MIN_TICK,
            MIN_SQRT_PRICE,
            None,
        ),
        (
            MIN_TICK + 1,
            4295343490,
            None,
        ),
        (
            -322900,
            7718727949420559597568,
            None,
        ),
        (
            MIN_TICK - 1,
            None,
            ValueError,
        ),
        (
            MAX_TICK + 1,
            None,
            ValueError,
        ),
    )
)
def test_tick_to_sqrt_price_x96(tick, expected_sqrt_price_x96, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            tick_to_sqrt_price_x96(tick)
    else:
        assert expected_sqrt_price_x96 == tick_to_sqrt_price_x96(tick)


@pytest.mark.parametrize(
    'tick, decimal_0, decimal_1, rounding_digits, expected_price_0, expected_exception',
    (
        (
            -322900,
            18,
            8,
            6,
            9.5e-05,
            None,
        ),
        (
            -321900,
            18,
            8,
            6,
            10.5e-05,
            None,
        ),
        (
            MIN_TICK - 1,
            18,
            8,
            6,
            None,
            ValueError,
        ),
        (
            MAX_TICK + 1,
            18,
            8,
            6,
            None,
            ValueError,
        ),
    )
)
def test_tick_to_prices(tick, decimal_0, decimal_1, rounding_digits, expected_price_0, expected_exception):
    if expected_exception:
        with pytest.raises(ValueError):
            tick_to_prices(tick, decimal_0, decimal_1)
    else:
        price_0, _ = tick_to_prices(tick, decimal_0, decimal_1)
        assert round(price_0, rounding_digits) == expected_price_0


@pytest.mark.parametrize(
    'price_0, decimal_0, decimal_1, tick_spacing, expected_tick, expected_exception',
    (
        (
            0.95e-4,
            18,
            8,
            50,
            -322900,
            None,
        ),
        (
            1.05e-4,
            18,
            8,
            50,
            -321900,
            None,
        ),
        (
            -1,
            18,
            8,
            50,
            None,
            ValueError,
        ),
    )
)
def test_price_0_to_closest_tick(price_0, decimal_0, decimal_1, tick_spacing, expected_tick, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            price_0_to_closest_tick(price_0, decimal_0, decimal_1, tick_spacing)
    else:
        assert expected_tick == price_0_to_closest_tick(price_0, decimal_0, decimal_1, tick_spacing)


# Liquidity unit tests heavily borrowed from:
# https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/test/LiquidityAmounts.spec.ts#L32
@pytest.mark.parametrize(
    'sqrt_price_x96, sqrt_price_x96_a, sqrt_price_x96_b, amount_0, amount_1, expected_liquidity, expected_error',
    (
        (
            compute_sqrt_price_x96(Wei(1), Wei(1)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            Wei(100),
            Wei(200),
            2148,
            ValueError,
        ),
        (
            compute_sqrt_price_x96(Wei(1), Wei(1)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            Wei(100),
            Wei(200),
            2148,
            None,
        ),
        (
            compute_sqrt_price_x96(Wei(110), Wei(99)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            Wei(100),
            Wei(200),
            1048,
            None,
        ),
        (
            compute_sqrt_price_x96(Wei(100), Wei(111)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            Wei(100),
            Wei(200),
            2097,
            None,
        ),
        (
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            Wei(100),
            Wei(200),
            1048,
            None,
        ),
        (
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            compute_sqrt_price_x96(Wei(110), Wei(100)),
            compute_sqrt_price_x96(Wei(100), Wei(110)),
            Wei(100),
            Wei(200),
            2097,
            None,
        ),
    )
)
def test_compute_liquidity(
        sqrt_price_x96,
        sqrt_price_x96_a,
        sqrt_price_x96_b,
        amount_0,
        amount_1,
        expected_liquidity,
        expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            compute_liquidity(
                sqrt_price_x96,
                sqrt_price_x96_a,
                sqrt_price_x96_b,
                amount_0,
                amount_1,
            )
    else:
        assert expected_liquidity == compute_liquidity(
            sqrt_price_x96,
            sqrt_price_x96_a,
            sqrt_price_x96_b,
            amount_0,
            amount_1,
        )
