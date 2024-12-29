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
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)

from eth_abi import encode
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

from uniswap_universal_router_decoder._abi_builder import _ABIMap
from uniswap_universal_router_decoder._constants import (
    _execution_function_input_types,
    _execution_function_selector,
    _execution_without_deadline_function_input_types,
    _execution_without_deadline_function_selector,
    _modify_liquidities_function_input_types,
    _modify_liquidities_function_selector,
    _path_key_types,
    _router_abi,
    _ur_address,
    _v4_swap_input_types,
)
from uniswap_universal_router_decoder._enums import (
    _RouterConstant,
    _RouterFunction,
    _V4Actions,
    FunctionRecipient,
    TransactionSpeed,
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


class _Encoder:
    def __init__(self, w3: Web3, abi_map: _ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map

    @staticmethod
    def v3_path(v3_fn_name: str, path_seq: Sequence[Union[int, ChecksumAddress]]) -> bytes:
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
        :param currency_0:
        :param currency_1:
        :param fee: pool fee in percentage * 10000 (ex: 3000 for 0.3%)
        :param tick_spacing: granularity of the pool. Lower values are more precise but more expensive to trade
        :param hooks: hook address
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

    @staticmethod
    def v4_pool_id(pool_key: PoolKey) -> bytes:
        path_key_values = tuple(pool_key.values())
        encoded_path_key = encode(_path_key_types, (path_key_values, ))
        return keccak(encoded_path_key)

    def chain(self) -> _ChainedFunctionBuilder:
        """
        :return: Initialize the chain of encoded functions
        """
        return _ChainedFunctionBuilder(self._w3, self._abi_map)


TV4ChainedCommonFunctionBuilder = TypeVar("TV4ChainedCommonFunctionBuilder", bound="_V4ChainedCommonFunctionBuilder")


class _V4ChainedCommonFunctionBuilder(ABC):
    def __init__(self, builder: _ChainedFunctionBuilder, w3: Web3, abi_map: _ABIMap):
        self.builder = builder
        self._w3 = w3
        self._abi_map = abi_map
        self.actions: bytearray = bytearray()
        self.arguments: List[bytes] = []

    def settle(
            self: TV4ChainedCommonFunctionBuilder,
            currency: ChecksumAddress,
            amount: int,
            payer_is_user: bool) -> TV4ChainedCommonFunctionBuilder:
        args = (currency, amount, payer_is_user)
        abi_mapping = self._abi_map[_V4Actions.SETTLE]
        self.actions.append(_V4Actions.SETTLE.value)
        self.arguments.append(encode(abi_mapping.fct_abi.get_abi_types(), args))
        return self


class _V4ChainedPositionFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def _encode_mint_position_sub_contract(
            self,
            pool_key: PoolKey,
            tick_lower: int,
            tick_upper: int,
            liquidity: int,
            amount_0_max: int,
            amount_1_max: int,
            recipient: ChecksumAddress,
            hook_data: bytes) -> bytes:
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
        abi_mapping = self._abi_map[_V4Actions.MINT_POSITION]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.actions.append(_V4Actions.MINT_POSITION.value)
        self.arguments.append(
            self._encode_mint_position_sub_contract(
                pool_key,
                tick_lower,
                tick_upper,
                liquidity,
                amount_0_max,
                amount_1_max,
                Web3.to_checksum_address(recipient),
                hook_data,
            )
        )
        return self

    def _encode_settle_pair_sub_contract(self, currency_0: ChecksumAddress, currency_1: ChecksumAddress) -> bytes:
        args = (currency_0, currency_1)
        abi_mapping = self._abi_map[_V4Actions.SETTLE_PAIR]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

    def settle_pair(
            self,
            currency_0: ChecksumAddress,
            currency_1: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        self.actions.append(_V4Actions.SETTLE_PAIR.value)
        self.arguments.append(
            self._encode_settle_pair_sub_contract(
                Web3.to_checksum_address(currency_0),
                Web3.to_checksum_address(currency_1),
            )
        )
        return self

    def close_currency(self, currency: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        args = (currency, )
        abi_mapping = self._abi_map[_V4Actions.CLOSE_CURRENCY]
        self.actions.append(_V4Actions.CLOSE_CURRENCY.value)
        self.arguments.append(encode(abi_mapping.fct_abi.get_abi_types(), args))
        return self

    def sweep(self, currency: ChecksumAddress, to: ChecksumAddress) -> _V4ChainedPositionFunctionBuilder:
        args = (currency, to)
        abi_mapping = self._abi_map[_V4Actions.SWEEP]
        self.actions.append(_V4Actions.SWEEP.value)
        self.arguments.append(encode(abi_mapping.fct_abi.get_abi_types(), args))
        return self

    @staticmethod
    def _encode_modify_liquidities_function(arguments: Tuple[bytes, int]) -> bytes:
        encoded_data = encode(_modify_liquidities_function_input_types, arguments)
        return Web3.to_bytes(hexstr=_modify_liquidities_function_selector) + encoded_data

    def build_v4_pm_call(self, deadline: int) -> _ChainedFunctionBuilder:
        action_values = (bytes(self.actions), self.arguments)
        encoded_data = encode(["bytes", "bytes[]"], action_values)
        encoded_modify_liquidities_data = self._encode_modify_liquidities_function((encoded_data, deadline))
        self.builder.commands.append(_RouterFunction.V4_POSITION_MANAGER_CALL.value)
        self.builder.arguments.append(encoded_modify_liquidities_data)
        return self.builder


class _V4ChainedSwapFunctionBuilder(_V4ChainedCommonFunctionBuilder):

    def _encode_swap_exact_in_single_sub_contract(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_in: Wei,
            amount_out_min: Wei,
            hook_data: bytes = b'') -> bytes:
        args = ((tuple(pool_key.values()), zero_for_one, amount_in, amount_out_min, hook_data),)
        abi_mapping = self._abi_map[_V4Actions.SWAP_EXACT_IN_SINGLE]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

    def swap_exact_in_single(
            self,
            pool_key: PoolKey,
            zero_for_one: bool,
            amount_in: Wei,
            amount_out_min: Wei,
            hook_data: bytes = b'') -> _V4ChainedSwapFunctionBuilder:
        """
        Encode the call to the V4_SWAP function SWAP_EXACT_IN_SINGLE.

        :param pool_key: the target pool key returned by encode.v4_pool_key()
        :param zero_for_one: the swap direction, true for currency_0 to currency_1, false for currency_1 to currency_0
        :param amount_in: the exact amount of the sold currency in Wei
        :param amount_out_min: the minimum accepted bought currency
        :param hook_data: encoded data sent to the pool's hook, if any.
        :return:
        """
        self.actions.append(_V4Actions.SWAP_EXACT_IN_SINGLE.value)
        self.arguments.append(
            self._encode_swap_exact_in_single_sub_contract(
                pool_key,
                zero_for_one,
                amount_in,
                amount_out_min,
                hook_data,
            )
        )
        return self

    def take_all(self, currency: ChecksumAddress, min_amount: Wei) -> _V4ChainedSwapFunctionBuilder:
        args = (currency, min_amount)
        abi_mapping = self._abi_map[_V4Actions.TAKE_ALL]
        self.actions.append(_V4Actions.TAKE_ALL.value)
        self.arguments.append(encode(abi_mapping.fct_abi.get_abi_types(), args))
        return self

    def settle_all(self, currency: ChecksumAddress, max_amount: Wei) -> _V4ChainedSwapFunctionBuilder:
        args = (currency, max_amount)
        abi_mapping = self._abi_map[_V4Actions.SETTLE_ALL]
        self.actions.append(_V4Actions.SETTLE_ALL.value)
        self.arguments.append(encode(abi_mapping.fct_abi.get_abi_types(), args))
        return self

    def build_v4_swap(self) -> _ChainedFunctionBuilder:
        action_values = (bytes(self.actions), self.arguments)
        encoded_data = encode(_v4_swap_input_types, action_values)
        self.builder.commands.append(_RouterFunction.V4_SWAP.value)
        self.builder.arguments.append(encoded_data)
        return self.builder


class _ChainedFunctionBuilder:
    def __init__(self, w3: Web3, abi_map: _ABIMap):
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self.commands: bytearray = bytearray()
        self.arguments: List[bytes] = []

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
    def _get_command(router_function: _RouterFunction, revert_on_fail: bool) -> int:
        return int(router_function.value if revert_on_fail else router_function.value | NO_REVERT_FLAG)

    @staticmethod
    def _encode_execution_function(arguments: Tuple[bytes, List[bytes], int]) -> HexStr:
        encoded_data = encode(_execution_function_input_types, arguments)
        return Web3.to_hex(Web3.to_bytes(hexstr=_execution_function_selector) + encoded_data)

    @staticmethod
    def _encode_execution_without_deadline_function(arguments: Tuple[bytes, List[bytes]]) -> HexStr:
        encoded_data = encode(_execution_without_deadline_function_input_types, arguments)
        return Web3.to_hex(Web3.to_bytes(hexstr=_execution_without_deadline_function_selector) + encoded_data)

    def _encode_wrap_eth_sub_contract(self, recipient: ChecksumAddress, amount_min: Wei) -> bytes:
        abi_mapping = self._abi_map[_RouterFunction.WRAP_ETH]
        return encode(abi_mapping.fct_abi.get_abi_types(), [recipient, amount_min])

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
        self.commands.append(_RouterFunction.WRAP_ETH.value)
        self.arguments.append(self._encode_wrap_eth_sub_contract(recipient, amount))
        return self

    def _encode_unwrap_weth_sub_contract(self, recipient: ChecksumAddress, amount_min: Wei) -> bytes:
        abi_mapping = self._abi_map[_RouterFunction.UNWRAP_WETH]
        return encode(abi_mapping.fct_abi.get_abi_types(), [recipient, amount_min])

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
        self.commands.append(_RouterFunction.UNWRAP_WETH.value)
        self.arguments.append(self._encode_unwrap_weth_sub_contract(recipient, amount))
        return self

    def _encode_v2_swap_exact_in_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            payer_is_user: bool) -> bytes:
        args = (recipient, amount_in, amount_out_min, path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V2_SWAP_EXACT_IN]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.commands.append(_RouterFunction.V2_SWAP_EXACT_IN.value)
        self.arguments.append(
            self._encode_v2_swap_exact_in_sub_contract(
                recipient,
                amount_in,
                amount_out_min,
                path,
                payer_is_sender,
            )
        )
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

    def _encode_v2_swap_exact_out_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[ChecksumAddress],
            payer_is_user: bool) -> bytes:
        args = (recipient, amount_out, amount_in_max, path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V2_SWAP_EXACT_OUT]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.commands.append(_RouterFunction.V2_SWAP_EXACT_OUT.value)
        self.arguments.append(
            self._encode_v2_swap_exact_out_sub_contract(
                recipient,
                amount_out,
                amount_in_max,
                path,
                payer_is_sender,
            )
        )
        return self

    def _encode_v3_swap_exact_in_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> bytes:
        encoded_v3_path = _Encoder.v3_path(_RouterFunction.V3_SWAP_EXACT_IN.name, path)
        args = (recipient, amount_in, amount_out_min, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_IN]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.commands.append(_RouterFunction.V3_SWAP_EXACT_IN.value)
        self.arguments.append(
            self._encode_v3_swap_exact_in_sub_contract(
                recipient,
                amount_in,
                amount_out_min,
                path,
                payer_is_sender,
            )
        )
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

    def _encode_v3_swap_exact_out_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> bytes:
        encoded_v3_path = _Encoder.v3_path(_RouterFunction.V3_SWAP_EXACT_OUT.name, path)
        args = (recipient, amount_out, amount_in_max, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_OUT]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.commands.append(_RouterFunction.V3_SWAP_EXACT_OUT.value)
        self.arguments.append(
            self._encode_v3_swap_exact_out_sub_contract(
                recipient,
                amount_out,
                amount_in_max,
                path,
                payer_is_sender,
            )
        )
        return self

    def _encode_permit2_permit_sub_contract(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage) -> bytes:
        struct = (
            tuple(permit_single["details"].values()),
            permit_single["spender"],
            permit_single["sigDeadline"],
        )
        args = (struct, signed_permit_single.signature)
        abi_mapping = self._abi_map[_RouterFunction.PERMIT2_PERMIT]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

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
        self.commands.append(_RouterFunction.PERMIT2_PERMIT.value)
        self.arguments.append(
            self._encode_permit2_permit_sub_contract(
                permit_single,
                signed_permit_single,
            )
        )
        return self

    def _encode_sweep_sub_contract(self, token: ChecksumAddress, recipient: ChecksumAddress, amount_min: Wei) -> bytes:
        abi_mapping = self._abi_map[_RouterFunction.SWEEP]
        return encode(abi_mapping.fct_abi.get_abi_types(), [token, recipient, amount_min])

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
        self.commands.append(_RouterFunction.SWEEP.value)
        self.arguments.append(
            self._encode_sweep_sub_contract(
                token_address,
                recipient,
                amount_min,
            )
        )
        return self

    def _encode_pay_portion_sub_contract(self, token: ChecksumAddress, recipient: ChecksumAddress, bips: int) -> bytes:
        abi_mapping = self._abi_map[_RouterFunction.PAY_PORTION]
        return encode(abi_mapping.fct_abi.get_abi_types(), [token, recipient, bips])

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
        self.commands.append(_RouterFunction.PAY_PORTION.value)
        self.arguments.append(
            self._encode_pay_portion_sub_contract(
                token_address,
                recipient,
                bips,
            )
        )
        return self

    def _encode_transfer_sub_contract(self, token: ChecksumAddress, recipient: ChecksumAddress, value: int) -> bytes:
        abi_mapping = self._abi_map[_RouterFunction.TRANSFER]
        return encode(abi_mapping.fct_abi.get_abi_types(), [token, recipient, value])

    def transfer(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            value: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        """
        Encode the call to the function TRANSFER which transfers a part of the router's ERC20 or ETH to an address.
        Transferred amount = balance * bips / 10_000

        :param function_recipient: A FunctionRecipient which defines the recipient of this function output.
        :param token_address: The address of token to pay or "0x0000000000000000000000000000000000000000" for ETH.
        :param value: The amount to transfer (in Wei)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.

        :return: The chain link corresponding to this function call.
        """

        recipient = self._get_recipient(function_recipient, custom_recipient)
        self.commands.append(_RouterFunction.TRANSFER.value)
        self.arguments.append(
            self._encode_transfer_sub_contract(
                token_address,
                recipient,
                value,
            )
        )
        return self

    def permit2_transfer_from(
            self,
            function_recipient: FunctionRecipient,
            token_address: ChecksumAddress,
            amount: Wei,
            custom_recipient: Optional[ChecksumAddress] = None) -> _ChainedFunctionBuilder:
        recipient = self._get_recipient(function_recipient, custom_recipient)
        abi_mapping = self._abi_map[_RouterFunction.PERMIT2_TRANSFER_FROM]
        self.commands.append(_RouterFunction.PERMIT2_TRANSFER_FROM.value)
        self.arguments.append(
            encode(abi_mapping.fct_abi.get_abi_types(), [token_address, recipient, amount])
        )
        return self

    def v4_swap(self) -> _V4ChainedSwapFunctionBuilder:
        return _V4ChainedSwapFunctionBuilder(self, self._w3, self._abi_map)

    def _encode_v4_initialize_pool_sub_contract(self, pool_key: PoolKey, sqrt_price_x96: int) -> bytes:
        args = (tuple(pool_key.values()), sqrt_price_x96)
        abi_mapping = self._abi_map[_RouterFunction.V4_INITIALIZE_POOL]
        return encode(abi_mapping.fct_abi.get_abi_types(), args)

    def v4_initialize_pool(self, pool_key: PoolKey, amount_0: Wei, amount_1: Wei) -> _ChainedFunctionBuilder:
        sqrt_price_x96 = compute_sqrt_price_x96(amount_0, amount_1)
        self.commands.append(_RouterFunction.V4_INITIALIZE_POOL.value)
        self.arguments.append(
            self._encode_v4_initialize_pool_sub_contract(
                pool_key,
                sqrt_price_x96,
            )
        )
        return self

    def v4_pm_call(self) -> _V4ChainedPositionFunctionBuilder:
        return _V4ChainedPositionFunctionBuilder(self, self._w3, self._abi_map)

    def build(self, deadline: Optional[int] = None) -> HexStr:
        """
        Build the encoded input for all the chained commands, ready to be sent to the UR

        :param deadline: The optional unix timestamp after which the transaction won't be valid any more.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        if deadline:
            execute_input = (bytes(self.commands), self.arguments, deadline)
            return self._encode_execution_function(execute_input)
        else:
            execute_without_deadline_input = (bytes(self.commands), self.arguments)
            return self._encode_execution_without_deadline_function(execute_without_deadline_input)

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
        :param deadline: The optional unix timestamp after which the transaction won't be valid any more.
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
