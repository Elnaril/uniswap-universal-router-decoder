"""
Factory that builds the UR function ABIs used by the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from io import BytesIO
from typing import (
    Any,
    cast,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
)

from eth_abi import encode
from eth_abi.registry import registry
from eth_utils import keccak
from web3 import Web3

from uniswap_universal_router_decoder._enums import (
    MiscFunctions,
    RouterFunction,
    V4Actions,
)


def _get_types_from_list(type_list: List[Any]) -> List[str]:
    types = []
    for item in type_list:
        if item["type"][:5] == "tuple":
            brackets = item["type"][5:]
            types.append(f"({','.join(_get_types_from_list(item['components']))}){brackets}")
        else:
            types.append(item["type"])
    return types


def build_abi_type_list(abi_dict: Dict[str, Any]) -> List[str]:
    return _get_types_from_list(abi_dict["inputs"])


class FunctionABI:
    def __init__(self, inputs: List[Any], name: str, _type: str) -> None:
        self.inputs = inputs
        self.name = name
        self.type = _type

    def get_abi(self) -> Dict[str, Any]:
        return {"inputs": self.inputs, "name": self.name, "type": self.type}

    def get_struct_abi(self) -> Dict[str, Any]:
        result = self.get_abi()
        result["components"] = result.pop("inputs")
        return result

    def get_full_abi(self) -> List[Dict[str, Any]]:
        return [self.get_abi()]

    def get_abi_types(self) -> List[str]:
        return build_abi_type_list(self.get_abi())

    def get_signature(self) -> str:
        return f"{self.name}({','.join(self.get_abi_types())})"

    def get_selector(self) -> bytes:
        return keccak(text=self.get_signature())[:4]

    def encode(self, args: Sequence[Any]) -> bytes:
        return encode(self.get_abi_types(), args)


ABIMap = Dict[Union[MiscFunctions, RouterFunction, V4Actions], FunctionABI]


class FunctionABIBuilder:
    def __init__(self, fct_name: str, _type: str = "function") -> None:
        self.abi = FunctionABI(inputs=[], name=fct_name, _type=_type)

    def add_address(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "address"})
        return self

    def add_uint256(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint256"})
        return self

    def add_uint160(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint160"})
        return self

    def add_uint48(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint48"})
        return self

    def add_uint24(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint24"})
        return self

    def add_int24(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "int24"})
        return self

    def add_uint128(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "uint128"})
        return self

    def add_address_array(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "address[]"})
        return self

    def add_bool(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bool"})
        return self

    def build(self) -> FunctionABI:
        return self.abi

    @staticmethod
    def create_struct_array(arg_name: str) -> FunctionABIBuilder:
        return FunctionABIBuilder(arg_name, "tuple[]")

    @staticmethod
    def create_struct(arg_name: str) -> FunctionABIBuilder:
        return FunctionABIBuilder(arg_name, "tuple")

    def add_struct(self, struct: FunctionABIBuilder) -> FunctionABIBuilder:
        self.abi.inputs.append(struct.abi.get_struct_abi())
        return self

    def add_struct_array(self, struct_array: FunctionABIBuilder) -> FunctionABIBuilder:
        self.abi.inputs.append(struct_array.abi.get_struct_abi())
        return self

    def add_bytes(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bytes"})
        return self

    def add_bytes_array(self, arg_name: str) -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "bytes[]"})
        return self

    def add_v4_exact_input_params(self, arg_name: str = "params") -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "ExactInputParams"})
        return self


class _ABIBuilder:
    def __init__(self, w3: Optional[Web3] = None) -> None:
        self.w3 = w3 if w3 else Web3()
        self.abi_map = self.build_abi_map()
        if not registry.has_encoder("ExactInputParams"):
            registry.register("ExactInputParams", self.encode_v4_exact_input_params, self.decode_v4_exact_input_params)

    def build_abi_map(self) -> ABIMap:
        abi_map: ABIMap = {
            # mapping between command identifier and function abi
            RouterFunction.V3_SWAP_EXACT_IN: self._build_v3_swap_exact_in(),
            RouterFunction.V3_SWAP_EXACT_OUT: self._build_v3_swap_exact_out(),
            RouterFunction.V2_SWAP_EXACT_IN: self._build_v2_swap_exact_in(),
            RouterFunction.V2_SWAP_EXACT_OUT: self._build_v2_swap_exact_out(),
            RouterFunction.PERMIT2_PERMIT: self._build_permit2_permit(),
            RouterFunction.WRAP_ETH: self._build_wrap_eth(),
            RouterFunction.UNWRAP_WETH: self._build_unwrap_weth(),
            RouterFunction.SWEEP: self._build_sweep(),
            RouterFunction.PAY_PORTION: self._build_pay_portion(),
            RouterFunction.TRANSFER: self._build_transfer(),
            RouterFunction.V4_SWAP: self._build_v4_swap(),
            RouterFunction.V4_INITIALIZE_POOL: self._build_v4_initialize_pool(),
            RouterFunction.V4_POSITION_MANAGER_CALL: self._build_modify_liquidities(),
            RouterFunction.PERMIT2_TRANSFER_FROM: self._build_permit2_transfer_from(),

            V4Actions.SWAP_EXACT_IN_SINGLE: self._build_v4_swap_exact_in_single(),
            V4Actions.MINT_POSITION: self._build_v4_mint_position(),
            V4Actions.SETTLE_PAIR: self._build_v4_settle_pair(),
            V4Actions.SETTLE: self._build_v4_settle(),
            V4Actions.CLOSE_CURRENCY: self._build_v4_close_currency(),
            V4Actions.SWEEP: self._build_v4_sweep(),
            V4Actions.TAKE_ALL: self._build_v4_take_all(),
            V4Actions.SETTLE_ALL: self._build_v4_settle_all(),
            V4Actions.SWAP_EXACT_IN: self._build_v4_swap_exact_in(),
            V4Actions.MINT_POSITION_FROM_DELTAS: self._build_v4_mint_position_from_deltas(),
            V4Actions.WRAP: self._build_v4_wrap_eth(),
            V4Actions.UNWRAP: self._build_v4_unwrap_weth(),
            V4Actions.SWAP_EXACT_OUT_SINGLE: self._build_v4_swap_exact_out_single(),
            V4Actions.SWAP_EXACT_OUT: self._build_v4_swap_exact_out(),
            V4Actions.TAKE_PAIR: self._build_v4_take_pair(),
            V4Actions.CLEAR_OR_TAKE: self._build_v4_clear_or_take(),
            V4Actions.TAKE_PORTION: self._build_v4_take_portion(),
            V4Actions.TAKE: self._build_v4_take(),

            MiscFunctions.EXECUTE: self._build_execute(),
            MiscFunctions.EXECUTE_WITH_DEADLINE: self._build_execute_with_deadline(),
            MiscFunctions.UNLOCK_DATA: self._build_unlock_data(),
            MiscFunctions.V4_POOL_ID: self._build_v4_pool_id(),
            MiscFunctions.STRICT_V4_SWAP_EXACT_IN: self._build_strict_v4_swap_exact_in(),
        }
        return abi_map

    @staticmethod
    def _build_v2_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_IN.name)
        builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_address_array("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_permit2_permit() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PERMIT2_PERMIT.name)
        inner_struct = builder.create_struct("details")
        inner_struct.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
        outer_struct = builder.create_struct("struct")
        outer_struct.add_struct(inner_struct).add_address("spender").add_uint256("sigDeadline")
        return builder.add_struct(outer_struct).add_bytes("data").build()

    @staticmethod
    def _build_unwrap_weth() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.UNWRAP_WETH.name)
        return builder.add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_v3_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_IN.name)
        builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_wrap_eth() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.WRAP_ETH.name)
        return builder.add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_v2_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_OUT.name)
        builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_address_array("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_v3_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_OUT.name)
        builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_bytes("path")
        return builder.add_bool("payerIsSender").build()

    @staticmethod
    def _build_sweep() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.SWEEP.name)
        return builder.add_address("token").add_address("recipient").add_uint256("amountMin").build()

    @staticmethod
    def _build_pay_portion() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PAY_PORTION.name)
        return builder.add_address("token").add_address("recipient").add_uint256("bips").build()

    @staticmethod
    def _build_transfer() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.TRANSFER.name)
        return builder.add_address("token").add_address("recipient").add_uint256("value").build()

    @staticmethod
    def _build_v4_swap() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V4_SWAP.name)
        return builder.add_bytes("actions").add_bytes_array("params").build()

    @staticmethod
    def _v4_pool_key_struct_builder() -> FunctionABIBuilder:
        builder = FunctionABIBuilder.create_struct("PoolKey")
        builder.add_address("currency0").add_address("currency1").add_uint24("fee").add_int24("tickSpacing")
        return builder.add_address("hooks")

    @staticmethod
    def _build_v4_swap_exact_in_single() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN_SINGLE.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        outer_struct = builder.create_struct("exact_in_single_params")
        outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountIn").add_uint128("amountOutMinimum")
        outer_struct.add_bytes("hookData")
        return builder.add_struct(outer_struct).build()

    @staticmethod
    def _build_v4_initialize_pool() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.V4_INITIALIZE_POOL.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        return builder.add_struct(pool_key).add_uint256("sqrtPriceX96").build()

    @staticmethod
    def _build_modify_liquidities() -> FunctionABI:
        builder = FunctionABIBuilder("modifyLiquidities")
        return builder.add_bytes("unlockData").add_uint256("deadline").build()

    @staticmethod
    def _build_unlock_data() -> FunctionABI:
        builder = FunctionABIBuilder("unlockData")
        return builder.add_bytes("actions").add_bytes_array("params").build()

    @staticmethod
    def _build_v4_mint_position() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.MINT_POSITION.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper").add_uint256("liquidity")
        builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
        return builder.build()

    @staticmethod
    def _build_v4_settle_pair() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE_PAIR.name)
        return builder.add_address("currency0").add_address("currency1").build()

    @staticmethod
    def _build_v4_settle() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE.name)
        return builder.add_address("currency").add_uint256("amount").add_bool("payerIsUser").build()

    @staticmethod
    def _build_v4_close_currency() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.CLOSE_CURRENCY.name)
        return builder.add_address("currency").build()

    @staticmethod
    def _build_v4_sweep() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWEEP.name)
        return builder.add_address("currency").add_address("to").build()

    @staticmethod
    def _build_permit2_transfer_from() -> FunctionABI:
        builder = FunctionABIBuilder(RouterFunction.PERMIT2_TRANSFER_FROM.name)
        return builder.add_address("token").add_address("recipient").add_uint256("amount").build()

    @staticmethod
    def _build_v4_take_all() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_ALL.name)
        return builder.add_address("currency").add_uint256("minAmount").build()

    @staticmethod
    def _build_v4_settle_all() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SETTLE_ALL.name)
        return builder.add_address("currency").add_uint256("maxAmount").build()

    @staticmethod
    def _build_execute() -> FunctionABI:
        builder = FunctionABIBuilder("execute")
        return builder.add_bytes("commands").add_bytes_array("inputs").build()

    @staticmethod
    def _build_execute_with_deadline() -> FunctionABI:
        builder = FunctionABIBuilder("execute")
        return builder.add_bytes("commands").add_bytes_array("inputs").add_uint256("deadline").build()

    @staticmethod
    def _build_v4_pool_id() -> FunctionABI:
        builder = FunctionABIBuilder("v4_pool_id")
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        return builder.add_struct(pool_key).build()

    @staticmethod
    def _v4_path_key_struct_array_builder() -> FunctionABIBuilder:
        builder = FunctionABIBuilder.create_struct_array("PathKeys")
        builder.add_address("intermediateCurrency").add_uint24("fee").add_int24("tickSpacing")
        return builder.add_address("hooks").add_bytes("hookData")

    @staticmethod
    def _build_strict_v4_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder("STRICT_SWAP_EXACT_IN")
        builder.add_address("currencyIn")
        builder.add_struct_array(_ABIBuilder._v4_path_key_struct_array_builder())
        return builder.add_uint128("amountIn").add_uint128("amountOutMinimum").build()

    @staticmethod
    def _build_v4_mint_position_from_deltas() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.MINT_POSITION_FROM_DELTAS.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper")
        builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
        return builder.build()

    @staticmethod
    def _build_v4_wrap_eth() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.WRAP.name)
        return builder.add_uint256("amount").build()

    @staticmethod
    def _build_v4_unwrap_weth() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.UNWRAP.name)
        return builder.add_uint256("amount").build()

    @staticmethod
    def _build_v4_swap_exact_out_single() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT_SINGLE.name)
        pool_key = _ABIBuilder._v4_pool_key_struct_builder()
        outer_struct = builder.create_struct("exact_out_single_params")
        outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountOut").add_uint128("amountInMaximum")
        outer_struct.add_bytes("hookData")
        return builder.add_struct(outer_struct).build()

    @staticmethod
    def _build_v4_swap_exact_out() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT.name)
        builder.add_address("currencyOut")
        builder.add_struct_array(_ABIBuilder._v4_path_key_struct_array_builder())
        return builder.add_uint128("amountOut").add_uint128("amountInMaximum").build()

    @staticmethod
    def _build_v4_take_pair() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_PAIR.name)
        return builder.add_address("currency0").add_address("currency1").add_address("recipient").build()

    @staticmethod
    def _build_v4_clear_or_take() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.CLEAR_OR_TAKE.name)
        return builder.add_address("currency").add_uint256("amountMax").build()

    @staticmethod
    def _build_v4_take_portion() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE_PORTION.name)
        return builder.add_address("currency").add_address("recipient").add_uint256("bips").build()

    @staticmethod
    def _build_v4_take() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.TAKE.name)
        return builder.add_address("currency").add_address("recipient").add_uint256("amount").build()

    @staticmethod
    def _build_v4_swap_exact_in() -> FunctionABI:
        builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN.name)
        return builder.add_v4_exact_input_params().build()

    def decode_v4_exact_input_params(self, stream: BytesIO) -> Dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.get_full_abi())
        fct_name, decoded_params = sub_contract.decode_function_input(fct_abi.get_selector() + raw_data[32:])
        return cast(Dict[str, Any], decoded_params)

    def encode_v4_exact_input_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.get_abi_types(), args)
        return encoded_data
