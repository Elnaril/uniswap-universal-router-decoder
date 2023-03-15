"""
Encoding part of the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
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
from uniswap_universal_router_decoder._enums import _RouterFunction


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

    def _encode_wrap_eth_sub_contract(self, recipient: ChecksumAddress, amount_min: Wei) -> HexStr:
        abi_mapping = self._abi_map[_RouterFunction.WRAP_ETH]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.WRAP_ETH(recipient, amount_min)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, [recipient, amount_min]))

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

    def _encode_v3_swap_exact_in_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> HexStr:
        encoded_v3_path = self.v3_path(_RouterFunction.V3_SWAP_EXACT_IN.name, path)
        args = (recipient, amount_in, amount_out_min, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_IN]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V3_SWAP_EXACT_IN(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

    def _encode_v3_swap_exact_out_sub_contract(
            self,
            recipient: ChecksumAddress,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            payer_is_user: bool) -> HexStr:
        encoded_v3_path = self.v3_path(_RouterFunction.V3_SWAP_EXACT_OUT.name, path)
        args = (recipient, amount_out, amount_in_max, encoded_v3_path, payer_is_user)
        abi_mapping = self._abi_map[_RouterFunction.V3_SWAP_EXACT_OUT]
        sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
        contract_function: ContractFunction = sub_contract.functions.V3_SWAP_EXACT_OUT(*args)
        return remove_0x_prefix(encode_abi(self._w3, contract_function.abi, args))

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

    @staticmethod
    def get_default_deadline(valid_duration: int = 180) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 180
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def get_default_expiration(valid_duration: int = 30*24*3600) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 30 days
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def _encode_execution_function(arguments: Tuple[bytes, List[bytes], int]) -> HexStr:
        encoded_data = encode(_execution_function_input_types, arguments)
        return Web3.to_hex(Web3.to_bytes(hexstr=_execution_function_selector) + encoded_data)

    def wrap_eth(self, amount: Wei, deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function WRAP_ETH which convert ETH to WETH through the UR
        The weth recipient is the transaction sender.

        :param amount: The amount of sent ETH in WEI.
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        arguments = (
            Web3.to_bytes(_RouterFunction.WRAP_ETH.value),
            [
                Web3.to_bytes(hexstr=self._encode_wrap_eth_sub_contract(recipient, amount)),
            ],
            deadline or self.get_default_deadline(),
        )
        return self._encode_execution_function(arguments)

    def v2_swap_exact_in(
            self,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function V2_SWAP_EXACT_IN, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.
        The swap recipient is the transaction sender.

        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        payer_is_user = True
        encoded_sub_data = self._encode_v2_swap_exact_in_sub_contract(
            recipient,
            amount_in,
            amount_out_min,
            path,
            payer_is_user,
        )
        arguments = (
            Web3.to_bytes(_RouterFunction.V2_SWAP_EXACT_IN.value),
            [
                Web3.to_bytes(hexstr=encoded_sub_data),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    def v2_swap_exact_out(
            self,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[ChecksumAddress],
            deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function V2_SWAP_EXACT_OUT, which swaps tokens on Uniswap V2.
        Correct allowances must have been set before sending such transaction.
        The swap recipient is the transaction sender.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        payer_is_user = True
        encoded_sub_data = self._encode_v2_swap_exact_out_sub_contract(
            recipient,
            amount_out,
            amount_in_max,
            path,
            payer_is_user,
        )
        arguments = (
            Web3.to_bytes(_RouterFunction.V2_SWAP_EXACT_OUT.value),
            [
                Web3.to_bytes(hexstr=encoded_sub_data),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    def v3_swap_exact_in(
            self,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function V3_SWAP_EXACT_IN, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.
        The swap recipient is the transaction sender.

        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in basis points (ex: 3000 for 0.3%)
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        payer_is_user = True
        encoded_sub_data = self._encode_v3_swap_exact_in_sub_contract(
            recipient,
            amount_in,
            amount_out_min,
            path,
            payer_is_user,
        )
        arguments = (
            Web3.to_bytes(_RouterFunction.V3_SWAP_EXACT_IN.value),
            [
                Web3.to_bytes(hexstr=encoded_sub_data),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    def v3_swap_exact_out(
            self,
            amount_out: Wei,
            amount_in_max: Wei,
            path: Sequence[Union[int, ChecksumAddress]],
            deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function V3_SWAP_EXACT_OUT, which swaps tokens on Uniswap V3.
        Correct allowances must have been set before sending such transaction.
        The swap recipient is the transaction sender.
        :param amount_out: The exact amount of the bought (token_out) token in Wei
        :param amount_in_max: The maximum accepted sold token (token_in) in Wei
        :param path: The V3 path: a list of tokens where the first is the token_in, the last one is the token_out, and
        with the pool fee between each token in basis points (ex: 3000 for 0.3%)
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        payer_is_user = True
        encoded_sub_data = self._encode_v3_swap_exact_out_sub_contract(
            recipient,
            amount_out,
            amount_in_max,
            path,
            payer_is_user,
        )
        arguments = (
            Web3.to_bytes(_RouterFunction.V3_SWAP_EXACT_OUT.value),
            [
                Web3.to_bytes(hexstr=encoded_sub_data),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    def permit2_permit(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage,
            deadline: Optional[int] = None) -> HexStr:
        """
        Encode the call to the function PERMIT2_PERMIT, which gives token allowances to the Permit2 contract.
        In addition, the Permit2 must be approved using the token contracts as usual.
        :param permit_single: The 1st element returned by create_permit2_signable_message()
        :param signed_permit_single: The 2nd element returned by create_permit2_signable_message(), once signed.
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        encoded_sub_data = self._encode_permit2_permit_sub_contract(permit_single, signed_permit_single)
        arguments = (
            Web3.to_bytes(_RouterFunction.PERMIT2_PERMIT.value),
            [
                Web3.to_bytes(hexstr=encoded_sub_data),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    def v2_swap_exact_in_with_permit(
            self,
            permit_single: Dict[str, Any],
            signed_permit_single: SignedMessage,
            amount_in: Wei,
            amount_out_min: Wei,
            path: Sequence[ChecksumAddress],
            deadline: Optional[int] = None) -> HexStr:
        """
        Chain and encode the call to the functiond PERMIT2_PERMIT and V2_SWAP_EXACT_IN,
        which gives token allowances to the Permit2 contract and swap tokens.
        The Permit2 must be approved using the token contracts as usual.

        :param permit_single: The 1st element returned by create_permit2_signable_message()
        :param signed_permit_single: The 2nd element returned by create_permit2_signable_message(), once signed.
        :param amount_in: The exact amount of the sold (token_in) token in Wei
        :param amount_out_min: The minimum accepted bought token (token_out)
        :param path: The V2 path: a list of 2 or 3 tokens where the first is token_in and the last is token_out
        :param deadline: The unix timestamp after which the transaction won't be valid any more. Default to now + 180s.
        :return: The encoded data to add to the UR transaction dictionary parameters.
        """
        encoded_sub_data_permit = self._encode_permit2_permit_sub_contract(permit_single, signed_permit_single)
        recipient = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")  # recipient is sender
        payer_is_user = True
        encoded_sub_data_swap = self._encode_v2_swap_exact_in_sub_contract(
            recipient,
            amount_in,
            amount_out_min,
            path,
            payer_is_user,
        )
        arguments = (
            self._to_command(_RouterFunction.PERMIT2_PERMIT, _RouterFunction.V2_SWAP_EXACT_IN),
            [
                Web3.to_bytes(hexstr=encoded_sub_data_permit),
                Web3.to_bytes(hexstr=encoded_sub_data_swap),
            ],
            deadline or self.get_default_deadline()
        )
        return self._encode_execution_function(arguments)

    @staticmethod
    def _to_command(*router_functions: _RouterFunction) -> bytes:
        command = b""
        for r_fct in router_functions:
            command += Web3.to_bytes(r_fct.value)
        return command
