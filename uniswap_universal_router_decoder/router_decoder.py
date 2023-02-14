from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from eth_utils import function_abi_to_4byte_selector
from web3 import Web3
from web3.contract import ContractFunction
from web3.types import (
    ChecksumAddress,
    HexBytes,
    HexStr,
    TxData,
)


class RouterDecoder:
    def __init__(self, w3: Optional[Web3] = None, rpc_endpoint: Optional[str] = None) -> None:
        self._abi_map = self._build_abi_map()
        if w3:
            self._w3 = w3
        elif rpc_endpoint:
            self._w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        else:
            self._w3 = Web3()
        self._router_contract = self._w3.eth.contract(abi=_router_abi)

    def decode_function_input(self, input_data: Union[HexStr, HexBytes]) -> Tuple[ContractFunction, Dict[str, Any]]:
        fct_name, decoded_input = self._router_contract.decode_function_input(input_data)
        command = decoded_input["commands"]
        command_input = decoded_input["inputs"]
        decoded_command_input = []
        for i, b in enumerate(command[-6:]):
            # iterating over bytes produces integers
            abi_mapping = self._abi_map.get(b)
            if abi_mapping:
                data = abi_mapping.selector + command_input[i]
                sub_contract = self._w3.eth.contract(abi=abi_mapping.fct_abi.get_full_abi())
                decoded_command_input.append(sub_contract.decode_function_input(data))
            else:
                decoded_command_input.append(command_input[i].hex())
        decoded_input["inputs"] = decoded_command_input
        return fct_name, decoded_input

    def decode_transaction(self, trx_hash: Union[HexBytes, HexStr]) -> Dict[str, Any]:
        trx = self._get_transaction(trx_hash)
        fct_name, decoded_input = self.decode_function_input(trx["input"])
        result_trx = dict(trx)
        result_trx["decoded_input"] = decoded_input
        return result_trx

    @staticmethod
    def decode_v3_path(v3_fn_name: str, path: Union[bytes, str]) -> Tuple[Union[int, ChecksumAddress], ...]:
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
        path_str = path.hex().lstrip("0x") if type(path) == bytes else str(path).lstrip("0x")
        path_list: List[Union[int, ChecksumAddress]] = [Web3.toChecksumAddress(path_str[0:40]), ]
        parsed_remaining_path: List[List[Union[int, ChecksumAddress]]] = [
            [
                int(path_str[40:][i:i + 6], 16),
                Web3.toChecksumAddress(path_str[40:][i + 6:i + 46]),
            ]
            for i in range(0, len(path_str[40:]), 46)
        ]
        path_list.extend(list(chain.from_iterable(parsed_remaining_path)))

        if v3_fn_name.upper() == "V3_SWAP_EXACT_OUT":
            path_list.reverse()

        return tuple(path_list)

    def _get_transaction(self, trx_hash: Union[HexBytes, HexStr]) -> TxData:
        return self._w3.eth.get_transaction(trx_hash)

    def _build_abi_map(self) -> _ABIMap:
        abi_map: _ABIMap = {
            # mapping between command identifier and fct descriptor (fct abi + selector)
            0: self._add_mapping(self._build_v3_swap_exact_in),
            1: self._add_mapping(self._build_v3_swap_exact_out),
            8: self._add_mapping(self._build_v2_swap_exact_in),
            9: self._add_mapping(self._build_v2_swap_exact_out),
            10: self._add_mapping(self._build_permit2_permit),
            11: self._add_mapping(self._build_wrap_eth),
            12: self._add_mapping(self._build_unwrap_weth),
        }
        return abi_map

    @staticmethod
    def _add_mapping(build_abi_method: Callable[[], _FunctionABI]) -> _FunctionDesc:
        fct_abi = build_abi_method()
        selector = function_abi_to_4byte_selector(fct_abi.get_abi())
        return _FunctionDesc(fct_abi=fct_abi, selector=selector)

    @staticmethod
    def _build_v2_swap_exact_in() -> _FunctionABI:
        builder = _FunctionABIBuilder("V2_SWAP_EXACT_IN")
        builder.add_address("recipient").add_int("amountIn").add_int("amountOutMin").add_address_array("path")
        return builder.add_bool("payerIsUser").build()

    @staticmethod
    def _build_permit2_permit() -> _FunctionABI:
        builder = _FunctionABIBuilder("PERMIT2_PERMIT")
        inner_struct = builder.create_struct("details")
        inner_struct.add_address("token").add_int("amount").add_int("expiration").add_int("nonce")
        outer_struct = builder.create_struct("struct")
        outer_struct.add_struct(inner_struct).add_address("spender").add_int("sigDeadline")
        return builder.add_struct(outer_struct).add_bytes("data").build()

    @staticmethod
    def _build_unwrap_weth() -> _FunctionABI:
        builder = _FunctionABIBuilder("UNWRAP_WETH")
        return builder.add_address("recipient").add_int("amountMin").build()

    @staticmethod
    def _build_v3_swap_exact_in() -> _FunctionABI:
        builder = _FunctionABIBuilder("V3_SWAP_EXACT_IN")
        builder.add_address("recipient").add_int("amountIn").add_int("amountOutMin").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_wrap_eth() -> _FunctionABI:
        builder = _FunctionABIBuilder("WRAP_ETH")
        return builder.add_address("recipient").add_int("amountMin").build()

    @staticmethod
    def _build_v2_swap_exact_out() -> _FunctionABI:
        builder = _FunctionABIBuilder("V2_SWAP_EXACT_OUT")
        builder.add_address("recipient").add_int("amountOut").add_int("amountInMax").add_address_array("path")
        return builder.add_bool("payerIsUser").build()

    @staticmethod
    def _build_v3_swap_exact_out() -> _FunctionABI:
        builder = _FunctionABIBuilder("V3_SWAP_EXACT_OUT")
        builder.add_address("recipient").add_int("amountIn").add_int("amountOutMin").add_bytes("path")
        return builder.add_bool("payerIsSender").build()


