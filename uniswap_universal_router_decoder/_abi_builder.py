"""
Factory that builds the UR function ABIs used by the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)
from typing import (
    Any,
    Callable,
    Dict,
    List,
)

from eth_utils import function_abi_to_4byte_selector

from uniswap_universal_router_decoder._enums import _RouterFunction


@dataclass(frozen=True)
class _FunctionABI:
    inputs: List[Any]
    name: str
    type: str

    def get_abi(self) -> Dict[str, Any]:
        return asdict(self)

    def get_struct_abi(self) -> Dict[str, Any]:
        result = asdict(self)
        result["components"] = result.pop("inputs")
        return result

    def get_full_abi(self) -> List[Dict[str, Any]]:
        return [self.get_abi()]


@dataclass(frozen=True)
class _FunctionDesc:
    fct_abi: _FunctionABI
    selector: bytes


_ABIMap = Dict[_RouterFunction, _FunctionDesc]


class _FunctionABIBuilder:
    def __init__(self, fct_name: str, _type: str = "function") -> None:
        self.abi = _FunctionABI(inputs=[], name=fct_name, type=_type)

    def add_address(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "address"})
        return self

    def add_uint256(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint256"})
        return self

    add_int = add_uint256

    def add_uint160(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint160"})
        return self

    def add_uint48(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint48"})
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
        self.abi.inputs.append(struct.abi.get_struct_abi())
        return self

    def add_bytes(self, arg_name: str) -> _FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bytes"})
        return self


class _ABIBuilder:
    def build_abi_map(self) -> _ABIMap:
        abi_map: _ABIMap = {
            # mapping between command identifier and fct descriptor (fct abi + selector)
            _RouterFunction.V3_SWAP_EXACT_IN: self._add_mapping(self._build_v3_swap_exact_in),
            _RouterFunction.V3_SWAP_EXACT_OUT: self._add_mapping(self._build_v3_swap_exact_out),
            _RouterFunction.V2_SWAP_EXACT_IN: self._add_mapping(self._build_v2_swap_exact_in),
            _RouterFunction.V2_SWAP_EXACT_OUT: self._add_mapping(self._build_v2_swap_exact_out),
            _RouterFunction.PERMIT2_PERMIT: self._add_mapping(self._build_permit2_permit),
            _RouterFunction.WRAP_ETH: self._add_mapping(self._build_wrap_eth),
            _RouterFunction.UNWRAP_WETH: self._add_mapping(self._build_unwrap_weth),
            _RouterFunction.SWEEP: self._add_mapping(self._build_sweep),
            _RouterFunction.PAY_PORTION: self._add_mapping(self._build_pay_portion),
            _RouterFunction.TRANSFER: self._add_mapping(self._build_transfer)
        }
        return abi_map

    @staticmethod
    def _add_mapping(build_abi_method: Callable[[], _FunctionABI]) -> _FunctionDesc:
        fct_abi = build_abi_method()
        selector = function_abi_to_4byte_selector(fct_abi.get_abi())  # type: ignore[arg-type, unused-ignore]
        return _FunctionDesc(fct_abi=fct_abi, selector=selector)

    @staticmethod
    def _build_v2_swap_exact_in() -> _FunctionABI:
        builder = _FunctionABIBuilder("V2_SWAP_EXACT_IN")
        builder.add_address("recipient").add_int("amountIn").add_int("amountOutMin").add_address_array("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_permit2_permit() -> _FunctionABI:
        builder = _FunctionABIBuilder("PERMIT2_PERMIT")
        inner_struct = builder.create_struct("details")
        inner_struct.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
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
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_v3_swap_exact_out() -> _FunctionABI:
        builder = _FunctionABIBuilder("V3_SWAP_EXACT_OUT")
        builder.add_address("recipient").add_int("amountOut").add_int("amountInMax").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_sweep() -> _FunctionABI:
        builder = _FunctionABIBuilder("SWEEP")
        return builder.add_address("token").add_address("recipient").add_int("amountMin").build()

    @staticmethod
    def _build_pay_portion() -> _FunctionABI:
        builder = _FunctionABIBuilder("PAY_PORTION")
        return builder.add_address("token").add_address("recipient").add_int("bips").build()

    @staticmethod
    def _build_transfer() -> _FunctionABI:
        builder = _FunctionABIBuilder("TRANSFER")
        return builder.add_address("token").add_address("recipient").add_uint256("value").build()
