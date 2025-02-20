"""
Encoding part of the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from abc import ABC
from typing import (
    Any,
    cast,
    Dict,
    List,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
)

from eth_account.account import SignedMessage
from eth_utils import keccak
from web3 import Web3
from web3.types import (
    BlockIdentifier,
    ChecksumAddress,
    HexStr,
    Nonce,
    TxParams,
    Wei,
)

from uniswap_universal_router_decoder._abi_builder import ABIMap
from uniswap_universal_router_decoder._constants import (
    _router_abi,
    _ur_address,
)
from uniswap_universal_router_decoder._enums import (
    _RouterConstant,
    FunctionRecipient,
    MiscFunctions,
    RouterFunction,
    TransactionSpeed,
    V4Actions,
)
from uniswap_universal_router_decoder.utils import (
    compute_gas_fees,
    compute_sqrt_price_x96,
)


NO_REVERT_FLAG = _RouterConstant.FLAG_ALLOW_REVERT.value


class PoolKey(TypedDict):
    """
    Use v4_pool_key() to make sure currency_0 < currency_1
    """
    currency_0: ChecksumAddress
    currency_1: ChecksumAddress
    fee: int
    tick_spacing: int
    hooks: ChecksumAddress


class PathKey(TypedDict):
    intermediate_currency: ChecksumAddress
    fee: int
    tick_spacing: int
    hooks: ChecksumAddress
    hook_data: bytes


class _Encoder:
    def __init__(self, w3: Web3, abi_map: ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map

    @staticmethod
    def v3_path(v3_fn_name: str, path_seq: Sequence[Union[int, ChecksumAddress]]) -> bytes:
        """
        Encode a V3 path
        :param v3_fn_name: 'V3_SWAP_EXACT_IN' or 'V3_SWAP_EXACT_OUT'
        :param path_seq: a sequence of token addresses with the pool fee in between, ex: [tk_in_addr, fee, tk_out_addr]
        :return: the encoded V3 path
        """
        if len(path_seq) < 3:
            raise ValueError("Invalid list to encode a V3 path. Must have at least 3 parameters")
        path_list = list(path_seq)
        if v3_fn_name == "V3_SWAP_EXACT_OUT":
            path_list.reverse()
        elif v3_fn_name != "V3_SWAP_EXACT_IN":
            raise ValueError("v3_fn_name must be in ('V3_SWAP_EXACT_IN', 'V3_SWAP_EXACT_OUT')")
        path = "0x"
        for i, item in enumerate(path_list):
            if i % 2 == 0:
                _item = Web3.to_checksum_address(cast(ChecksumAddress, item))[2:]
            else:
                _item = f"{item:06X}"
            path += _item
        return Web3.to_bytes(hexstr=HexStr(path))

    @staticmethod
    def v4_pool_key(
            currency_0: Union[str, HexStr, ChecksumAddress],
            currency_1: Union[str, HexStr, ChecksumAddress],
            fee: int,
            tick_spacing: int,
            hooks: Union[str, HexStr, ChecksumAddress] = "0x0000000000000000000000000000000000000000") -> PoolKey:
        """
        Make sure currency_0 < currency_1 and returns the v4 pool key

        :param currency_0: the address of one token, or "0x0000000000000000000000000000000000000000" for ETH
        :param currency_1: the address of the other token, or "0x0000000000000000000000000000000000000000" for ETH
        :param fee: pool fee in percentage * 10000 (ex: 3000 for 0.3%)
        :param tick_spacing: granularity of the pool. Lower values are more precise but more expensive to trade
        :param hooks: hook address, default is no hooks, ie "0x0000000000000000000000000000000000000000"
        :return: the v4 pool key
        """
        if int(currency_0, 16) > int(currency_1, 16):
            currency_0, currency_1 = currency_1, currency_0
        return PoolKey(
            currency_0=Web3.to_checksum_address(currency_0),
            currency_1=Web3.to_checksum_address(currency_1),
            fee=int(fee),
            tick_spacing=int(tick_spacing),
            hooks=Web3.to_checksum_address(hooks),
        )

    def v4_pool_id(self, pool_key: PoolKey) -> bytes:
        """
        Encode the pool id

        :param pool_key: the PoolKey (see v4_pool_key() to get it)
        :return: the pool id
        """
        args = (tuple(pool_key.values()), )
        abi = self._abi_map[MiscFunctions.V4_POOL_ID]
        return keccak(abi.encode(args))

    @staticmethod
    def v4_path_key(
            intermediate_currency: ChecksumAddress,
            fee: int,
            tick_spacing: int,
            hooks: Union[str, HexStr, ChecksumAddress] = "0x0000000000000000000000000000000000000000",
            hook_data: bytes = b"") -> PathKey:
        """
        Build a PathKey which is used by multi-hop swap encoding

        :param intermediate_currency: the address of one token of the target pool
        :param fee: pool fee in percentage * 10000 (ex: 3000 for 0.3%)
        :param tick_spacing: granularity of the pool. Lower values are more precise but more expensive to trade
        :param hooks: hook address, default is no hooks, ie "0x0000000000000000000000000000000000000000"
        :param hook_data: encoded hook data
        :return: the corresponding PathKey
        """
        return PathKey(
            intermediate_currency=Web3.to_checksum_address(intermediate_currency),
            fee=int(fee),
            tick_spacing=int(tick_spacing),
            hooks=Web3.to_checksum_address(hooks),
            hook_data=hook_data,
        )

    def chain(self) -> _ChainedFunctionBuilder:
        """
        :return: Initialize the chain of encoded functions
        """
        return _ChainedFunctionBuilder(self._w3, self._abi_map)


TV4ChainedCommonFunctionBuilder = TypeVar("TV4ChainedCommonFunctionBuilder", bound="_V4ChainedCommonFunctionBuilder")


class _V4ChainedCommonFunctionBuilder(ABC):
    def __init__(self, builder: _ChainedFunctionBuilder, w3: Web3, abi_map: ABIMap):
        self.builder = builder
        self._w3 = w3
        self._abi_map = abi_map
        self.actions: bytearray = bytearray()
        self.arguments: List[bytes] = []

    def _add_action(self, action: V4Actions, args: Sequence[Any]) -> None:
        abi = self._abi_map[action]
        self.actions.append(action.value)
        self.arguments.append(abi.encode(args))

    def settle(
            self: TV4ChainedCommonFunctionBuilder,
            currency: ChecksumAddress,
            amount: int,
            payer_is_user: bool) -> TV4ChainedCommonFunctionBuilder:
        """
        Pay the contract for a given amount of tokens (currency). Used for swaps and position management.

        :param currency: The token addr or "0x0000000000000000000000000000000000000000" for the native currency (ie ETH)
        :param amount: The amount to send to the contract
        :param payer_is_user: Whether this amount comes from the transaction sender or not.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, amount, payer_is_user)
        self._add_action(V4Actions.SETTLE, args)
        return self

    def take(
            self: TV4ChainedCommonFunctionBuilder,
            currency: ChecksumAddress,
            recipient: ChecksumAddress,
            amount: int) -> TV4ChainedCommonFunctionBuilder:
        """
        Get the given amount of tokens (currency) from the contract. Used for swaps and position management.

        :param currency: The token addr or "0x0000000000000000000000000000000000000000" for the native currency (ie ETH)
        :param recipient: Address of who gets the tokens
        :param amount: The token amount to get
        :return: The chain link corresponding to this function call.
        """
        args = (currency, recipient, amount)
        self._add_action(V4Actions.TAKE, args)
        return self