@dataclass(frozen=True)
class _FunctionABI:
    inputs: List[Any]
    name: str
    type: str

    def get_abi(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.type == "tuple":
            result["components"] = result.pop("inputs")
        return result

    def get_full_abi(self) -> List[Dict[str, Any]]:
        return [self.get_abi()]


@dataclass(frozen=True)
class _FunctionDesc:
    fct_abi: _FunctionABI
    selector: bytes


_ABIMap = Dict[int, _FunctionDesc]


class _FunctionABIBuilder:
    def __init__(self, fct_name: str, _type: str = "function") -> None:
        self.abi = _FunctionABI(inputs=[], name=fct_name, type=_type)

    def add_address(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "address"})
        return self

    def add_int(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint256"})
        return self

    def add_address_array(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "address[]"})
        return self

    def add_bool(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bool"})
        return self

    def build(self) -> _FunctionABI:
        return self.abi

    @staticmethod
    def create_struct(arg_name: str) -> _FunctionABIBuilder:
        return _FunctionABIBuilder(arg_name, "tuple")

    def add_struct(self, struct: _FunctionABIBuilder) -> _FunctionABIBuilder:
        self.abi.inputs.append(struct.abi.get_abi())
        return self

    def add_bytes(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bytes"})
        return self


_router_abi = '[{"inputs":[{"components":[{"internalType":"address","name":"permit2","type":"address"},{"internalType":"address","name":"weth9","type":"address"},{"internalType":"address","name":"seaport","type":"address"},{"internalType":"address","name":"nftxZap","type":"address"},{"internalType":"address","name":"x2y2","type":"address"},{"internalType":"address","name":"foundation","type":"address"},{"internalType":"address","name":"sudoswap","type":"address"},{"internalType":"address","name":"nft20Zap","type":"address"},{"internalType":"address","name":"cryptopunks","type":"address"},{"internalType":"address","name":"looksRare","type":"address"},{"internalType":"address","name":"routerRewardsDistributor","type":"address"},{"internalType":"address","name":"looksRareRewardsDistributor","type":"address"},{"internalType":"address","name":"looksRareToken","type":"address"},{"internalType":"address","name":"v2Factory","type":"address"},{"internalType":"address","name":"v3Factory","type":"address"},{"internalType":"bytes32","name":"pairInitCodeHash","type":"bytes32"},{"internalType":"bytes32","name":"poolInitCodeHash","type":"bytes32"}],"internalType":"struct RouterParameters","name":"params","type":"tuple"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"ContractLocked","type":"error"},{"inputs":[],"name":"ETHNotAccepted","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandIndex","type":"uint256"},{"internalType":"bytes","name":"message","type":"bytes"}],"name":"ExecutionFailed","type":"error"},{"inputs":[],"name":"FromAddressIsNotOwner","type":"error"},{"inputs":[],"name":"InsufficientETH","type":"error"},{"inputs":[],"name":"InsufficientToken","type":"error"},{"inputs":[],"name":"InvalidBips","type":"error"},{"inputs":[{"internalType":"uint256","name":"commandType","type":"uint256"}],"name":"InvalidCommandType","type":"error"},{"inputs":[],"name":"InvalidOwnerERC1155","type":"error"},{"inputs":[],"name":"InvalidOwnerERC721","type":"error"},{"inputs":[],"name":"InvalidPath","type":"error"},{"inputs":[],"name":"InvalidReserves","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[],"name":"NoSlice","type":"error"},{"inputs":[],"name":"SliceOutOfBounds","type":"error"},{"inputs":[],"name":"SliceOverflow","type":"error"},{"inputs":[],"name":"ToAddressOutOfBounds","type":"error"},{"inputs":[],"name":"ToAddressOverflow","type":"error"},{"inputs":[],"name":"ToUint24OutOfBounds","type":"error"},{"inputs":[],"name":"ToUint24Overflow","type":"error"},{"inputs":[],"name":"TransactionDeadlinePassed","type":"error"},{"inputs":[],"name":"UnableToClaim","type":"error"},{"inputs":[],"name":"UnsafeCast","type":"error"},{"inputs":[],"name":"V2InvalidPath","type":"error"},{"inputs":[],"name":"V2TooLittleReceived","type":"error"},{"inputs":[],"name":"V2TooMuchRequested","type":"error"},{"inputs":[],"name":"V3InvalidAmountOut","type":"error"},{"inputs":[],"name":"V3InvalidCaller","type":"error"},{"inputs":[],"name":"V3InvalidSwap","type":"error"},{"inputs":[],"name":"V3TooLittleReceived","type":"error"},{"inputs":[],"name":"V3TooMuchRequested","type":"error"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"RewardsSent","type":"event"},{"inputs":[{"internalType":"bytes","name":"looksRareClaim","type":"bytes"}],"name":"collectRewards","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bytes","name":"commands","type":"bytes"},{"internalType":"bytes[]","name":"inputs","type":"bytes[]"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"execute","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256[]","name":"","type":"uint256[]"},{"internalType":"uint256[]","name":"","type":"uint256[]"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC1155BatchReceived","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC1155Received","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bytes","name":"","type":"bytes"}],"name":"onERC721Received","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"int256","name":"amount0Delta","type":"int256"},{"internalType":"int256","name":"amount1Delta","type":"int256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"uniswapV3SwapCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]'  # noqa
