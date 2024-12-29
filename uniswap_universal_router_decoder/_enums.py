"""
Enums used by the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""


from enum import Enum

from web3 import Web3
from web3.types import Wei


class _RouterFunction(Enum):
    # https://docs.uniswap.org/contracts/universal-router/technical-reference#command
    V3_SWAP_EXACT_IN = 0
    V3_SWAP_EXACT_OUT = 1
    PERMIT2_TRANSFER_FROM = 2
    SWEEP = 4
    TRANSFER = 5
    PAY_PORTION = 6
    V2_SWAP_EXACT_IN = 8
    V2_SWAP_EXACT_OUT = 9
    PERMIT2_PERMIT = 10
    WRAP_ETH = 11
    UNWRAP_WETH = 12
    V4_SWAP = 16
    V4_INITIALIZE_POOL = 19
    V4_POSITION_MANAGER_CALL = 20


class FunctionRecipient(Enum):
    """
    SENDER: When the function recipient is the sender

    ROUTER: When the function recipient is the router

    CUSTOM: When the function recipient is neither the trx sender nor the router
    """
    SENDER = "recipient is transaction sender"
    ROUTER = "recipient is universal router"
    CUSTOM = "recipient is custom"


class _RouterConstant(Enum):
    # https://github.com/Uniswap/universal-router/blob/main/contracts/libraries/Constants.sol
    MSG_SENDER = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")
    ADDRESS_THIS = Web3.to_checksum_address("0x0000000000000000000000000000000000000002")
    ROUTER_BALANCE = Wei(2**255)
    FLAG_ALLOW_REVERT = 0x80
    COMMAND_TYPE_MASK = 0x3f


class TransactionSpeed(Enum):
    SLOW = 0
    AVERAGE = 1
    FAST = 2
    FASTER = 3


class _V4Actions(Enum):
    # https://github.com/Uniswap/v4-periphery/blob/main/src/libraries/Actions.sol
    # Positions
    MINT_POSITION = 0x02
    SETTLE_PAIR = 0x0d
    CLOSE_CURRENCY = 0x12
    SWEEP = 0x14
    UNWRAP = 0x16

    # Swaps
    SWAP_EXACT_IN_SINGLE = 0x06
    SETTLE_ALL = 0x0c
    TAKE_ALL = 0x0f

    # Common
    SETTLE = 0x0b


class V4Constants(Enum):
    OPEN_DELTA = 0
    CONTRACT_BALANCE = 0x8000000000000000000000000000000000000000000000000000000000000000
