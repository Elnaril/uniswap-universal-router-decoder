"""
Collection of utility functions used by the Uniswap Universal Router Codec

* Author: Elnaril (elnaril_dev@caramail.com, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from collections.abc import Sequence
from math import (
    ceil,
    floor,
    log10,
)
from statistics import quantiles
from typing import cast

from web3 import (
    AsyncHTTPProvider,
    AsyncWeb3,
    Web3,
)
from web3.types import (
    BlockData,
    BlockIdentifier,
    TxData,
    Wei,
)

from uniswap_universal_router_decoder._constants import (
    BASELOG,
    MAX_TICK,
    MIN_TICK,
    Q96,
)
from uniswap_universal_router_decoder._enums import TransactionSpeed


_speed_multiplier = {
    TransactionSpeed.SLOW: 1,
    TransactionSpeed.AVERAGE: 1,
    TransactionSpeed.FAST: 1.25,
    TransactionSpeed.FASTER: 1.5,
}


def compute_gas_fees(
        w3: Web3,
        trx_speed: TransactionSpeed = TransactionSpeed.FAST,
        block_identifier: BlockIdentifier = "latest") -> tuple[Wei, Wei]:
    """
    Compute the priority_fee (maxPriorityFeePerGas) and max_fee_per_gas (maxFeePerGas) according to the given
    transaction 'speed'. All speeds will compute gas fees in order to try to place the transaction in the next block
    (without certainty, of course).
    Higher speeds would place the transaction higher in the block than lower ones.
    So, during strained conditions, the computed gas fees could be very high and should be double-checked before
    using them.

    :param w3: valid Web3 instance
    :param trx_speed: the desired transaction 'speed'
    :param block_identifier: the block number or identifier, default to 'latest'
    :return: the tuple (priority_fee, max_fee_per_gas)
    """
    block = w3.eth.get_block(block_identifier, True)
    return _compute_gas_fees(block, trx_speed, block_identifier)


async def async_compute_gas_fees(
        async_w3: AsyncWeb3[AsyncHTTPProvider],
        trx_speed: TransactionSpeed = TransactionSpeed.FAST,
        block_identifier: BlockIdentifier = "latest") -> tuple[Wei, Wei]:
    """
    Asynchronously compute the priority_fee (maxPriorityFeePerGas) and max_fee_per_gas (maxFeePerGas)
    according to the given transaction 'speed'.
    All speeds will compute gas fees in order to try to place the transaction in the next block
    (without certainty, of course).
    Higher speeds would place the transaction higher in the block than lower ones.
    So, during strained conditions, the computed gas fees could be very high and should be double-checked before
    using them.

    :param w3: valid Web3 instance
    :param trx_speed: the desired transaction 'speed'
    :param block_identifier: the block number or identifier, default to 'latest'
    :return: the tuple (priority_fee, max_fee_per_gas)
    """
    block = await async_w3.eth.get_block(block_identifier, True)
    return _compute_gas_fees(block, trx_speed, block_identifier)


def _compute_gas_fees(
        block: BlockData,
        trx_speed: TransactionSpeed = TransactionSpeed.FAST,
        block_identifier: BlockIdentifier = "latest") -> tuple[Wei, Wei]:
    transactions = cast(Sequence[TxData], block.get("transactions", []))
    tips = [
        int(trx.get("maxPriorityFeePerGas", 0))
        for trx
        in transactions
        if trx.get("maxPriorityFeePerGas", 0) > 0
    ]
    if len(tips) < 3:
        priority_fee = 1
    else:
        quintiles = quantiles(tips, n=5, method="inclusive")
        priority_fee = int(quintiles[trx_speed.value] * _speed_multiplier[trx_speed])

    base_fee = block.get("baseFeePerGas")
    if not base_fee:
        raise ValueError(
            "Cannot compute gas fees because the retrieved block at block_identifier "
            f"= {block_identifier!r} does not contain 'baseFeePerGas'"
        )
    max_fee_per_gas = int(base_fee * 1.5 + priority_fee)

    return Wei(priority_fee), Wei(max_fee_per_gas)


def compute_sqrt_price_x96(amount_0: Wei, amount_1: Wei) -> int:
    """
    Compute the sqrtPriceX96

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param amount_0: amount of PoolKey.currency_0
    :param amount_1: amount of PoolKey.currency_1
    :returns: int(sqrt(amount_1 / amount_0) * 2^96)
    """
    return int(pow(amount_1 / amount_0, 1/2) * 2**96)


def convert_sqrt_price_x96(sqrt_price_x96: int) -> float:
    """
    Return the price

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param sqrt_price_x96: the sqrtPriceX96
    :returns: amount_1 / amount_0
    """
    return (sqrt_price_x96 / 2**96)**2


def sqrt_price_x96_to_floor_tick(sqrt_price_x96: int) -> int:
    """
    convert a sqrtPriceX96 to floor tick

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param sqrt_price_x96: the sqrtPriceX96

    :returns: the corresponding floor tick
    """
    return floor(log10((sqrt_price_x96 / Q96)**2) / BASELOG)


def tick_to_sqrt_price_x96(tick: int) -> int:
    """
    convert a tick to sqrtPriceX96

    ⚠️ Implementation is not the same as in the contract: expect discrepencies !

    :param tick: the given tick
    :returns: the sqrtPriceX96
    """
    if not MIN_TICK <= tick <= MAX_TICK:
        raise ValueError(f"Tick must be between {MIN_TICK} and {MAX_TICK}. Got: {tick}")
    return ceil((10**(BASELOG * tick))**(1/2) * Q96)


def tick_to_prices(tick: int, decimal_0: int, decimal_1: int) -> tuple[float, float]:
    """
    compute price_0 (with currency_0 as the quote currency) and price_1 (with currency_1 as the quote currency)
    at a given tick

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param tick: the given tick
    :param decimal_0: the number of currency_0's decimals
    :param decimal_1: the number of currency_1's decimals

    :returns: price_0, price_1
    """
    if not MIN_TICK <= tick <= MAX_TICK:
        raise ValueError(f"Tick must be between {MIN_TICK} and {MAX_TICK}. Got: {tick}")
    price_0 = (1.0001**tick)/(10**(decimal_1 - decimal_0))
    price_1 = 1 / price_0
    return price_0, price_1


def _price_0_to_tick_float(price_0: float, decimal_0: int, decimal_1: int) -> float:
    return log10(price_0 * (10**(decimal_1 - decimal_0))) / BASELOG


def price_0_to_closest_tick(price_0: float, decimal_0: int, decimal_1: int, tick_spacing: int) -> int:
    """
    compute the closest tick to a given price; useful to compute a price range lower and upper ticks

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param price_0: the price expressed with currency_0 as the quote currency
    :param decimal_0: the number of currency_0's decimals
    :param decimal_1: the number of currency_1's decimals
    :param tick_spacing: the pool tick spacing

    :returns: the closest tick
    """
    if price_0 <= 0:
        raise ValueError(f"Price must be strictly positive. Got {price_0}")
    tick_float = _price_0_to_tick_float(price_0, decimal_0, decimal_1)
    left_tick = int(tick_float // tick_spacing) * tick_spacing
    right_tick = left_tick + tick_spacing
    return left_tick if tick_float - left_tick < right_tick - tick_float else right_tick


# Liquidity computation heavily borrowed from:
# https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/libraries/LiquidityAmounts.sol#L56
def _compute_amount_0_liquidity(sqrt_price_x96_a: int, sqrt_price_x96_b: int, amount_0: Wei) -> int:
    # with sqrt_price_x96_a < sqrt_price_x96_b
    intermediate = sqrt_price_x96_a * sqrt_price_x96_b // Q96  # floor div
    return amount_0 * intermediate // (sqrt_price_x96_b - sqrt_price_x96_a)


def _compute_amount_1_liquidity(sqrt_price_x96_a: int, sqrt_price_x96_b: int, amount_1: Wei) -> int:
    # with sqrt_price_x96_a < sqrt_price_x96_b
    return amount_1 * Q96 // (sqrt_price_x96_b - sqrt_price_x96_a)  # floor div


def compute_liquidity(
        sqrt_price_x96: int,
        sqrt_price_x96_a: int,
        sqrt_price_x96_b: int,
        amount_0: Wei,
        amount_1: Wei) -> int:
    """
    Compute theoretical liquidity as used to mint positions.

    ⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts:
    if you want the exact same numbers, do not use them.

    :param sqrt_price_x96: the current sqrtPriceX96
    :param sqrt_price_x96_a: the left range boundary sqrtPriceX96
    :param sqrt_price_x96_b: the right range boundary sqrtPriceX96
    :param amount_0: the desired amount of currency_0 in Wei
    :param amount_1: the desired amount of currency_1 in Wei

    :returns: the computed theoretical liquidity
    """
    if sqrt_price_x96_a >= sqrt_price_x96_b:
        raise ValueError("sqrt_price_x96_a must be strictly less than sqrt_price_x96_b !")
    if sqrt_price_x96 <= sqrt_price_x96_a:
        return _compute_amount_0_liquidity(sqrt_price_x96_a, sqrt_price_x96_b, amount_0)
    elif sqrt_price_x96 < sqrt_price_x96_b:
        liquidity_0 = _compute_amount_0_liquidity(sqrt_price_x96, sqrt_price_x96_b, amount_0)
        liquidity_1 = _compute_amount_1_liquidity(sqrt_price_x96_a, sqrt_price_x96, amount_1)
        return liquidity_0 if liquidity_0 < liquidity_1 else liquidity_1
    else:
        return _compute_amount_1_liquidity(sqrt_price_x96_a, sqrt_price_x96_b, amount_1)
