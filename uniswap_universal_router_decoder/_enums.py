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
    V2_SWAP_EXACT_IN = 8
    V2_SWAP_EXACT_OUT = 9
    PERMIT2_PERMIT = 10
    WRAP_ETH = 11
    UNWRAP_WETH = 12


class FunctionRecipient(Enum):
    SENDER = "recipient is transaction sender"
    ROUTER = "recipient is universal router"
    CUSTOM = "recipient is custom"


class _RouterConstant(Enum):
    # https://github.com/Uniswap/universal-router/blob/main/contracts/libraries/Constants.sol
    MSG_SENDER = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")
    ADDRESS_THIS = Web3.to_checksum_address("0x0000000000000000000000000000000000000002")
    ROUTER_BALANCE = Wei(2**255)