class _V4ChainedPositionFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def mint_position(
            self,
            pool_key: PoolKey,
            tick_lower: int,
            tick_upper: int,
            liquidity: int,
            amount_0_max: int,
            amount_1_max: int,
            recipient: ChecksumAddress,
            hook_data: bytes) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Mint a V4 position, ie add some liquidity to a given pool and get a position as ERC-721 token.

        :param pool_key: The PoolKey to identify the pool where the liquidity will be added to.
        :param tick_lower: The lower tick boundary of the position
        :param tick_upper: The upper tick boundary of the position
        :param liquidity: The amount of liquidity units to mint
        :param amount_0_max: The maximum amount of currency_0 the sender is willing to pay
        :param amount_1_max: The maximum amount of currency_1 the sender is willing to pay
        :param recipient: The address that will receive the liquidity position (ERC-721)
        :param hook_data: The encoded hook data to be forwarded to the hook functions
        :return: The chain link corresponding to this function call.
        """
        args = (
            tuple(pool_key.values()),
            tick_lower,
            tick_upper,
            liquidity,
            amount_0_max,
            amount_1_max,
            recipient,
            hook_data
        )
        self._add_action(V4Actions.MINT_POSITION, args)
        return self

    def settle_pair(
            self,
            currency_0: ChecksumAddress,
            currency_1: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Indicates that tokens are to be paid by the caller to create the position.

        :param currency_0: The address of 1 token
        :param currency_1: The address of the other token
        :return: The chain link corresponding to this function call.
        """
        args = (currency_0, currency_1)
        self._add_action(V4Actions.SETTLE_PAIR, args)
        return self

    def close_currency(self, currency: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Automatically determines if a currency should be settled or taken.

        :param currency: The token or ETH to be paid or received.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, )
        self._add_action(V4Actions.CLOSE_CURRENCY, args)
        return self

    def sweep(self, currency: ChecksumAddress, to: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Sweep the contract

        :param currency: The token or ETH address to sweep
        :param to: The sweep recipient address
        :return: The chain link corresponding to this function call.
        """
        args = (currency, to)
        self._add_action(V4Actions.SWEEP, args)
        return self

    # def mint_position_from_deltas(
    #         self,
    #         pool_key: PoolKey,
    #         tick_lower: int,
    #         tick_upper: int,
    #         amount_0_max: int,
    #         amount_1_max: int,
    #         recipient: ChecksumAddress,
    #         hook_data: bytes) -> _V4ChainedPositionFunctionBuilder:
    #     args = (
    #         tuple(pool_key.values()),
    #         tick_lower,
    #         tick_upper,
    #         amount_0_max,
    #         amount_1_max,
    #         recipient,
    #         hook_data
    #     )
    #     self._add_action(V4Actions.MINT_POSITION_FROM_DELTAS, args)
    #     return self

    def wrap_eth(self, amount: Wei) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Encode the call to the function WRAP which convert ETH to WETH in the position manager contract

        :param amount: The amount of ETH in Wei.
        :return: The chain link corresponding to this function call.
        """
        args = (amount, )
        self._add_action(V4Actions.WRAP, args)
        return self

    def unwrap_weth(self, amount: Wei) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - Encode the call to the function UNWRAP which convert WETH to ETH in the position manager contract

        :param amount: The amount of WETH in Wei.
        :return: The chain link corresponding to this function call.
        """
        args = (amount, )
        self._add_action(V4Actions.UNWRAP, args)
        return self

    def take_pair(
            self,
            currency_0: ChecksumAddress,
            currency_1: ChecksumAddress,
            recipient: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        args = (currency_0, currency_1, recipient)
        self._add_action(V4Actions.TAKE_PAIR, args)
        return self

    def clear_or_take(
            self,
            currency: ChecksumAddress,
            amount_max: int) -> _V4ChainedPositionFunctionBuilder:
        """
        Position - If the token amount to-be-collected is below a threshold, opt to forfeit the dust.
        Otherwise, claim the tokens.

        :param currency: The token or ETH address to be forfeited or claimed.
        :param amount_max: The threshold.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, amount_max)
        self._add_action(V4Actions.CLEAR_OR_TAKE, args)
        return self

    def build_v4_posm_call(self, deadline: int) -> _ChainedFunctionBuilder:
        """
        Position - Build the V4 position manager call

        :param deadline: When this call is not valid anymore
        :return: The chain link corresponding to this function call.
        """
        action_values = (bytes(self.actions), self.arguments)
        abi = self._abi_map[MiscFunctions.UNLOCK_DATA]
        encoded_data = abi.encode(action_values)
        args = (encoded_data, deadline)
        self.builder._add_command(RouterFunction.V4_POSITION_MANAGER_CALL, args, True)
        return self.builder


