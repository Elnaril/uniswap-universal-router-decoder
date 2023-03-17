"""
Encoding part of the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from datetime import datetime
from typing import (
    Any,
    cast,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from eth_abi import encode
from eth_account.account import SignedMessage
from eth_utils import remove_0x_prefix
from web3 import Web3
from web3._utils.contracts import encode_abi  # noqa
from web3.contract.contract import ContractFunction
from web3.types import (
    ChecksumAddress,
    HexStr,
    Wei,
)

from uniswap_universal_router_decoder._abi_builder import _ABIMap
from uniswap_universal_router_decoder._constants import (
    _execution_function_input_types,
    _execution_function_selector,
    _router_abi,
)
from uniswap_universal_router_decoder._enums import (
    _RouterConstant,
    _RouterFunction,
    FunctionRecipient,
)


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

    def chain(self) -> _ChainedFunctionBuilder:
        """
        :return: Initialize the chain of encoded functions
        """
        return _ChainedFunctionBuilder(self._w3, self._abi_map)


class _ChainedFunctionBuilder:
    def __init__(self, w3: Web3, abi_map: _ABIMap):
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self.commands: List[_RouterFunction] = []
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
    def _to_command(*router_functions: _RouterFunction) -> bytes:
        command = b""
        for r_fct in router_functions:
            command += Web3.to_bytes(r_fct.value)
        return command

    @staticmethod
    def _encode_execution_function(arguments: Tuple[bytes, List[bytes], int]) -> HexStr:
        encoded_data = encode(_execution_function_input_types, arguments)
        return Web3.to_hex(Web3.to_bytes(hexstr=_execution_function_selector) + encoded_data)

    def _encode_wrap_eth_sub_contract(self, recipient: ChecksumAddress, amount_min: Wei) -> HexStr:
        abi_mapping = self._abi_map[_RouterFunction.WRAP_ETH]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.WRAP_ETH(recipient, amount_min)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, [recipient, amount_min]))

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
        self.commands.append(_RouterFunction.WRAP_ETH)
        self.arguments.append(Web3.to_bytes(hexstr=self._encode_wrap_eth_sub_contract(recipient, amount)))
        return self

    def _encode_v2_swap_exact_in_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            payer_is_user: bool) -> HexStr:
        args = (recipient, amount_in, amount_out_min, path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V2_SWAP_EXACT_IN]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V2_SWAP_EXACT_IN(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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
        self.commands.append(_RouterFunction.V2_SWAP_EXACT_IN)
        self.arguments.append(
            Web3.to_bytes(
                hexstr=self._encode_v2_swap_exact_in_sub_contract(
                    recipient,
                    amount_in,
                    amount_out_min,
                    path,
                    payer_is_sender,
                )
            )
        )
        return self

    def _encode_v2_swap_exact_out_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[ChecksumAddress],
            payer_is_user: bool) -> HexStr:
        args = (recipient, amount_out, amount_in_max, path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V2_SWAP_EXACT_OUT]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V2_SWAP_EXACT_OUT(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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
        self.commands.append(_RouterFunction.V2_SWAP_EXACT_OUT)
        self.arguments.append(
            Web3.to_bytes(
                hexstr=self._encode_v2_swap_exact_out_sub_contract(
                    recipient,
                    amount_out,
                    amount_in_max,
                    path,
                    payer_is_sender,
                )
            )
        )
        return self

    def _encode_v3_swap_exact_in_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> HexStr:
        encoded_v3_path = _Encoder.v3_path(_RouterFunction.V3_SWAP_EXACT_IN.name, path)
        args = (recipient, amount_in, amount_out_min, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_IN]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V3_SWAP_EXACT_IN(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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
        with the pool fee between each token in basis points (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router
        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        self.commands.append(_RouterFunction.V3_SWAP_EXACT_IN)
        self.arguments.append(
            Web3.to_bytes(
                hexstr=self._encode_v3_swap_exact_in_sub_contract(
                    recipient,
                    amount_in,
                    amount_out_min,
                    path,
                    payer_is_sender,
                )
            )
        )
        return self

    def _encode_v3_swap_exact_out_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> HexStr:
        encoded_v3_path = _Encoder.v3_path(_RouterFunction.V3_SWAP_EXACT_OUT.name, path)
        args = (recipient, amount_out, amount_in_max, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_OUT]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V3_SWAP_EXACT_OUT(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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
        with the pool fee between each token in basis points (ex: 3000 for 0.3%)
        :param custom_recipient: If function_recipient is CUSTOM, must be the actual recipient, otherwise None.
        :param payer_is_sender: True if the in tokens come from the sender, False if they already are in the router
        :return: The chain link corresponding to this function call.
        """
        recipient = self._get_recipient(function_recipient, custom_recipient)
        self.commands.append(_RouterFunction.V3_SWAP_EXACT_OUT)
        self.arguments.append(
            Web3.to_bytes(
                hexstr=self._encode_v3_swap_exact_out_sub_contract(
                    recipient,
                    amount_out,
                    amount_in_max,
                    path,
                    payer_is_sender,
                )
            )
        )
        return self

    def _encode_permit2_permit_sub_contract(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage) -> HexStr:
        struct = (
            tuple(permit_single["details"].values()),
            permit_single["spender"],
            permit_single["sigDeadline"],
        )
        args = (struct, signed_permit_single.signature)
        abi_mapping = self._abi_map[_RouterFunction.PERMIT2_PERMIT]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.PERMIT2_PERMIT(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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
        self.commands.append(_RouterFunction.PERMIT2_PERMIT)
        self.arguments.append(
            Web3.to_bytes(
                hexstr=self._encode_permit2_permit_sub_contract(
                    permit_single,
                    signed_permit_single,
                )
            )
        )
        return self

    def build(self, deadline: Optional[int] = None) -> HexStr:
        """
        Build the encoded input for all the chained commands, ready to be sent to the UR
        Currently default deadline is now + 180s
        Todo: Support UR execution function without deadline

        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        execute_input = (
            self._to_command(*self.commands),
            self.arguments,
            deadline or int(datetime.now().timestamp() + 180)  # Todo: support UR execution function without deadline
        )
        return self._encode_execution_function(execute_input)
