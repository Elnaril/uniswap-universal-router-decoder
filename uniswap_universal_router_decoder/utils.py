from statistics import quantiles
from typing import (
    cast,
    Sequence,
    Tuple,
)

from web3 import Web3
from web3.types import (
    BlockIdentifier,
    TxData,
    Wei,
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
        block_identifier: BlockIdentifier = "latest") -> Tuple[Wei, Wei]:
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
    transactions = cast(Sequence[TxData], block["transactions"])
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

    base_fee = block["baseFeePerGas"]
    max_fee_per_gas = int(base_fee * 1.5 + priority_fee)

    return Wei(priority_fee), Wei(max_fee_per_gas)