class _V4ChainedSwapFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def swap_exact_in_single(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_in: Wei,
            amount_out_min: Wei,
            hook_data: bytes = b'') -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Encode the call to the V4_SWAP function SWAP_EXACT_IN_SINGLE.

        :param pool_key: the target pool key returned by encode.v4_pool_key()
        :param zero_for_one: the swap direction, true for currency_0 to currency_1, false for currency_1 to currency_0
        :param amount_in: the exact amount of the sold currency in Wei
        :param amount_out_min: the minimum accepted bought currency
        :param hook_data: encoded data sent to the pool's hook, if any.
        :return: The chain link corresponding to this function call.
        """
        args = ((tuple(pool_key.values()), zero_for_one, amount_in, amount_out_min, hook_data),)
        self._add_action(V4Actions.SWAP_EXACT_IN_SINGLE, args)
        return self

    def take_all(self, currency: ChecksumAddress, min_amount: Wei) -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Final action that collects all output tokens after the swap is complete.

        :param currency: The address of the token or ETH ("0x0000000000000000000000000000000000000000") to receive
        :param min_amount: The expected minimum amount to be received.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, min_amount)
        self._add_action(V4Actions.TAKE_ALL, args)
        return self

    def settle_all(self, currency: ChecksumAddress, max_amount: Wei) -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Final action that ensures all input tokens involved in the swap are properly paid to the contract.

        :param currency: The address of the token or ETH ("0x0000000000000000000000000000000000000000") to pay.
        :param max_amount: The expected maximum amount to pay.
        :return: The chain link corresponding to this function call.
        """
        args = (currency, max_amount)
        self._add_action(V4Actions.SETTLE_ALL, args)
        return self

    def swap_exact_in(
            self,
            currency_in: ChecksumAddress,
            path_keys: Sequence[PathKey],
            amount_in: int,
            amount_out_min: int) -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Encode Multi-hop V4 SWAP_EXACT_IN swaps.

        :param currency_in: The address of the token (or ETH) to send to the first pool.
        :param path_keys: The sequence of path keys to identify the pools
        :param amount_in: The amount to send to the contract
        :param amount_out_min: The expected minimum amount to be received
        :return: The chain link corresponding to this function call.
        """
        args = ((currency_in, [tuple(path_key.values()) for path_key in path_keys], amount_in, amount_out_min), )
        self._add_action(V4Actions.SWAP_EXACT_IN, args)
        return self

    def swap_exact_out_single(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_out: Wei,
            amount_in_max: Wei,
            hook_data: bytes = b'') -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Encode the call to the V4_SWAP function SWAP_EXACT_IN_SINGLE.

        :param pool_key: the target pool key returned by encode.v4_pool_key()
        :param zero_for_one: the swap direction, true for currency_0 to currency_1, false for currency_1 to currency_0
        :param amount_out: the exact amount of the bought currency in Wei
        :param amount_in_max: the maximum accepted sold currency
        :param hook_data: encoded data sent to the pool's hook, if any.
        :return: The chain link corresponding to this function call.
        """
        args = ((tuple(pool_key.values()), zero_for_one, amount_out, amount_in_max, hook_data),)
        self._add_action(V4Actions.SWAP_EXACT_OUT_SINGLE, args)
        return self

    def swap_exact_out(
            self,
            currency_out: ChecksumAddress,
            path_keys: Sequence[PathKey],
            amount_out: int,
            amount_in_max: int) -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Encode Multi-hop V4 SWAP_EXACT_OUT swaps.

        :param currency_out: The address of the token (or ETH) to be received
        :param path_keys: The sequence of path keys to identify the pools
        :param amount_out: The amount to be received
        :param amount_in_max: The maximum amount that the transaction sender is willing to pay.
        :return: The chain link corresponding to this function call.
        """
        args = ((currency_out, [tuple(path_key.values()) for path_key in path_keys], amount_out, amount_in_max), )
        self._add_action(V4Actions.SWAP_EXACT_OUT, args)
        return self

    def take_portion(
            self,
            currency: ChecksumAddress,
            recipient: ChecksumAddress,
            bips: int) -> _V4ChainedSwapFunctionBuilder:
        """
        Swap - Send a portion of token to a given recipient.

        :param currency: The address of the token (or ETH) to use for this action
        :param recipient: The address which will receive the tokens
        :param bips: The recipient will receive balance * bips / 10_000
        :return: The chain link corresponding to this function call.
        """
        args = (currency, recipient, bips)
        self._add_action(V4Actions.TAKE_PORTION, args)
        return self

    def build_v4_swap(self) -> _ChainedFunctionBuilder:
        """
        Build the V4 swap call

        :return: The chain link corresponding to this function call.
        """
        args = (bytes(self.actions), self.arguments)
        self.builder._add_command(RouterFunction.V4_SWAP, args)
        return self.builder


class _ChainedFunctionBuilder:
    def __init__(self, w3: Web3, abi_map: ABIMap):
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self.commands: bytearray = bytearray()
        self.arguments: List[bytes] = []

    def _add_command(self, command: RouterFunction, args: Sequence[Any], add_selector: bool = False) -> None:
        abi = self._abi_map[command]
        self.commands.append(command.value)
        arguments = abi.get_selector() + abi.encode(args) if add_selector else abi.encode(args)
        self.arguments.append(arguments)

    @staticmethod
    def _get_recipient(
            function_recipient: FunctionRecipient,
            custom_recipient: Optional[ChecksumAddress] = None) -> ChecksumAddress:
        recipient_mapping = {
            FunctionRecipient.SENDER: _RouterConstant.MSG_SENDER.value,
            FunctionRecipient.ROUTER: _RouterConstant.ADDRESS_THIS.value,
            FunctionRecipient.CUSTOM: custom_recipient,
        }
        recipient = recipient_mapping[function_recipient]
        if recipient:
            return Web3.to_checksum_address(recipient)
        else:
            raise ValueError(
                f"Invalid function_recipient: {function_recipient} or custom_recipient: {custom_recipient}: "
                f"custom_recipient address must be provided if FunctionRecipient.CUSTOM is selected."
            )

    @staticmethod
    def _get_command(router_function: RouterFunction, revert_on_fail: bool) -> int:
        return int(router_function.value if revert_on_fail else router_function.value | NO_REVERT_FLAG)

    def wrap_eth(
            self,
            function_recipient: FunctionRecipient,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function WRAP_ETH which convert ETH to WETH through the UR

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount: The amount of sent ETH in WEI.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount)
        self._add_command(RouterFunction.WRAP_ETH, args)
        return self

    def unwrap_weth(
            self,
            function_recipient: FunctionRecipient,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function UNWRAP_WETH which convert WETH to ETH through the UR

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount: The amount of sent WETH in WEI.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount)
        self._add_command(RouterFunction.UNWRAP_WETH, args)
        return self

    def v2_swap_exact_in(
            self,
            function_recipient: FunctionRecipient,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V2_SWAP_EXACT_IN, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount_in, amount_out_min, path, payer_is_sender)
        self._add_command(RouterFunction.V2_SWAP_EXACT_IN, args)
        return self

    def v2_swap_exact_in_from_balance(
            self,
            function_recipient: FunctionRecipient,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V2_SWAP_EXACT_IN, using the router balance as amount_in,
        which swaps tokens on Uniswap V2.
        Typically used when the amount_in is unknown because it comes from a V*_SWAP_EXACT_IN output.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        return self.v2_swap_exact_in(
            function_recipient,
            _RouterConstant.ROUTER_BALANCE.value,
            amount_out_min,
            path,
            custom_recipient,
            False,
        )

    def v2_swap_exact_out(
            self,
            function_recipient: FunctionRecipient,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[ChecksumAddress],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V2_SWAP_EXACT_OUT, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (recipient, amount_out, amount_in_max, path, payer_is_sender)
        self._add_command(RouterFunction.V2_SWAP_EXACT_OUT, args)
        return self

    def v3_swap_exact_in(
            self,
            function_recipient: FunctionRecipient,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V3_SWAP_EXACT_IN, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        encoded_v3_path = _Encoder.v3_path(RouterFunction.V3_SWAP_EXACT_IN.name, path)
        args = (recipient, amount_in, amount_out_min, encoded_v3_path, payer_is_sender)
        self._add_command(RouterFunction.V3_SWAP_EXACT_IN, args)
        return self

    def v3_swap_exact_in_from_balance(
            self,
            function_recipient: FunctionRecipient,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V3_SWAP_EXACT_IN, using the router balance as amount_in,
        which swaps tokens on Uniswap V3.
        Typically used when the amount_in is unknown because it comes from a V*_SWAP_EXACT_IN output.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out_min: The minimum accepted bought token (token_out) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        return self.v3_swap_exact_in(
            function_recipient,
            _RouterConstant.ROUTER_BALANCE.value,
            amount_out_min,
            path,
            custom_recipient,
            False,
        )

    def v3_swap_exact_out(
            self,
            function_recipient: FunctionRecipient,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            custom_recipient: Optional[ChecksumAddress] = None,
            payer_is_sender: bool = True) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function V3_SWAP_EXACT_OUT, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in percentage * 10000 (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        encoded_v3_path = _Encoder.v3_path(RouterFunction.V3_SWAP_EXACT_OUT.name, path)
        args = (recipient, amount_out, amount_in_max, encoded_v3_path, payer_is_sender)
        self._add_command(RouterFunction.V3_SWAP_EXACT_OUT, args)
        return self

    def permit2_permit(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function PERMIT2_PERMIT, which gives token allowances to the Permit2 contract.
        In addition, the Permit2 must be approved using the token contracts as usual.

        :param permit_single: The 1st element returned by create_permit2_signable_message()
        :param signed_permit_single: The 2nd element returned by create_permit2_signable_message(), once signed.

        :return: The chain link corresponding to this function call.
        """
        struct = (
            tuple(permit_single["details"].values()),
            permit_single["spender"],
            permit_single["sigDeadline"],
        )
        args = (struct, signed_permit_single.signature)
        self._add_command(RouterFunction.PERMIT2_PERMIT, args)
        return self

    def sweep(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            amount_min: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function SWEEP which sweeps all of the router's ERC20 or ETH to an address

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of the token to sweep or "0x0000000000000000000000000000000000000000" for ETH.
        :param amount_min: The minimum desired amount
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, amount_min)
        self._add_command(RouterFunction.SWEEP, args)
        return self

    def pay_portion(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            bips: int,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function PAY_PORTION which transfers a part of the router's ERC20 or ETH to an address.
        Transferred amount = balance * bips / 10_000

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of token to pay or "0x0000000000000000000000000000000000000000" for ETH.
        :param bips: integer between 0 and 10_000
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """
        if (
            bips < 0
            or bips > 10_000
            or not isinstance(bips, int)
        ):
            raise ValueError(f"Invalid argument: bips must be an int between 0 and 10_000. Received {bips}")

        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, bips)
        self._add_command(RouterFunction.PAY_PORTION, args)
        return self

    def transfer(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            value: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function TRANSFER which transfers an amount of ERC20 or ETH from the router's balance
        to an address.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of token to pay or "0x0000000000000000000000000000000000000000" for ETH.
        :param value: The amount to transfer (in Wei)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """

        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, value)
        self._add_command(RouterFunction.TRANSFER, args)
        return self

    def permit2_transfer_from(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the transfer of tokens from the caller address to the given recipient.
        The UR must have been permit2'ed for the token first.

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of the token to be transferred.
        :param amount: The amount to transfer.
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        args = (token_address, recipient, amount)
        self._add_command(RouterFunction.PERMIT2_TRANSFER_FROM, args)
        return self

    def v4_swap(self) -> _V4ChainedSwapFunctionBuilder:
        """
        V4 - Start building a call to the V4 swap functions

        :return: The chain link corresponding to this function call.
        """
        return _V4ChainedSwapFunctionBuilder(self, self._w3, self._abi_map)

    def v4_initialize_pool(self, pool_key: PoolKey, amount_0: Wei, amount_1: Wei) -> _ChainedFunctionBuilder:
        """
        V4 - Encode the call to initialize (create) a V4 pool.
        The amounts are used to compute the initial sqrtPriceX96. They are NOT sent.
        So, basically only the ratio amount_0 / amount_1 is relevant.
        For ex, to create a pool with 2 USD stable coins, you just need to set amount_0 = amount_1 = 1

        :param pool_key: The pool key that identify the pool to create
        :param amount_0: "virtual" amount of PoolKey.currency_0
        :param amount_1: "virtual" amount of PoolKey.currency_1
        :return: The chain link corresponding to this function call.
        """
        sqrt_price_x96 = compute_sqrt_price_x96(amount_0, amount_1)
        args = (tuple(pool_key.values()), sqrt_price_x96)
        self._add_command(RouterFunction.V4_INITIALIZE_POOL, args)
        return self

    def v4_posm_call(self) -> _V4ChainedPositionFunctionBuilder:
        """
        V4 - Start building a call to the V4 positon manager functions
        :return: The chain link corresponding to this function call.
        """
        return _V4ChainedPositionFunctionBuilder(self, self._w3, self._abi_map)

    def build(self, deadline: Optional[int] = None) -> HexStr:
        """
        Build the encoded input for all the chained commands, ready to be sent to the UR

        :param deadline: The optional unix timestamp after which the transaction won't be valid anymore.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        if deadline:
            execute_with_deadline_args = (bytes(self.commands), self.arguments, deadline)
            abi = self._abi_map[MiscFunctions.EXECUTE_WITH_DEADLINE]
            return Web3.to_hex(abi.get_selector() + abi.encode(execute_with_deadline_args))
        else:
            execute_args = (bytes(self.commands), self.arguments)
            abi = self._abi_map[MiscFunctions.EXECUTE]
            return Web3.to_hex(abi.get_selector() + abi.encode(execute_args))

    def build_transaction(
            self,
            sender: ChecksumAddress,
            value: Wei = Wei(0),
            trx_speed: Optional[TransactionSpeed] = TransactionSpeed.FAST,
            *,
            priority_fee: Optional[Wei] = None,
            max_fee_per_gas: Optional[Wei] = None,
            max_fee_per_gas_limit: Wei = Wei(100 * 10 ** 9),
            gas_limit: Optional[int] = None,
            chain_id: Optional[int] = None,
            nonce: Optional[Union[int, Nonce]] = None,
            ur_address: ChecksumAddress = _ur_address,
            deadline: Optional[int] = None,
            block_identifier: BlockIdentifier = "latest") -> TxParams:
        """
        Build the encoded data and the transaction dictionary, ready to be signed.

        By default, compute the gas fees, chain_id, nonce, deadline, ... but custom values can be used instead.
        Gas fees are computed with a given TransactionSpeed (default is FAST).
        All speeds will compute gas fees in order to try to place the transaction in the next block
        (without certainty, of course).
        So, during strained conditions, the computed gas fees could be very high but can be controlled
        thanks to 'max_fee_per_gas_limit'.

        Either a transaction speed is provided or custom gas fees, otherwise a ValueError is raised.

        The RouterCodec must be built with a Web3 instance or a rpc endpoint address except if custom values are used.

        :param sender: The 'from' field - Mandatory
        :param value: The quantity of ETH sent to the Universal Router - Default is 0
        :param trx_speed: The indicative 'speed' of the transaction - Default is TransactionSpeed.FAST
        :param priority_fee: custom 'maxPriorityFeePerGas' - Default is None
        :param max_fee_per_gas: custom 'maxFeePerGas' - Default is None
        :param max_fee_per_gas_limit: if the computed 'max_fee_per_gas' is greater than 'max_fee_per_gas_limit', raise a ValueError  # noqa
        :param gas_limit: custom 'gas' - Default is None
        :param chain_id: custom 'chainId'
        :param nonce: custom 'nonce'
        :param ur_address: custom Universal Router address
        :param deadline: The optional unix timestamp after which the transaction won't be valid anymore.
        :param block_identifier: specify at what block the computing is done. Mostly for test purposes.
        :return: a transaction (TxParams) ready to be signed
        """
        encoded_data = self.build(deadline)

        if chain_id is None:
            chain_id = self._w3.eth.chain_id

        if nonce is None:
            nonce = self._w3.eth.get_transaction_count(sender, block_identifier)

        if not trx_speed:
            if priority_fee is None or max_fee_per_gas is None:
                raise ValueError("Either trx_speed or both priority_fee and max_fee_per_gas must be set.")
            else:
                _priority_fee = priority_fee
                _max_fee_per_gas = max_fee_per_gas
        else:
            if priority_fee or max_fee_per_gas:
                raise ValueError("priority_fee and max_fee_per_gas can't be set with trx_speed")
            else:
                _priority_fee, _max_fee_per_gas = compute_gas_fees(self._w3, trx_speed, block_identifier)
                if _max_fee_per_gas > max_fee_per_gas_limit:
                    raise ValueError(
                        "Computed max_fee_per_gas is greater than max_fee_per_gas_limit. "
                        "Either provide max_fee_per_gas, increase max_fee_per_gas_limit "
                        "or wait for less strained conditions"
                    )

        tx_params: TxParams = {
            "from": sender,
            "value": value,
            "to": ur_address,
            "chainId": chain_id,
            "nonce": Nonce(nonce),
            "type": HexStr('0x2'),
            "maxPriorityFeePerGas": _priority_fee,
            "maxFeePerGas": _max_fee_per_gas,
            "data": encoded_data,
        }

        if gas_limit is None:
            estimated_gas = self._w3.eth.estimate_gas(tx_params, block_identifier)
            gas_limit = int(estimated_gas * 1.15)

        tx_params["gas"] = Wei(gas_limit)

        return tx_params
