"""
Decoding part of the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from itertools import chain
import json
from typing import (
    Any,
    Dict,
    List,
    Sequence,
    Tuple,
    Union,
)

from eth_abi import decode
from eth_abi.exceptions import DecodingError
from web3 import Web3
from web3.contract.contract import BaseContractFunction
from web3.exceptions import Web3Exception
from web3.types import (
    ChecksumAddress,
    HexBytes,
    HexStr,
    TxData,
)

from uniswap_universal_router_decoder._abi_builder import (
    _ABIMap,
    build_abi_type_list,
)
from uniswap_universal_router_decoder._constants import (
    _permit2_abi,
    _pool_manager_abi,
    _position_manager_abi,
    _router_abi,
)
from uniswap_universal_router_decoder._enums import (
    _RouterConstant,
    _RouterFunction,
    _V4Actions,
)


class _V4Decoder:
    def __init__(self, w3: Web3, abi_map: _ABIMap) -> None:
        self._w3 = w3
        self._abi_map = abi_map
        self._pm_contract = w3.eth.contract(abi=_position_manager_abi)

    def _decode_v4_actions(
            self,
            actions: bytes,
            params: List[bytes]) -> List[Tuple[BaseContractFunction, Dict[str, Any]]]:
        if len(actions) != len(params):
            raise ValueError(f"Number of actions {len(actions)} is different from number of params: {len(params)}")

        decoded_params = []
        for i, action in enumerate(actions):
            try:
                abi_mapping = self._abi_map[_V4Actions(action)]
                data = abi_mapping.selector + params[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
                decoded_params.append(sub_contract.decode_function_input(data))
            except (ValueError, KeyError, DecodingError):
                decoded_params.append(params[i].hex())
        return decoded_params

    def decode_v4_swap(self, actions: bytes, params: List[bytes]) -> List[Tuple[BaseContractFunction, Dict[str, Any]]]:
        return self._decode_v4_actions(actions, params)

    def decode_v4_pm_call(self, encoded_input: bytes) -> Dict[str, Any]:
        actions, params = decode(["bytes", "bytes[]"], encoded_input)
        return {"actions": actions, "params": self._decode_v4_actions(actions, params)}


class _Decoder:
    def __init__(self, w3: Web3, abi_map: _ABIMap) -> None:
        self._w3 = w3
        self._router_contract = self._w3.eth.contract(abi=_router_abi)
        self._abi_map = abi_map
        self._v4_decoder = _V4Decoder(w3, abi_map)

    def function_input(self, input_data: Union[HexStr, HexBytes]) -> Tuple[BaseContractFunction, Dict[str, Any]]:
        """
        Decode the data sent to an UR function

        :param input_data: the transaction 'input' data
        :return: The decoded data if the function has been implemented.
        """
        fct_name, decoded_input = self._router_contract.decode_function_input(input_data)
        # returns (execute as basecontractfunction, {commands as bytes, inputs as seq of bytes, deadline as int})
        command = decoded_input["commands"]
        command_input = decoded_input["inputs"]
        decoded_command_input = []
        for i, b in enumerate(command):
            # iterating over bytes produces integers
            command_function = b & _RouterConstant.COMMAND_TYPE_MASK.value
            try:
                abi_mapping = self._abi_map[_RouterFunction(command_function)]
                if b == _RouterFunction.V4_POSITION_MANAGER_CALL.value:
                    data = command_input[i]
                else:
                    data = abi_mapping.selector + command_input[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
                revert_on_fail = not bool(b & _RouterConstant.FLAG_ALLOW_REVERT.value)
                decoded_fct_name, decoded_fct_params = sub_contract.decode_function_input(data)
                if b == _RouterFunction.V4_SWAP.value:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            {
                                "actions": decoded_fct_params["actions"],
                                "params": self._v4_decoder.decode_v4_swap(
                                    decoded_fct_params["actions"],
                                    decoded_fct_params["params"],
                                ),
                            },
                            {"revert_on_fail": revert_on_fail},
                        )
                    )
                elif b == _RouterFunction.V4_POSITION_MANAGER_CALL.value:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            {
                                "unlockData": self._v4_decoder.decode_v4_pm_call(decoded_fct_params["unlockData"]),
                                "deadline": decoded_fct_params["deadline"]
                            },
                            {"revert_on_fail": revert_on_fail},
                        )
                    )
                else:
                    decoded_command_input.append(
                        (
                            decoded_fct_name,
                            decoded_fct_params,
                            {"revert_on_fail": revert_on_fail}
                        )
                    )

            except (ValueError, KeyError, DecodingError):
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

    def contract_error(
            self,
            contract_error: Union[str, HexStr],
            abis: Sequence[str] = (_permit2_abi, _pool_manager_abi, _position_manager_abi, _router_abi),
    ) -> Tuple[str, Dict[str, Any]]:
        for abi in abis:
            try:
                json_abi = json.loads(abi)
                error_abi = []
                for item in json_abi:
                    if item["type"].lower() == "error":
                        item["type"] = "function"
                        error_abi.append(item)
                contract = self._w3.eth.contract(abi=error_abi)
                error, params = contract.decode_function_input(contract_error)
                return f"{error.fn_name}({','.join(build_abi_type_list(error.abi))})", params
            except (ValueError, Web3Exception):
                """The error is not defined in this ABI"""
        return "Unknown error", {}
