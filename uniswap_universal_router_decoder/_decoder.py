"""
Decoding part of the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from itertools import chain
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
)

from web3 import Web3
from web3.contract.contract import ContractFunction
from web3.types import (
    ChecksumAddress,
    HexBytes,
    HexStr,
    TxData,
)

from uniswap_universal_router_decoder._abi_builder import _ABIMap
from uniswap_universal_router_decoder._constants import _router_abi
from uniswap_universal_router_decoder._enums import (
    _RouterConstant,
    _RouterFunction,
)


class _Decoder:
    def __init__(self, w3: Web3, abi_map: _ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map

    def function_input(self, input_data: Union[HexStr, HexBytes]) -> Tuple[ContractFunction, Dict[str, Any]]:
        """
        Decode the data sent to an UR function

        :param input_data: the transaction 'input' data
        :return: The decoded data if the function has been implemented.
        """
        fct_name, decoded_input = self._router_contract.decode_function_input(input_data)
        command = decoded_input["commands"]
        command_input = decoded_input["inputs"]
        decoded_command_input = []
        for i, b in enumerate(command):
            # iterating over bytes produces integers
            command_function = b & _RouterConstant.COMMAND_TYPE_MASK.value
            try:
                abi_mapping = self._abi_map[_RouterFunction(command_function)]
                data = abi_mapping.selector + command_input[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
                revert_on_fail = not bool(b & _RouterConstant.FLAG_ALLOW_REVERT.value)
                decoded_command_input.append(
                    sub_contract.decode_function_input(data) + ({"revert_on_fail": revert_on_fail}, )
                )
            except (ValueError, KeyError):
                decoded_command_input.append(command_input[i].hex())
        decoded_input["inputs"] = decoded_command_input
        return fct_name, decoded_input

    def transaction(self, trx_hash: Union[HexBytes, HexStr]) -> Dict[str, Any]:
        """
        Get transaction details and decode the data used to call a UR function.

        ⚠ To use this method, the decoder must be built with a Web3 instance or a rpc endpoint address.

        :param trx_hash: the hash of the transaction sent to the UR
        :return: the transaction as a dict with the additional 'decoded_input' field
        """
        trx = self._get_transaction(trx_hash)
        fct_name, decoded_input = self.function_input(trx["input"])
        result_trx = dict(trx)
        result_trx["decoded_input"] = decoded_input
        return result_trx

    def _get_transaction(self, trx_hash: Union[HexBytes, HexStr]) -> TxData:
        return self._w3.eth.get_transaction(trx_hash)

    @staticmethod
    def v3_path(v3_fn_name: str, path: Union[bytes, str]) -> Tuple[Union[int, ChecksumAddress], ...]:
        """
        Decode a V3 router path

        :param v3_fn_name: V3_SWAP_EXACT_IN or V3_SWAP_EXACT_OUT only
        :param path: the V3 path as returned by decode_function_input() or decode_transaction()
        :return: a tuple of token addresses separated by the corresponding pool fees, first token being the 'in-token',
        last token being the 'out-token'
        """
        valid_fn_names = ("V3_SWAP_EXACT_IN", "V3_SWAP_EXACT_OUT")
        if v3_fn_name.upper() not in valid_fn_names:
            raise ValueError(f"v3_fn_name must be in {valid_fn_names}")
        path_str = path.hex() if isinstance(path, bytes) else str(path)
        path_str = path_str[2:] if path_str.startswith("0x") else path_str
        path_list: List[Union[int, ChecksumAddress]] = [Web3.to_checksum_address(path_str[0:40]), ]
        parsed_remaining_path: List[List[Union[int, ChecksumAddress]]] = [
            [
                int(path_str[40:][i:i + 6], 16),
                Web3.to_checksum_address(path_str[40:][i + 6:i + 46]),
            ]
            for i in range(0, len(path_str[40:]), 46)
        ]
        path_list.extend(list(chain.from_iterable(parsed_remaining_path)))

        if v3_fn_name.upper() == "V3_SWAP_EXACT_OUT":
            path_list.reverse()

        return tuple(path_list)
