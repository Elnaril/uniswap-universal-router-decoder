"""
Factory that builds the UR function ABIs used by the Uniswap Universal Router Codec

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from functools import wraps
from io import BytesIO
from typing import (
    Any,
    cast,
    Optional,
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


def _get_types_from_list(type_list: list[Any]) -> list[str]:
    types = []
    for item in type_list:
        if item["type"][:5] == "tuple":
            brackets = item["type"][5:]
            types.append(f"({','.join(_get_types_from_list(item['components']))}){brackets}")
        else:
            types.append(item["type"])
    return types


def build_abi_type_list(abi_dict: dict[str, Any]) -> list[str]:
    return _get_types_from_list(abi_dict["inputs"])


class FunctionABI:
    def __init__(self, inputs: list[Any], name: str, _type: str) -> None:
        self.inputs = inputs
        self.name = name
        self.type = _type

    def get_abi(self) -> dict[str, Any]:
        return {"inputs": self.inputs, "name": self.name, "type": self.type}

    def get_struct_abi(self) -> dict[str, Any]:
        result = self.get_abi()
        result["components"] = result.pop("inputs")
        return result

    def get_full_abi(self) -> list[dict[str, Any]]:
        return [self.get_abi()]

    def get_abi_types(self) -> list[str]:
        return build_abi_type_list(self.get_abi())

    def get_signature(self) -> str:
        return f"{self.name}({','.join(self.get_abi_types())})"

    def get_selector(self) -> bytes:
        return keccak(text=self.get_signature())[:4]

    def encode(self, args: Sequence[Any]) -> bytes:
        return encode(self.get_abi_types(), args)


ABIMap = dict[Union[MiscFunctions, RouterFunction, V4Actions], FunctionABI]


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

    def add_v4_exact_output_params(self, arg_name: str = "params") -> FunctionABIBuilder:
        self.abi.inputs.append({"name": arg_name, "type": "ExactOutputParams"})
        return self


class ABIRegister:
    abi_map: ABIMap = {}

    def __init__(self, enum_key: Union[MiscFunctions, RouterFunction, V4Actions]) -> None:
        self.enum_key = enum_key

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        ABIRegister.abi_map[self.enum_key] = func()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper


class ABIBuilder:
    def __init__(self, w3: Optional[Web3] = None) -> None:
        self.w3 = w3 if w3 else Web3()
        self.abi_map = ABIRegister.abi_map
        if not registry.has_encoder("ExactInputParams"):
            registry.register("ExactInputParams", self.encode_v4_exact_input_params, self.decode_v4_exact_input_params)
        if not registry.has_encoder("ExactOutputParams"):
            registry.register(
                "ExactOutputParams",
                self.encode_v4_exact_output_params,
                self.decode_v4_exact_output_params,
            )

    def decode_v4_exact_input_params(self, stream: BytesIO) -> dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.get_full_abi())
        fct_name, decoded_params = sub_contract.decode_function_input(fct_abi.get_selector() + raw_data[32:])
        return cast(dict[str, Any], decoded_params)

    def encode_v4_exact_input_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.get_abi_types(), args)
        return encoded_data

    def decode_v4_exact_output_params(self, stream: BytesIO) -> dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.get_full_abi())
        fct_name, decoded_params = sub_contract.decode_function_input(fct_abi.get_selector() + raw_data[32:])
        return cast(dict[str, Any], decoded_params)

    def encode_v4_exact_output_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.get_abi_types(), args)
        return encoded_data


@ABIRegister(RouterFunction.V2_SWAP_EXACT_IN)
def _build_v2_swap_exact_in() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_IN.name)
    builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_address_array("path")
    return builder.add_bool("payerIsSender").build()


@ABIRegister(RouterFunction.PERMIT2_PERMIT)
def _build_permit2_permit() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.PERMIT2_PERMIT.name)
    inner_struct = builder.create_struct("details")
    inner_struct.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
    outer_struct = builder.create_struct("struct")
    outer_struct.add_struct(inner_struct).add_address("spender").add_uint256("sigDeadline")
    return builder.add_struct(outer_struct).add_bytes("data").build()


@ABIRegister(RouterFunction.PERMIT2_PERMIT_BATCH)
def _build_permit2_permit_batch() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.PERMIT2_PERMIT_BATCH.name)
    inner_struct_array = builder.create_struct_array("details")
    inner_struct_array.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
    outer_struct = builder.create_struct("struct")
    outer_struct.add_struct_array(inner_struct_array).add_address("spender").add_uint256("sigDeadline")
    return builder.add_struct(outer_struct).add_bytes("data").build()


@ABIRegister(RouterFunction.UNWRAP_WETH)
def _build_unwrap_weth() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.UNWRAP_WETH.name)
    return builder.add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.V3_SWAP_EXACT_IN)
def _build_v3_swap_exact_in() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_IN.name)
    builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_bytes("path")
    return builder.add_bool("payerIsSender").build()


@ABIRegister(RouterFunction.WRAP_ETH)
def _build_wrap_eth() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.WRAP_ETH.name)
    return builder.add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.V2_SWAP_EXACT_OUT)
def _build_v2_swap_exact_out() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V2_SWAP_EXACT_OUT.name)
    builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_address_array("path")
    return builder.add_bool("payerIsSender").build()


@ABIRegister(RouterFunction.V3_SWAP_EXACT_OUT)
def _build_v3_swap_exact_out() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V3_SWAP_EXACT_OUT.name)
    builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_bytes("path")
    return builder.add_bool("payerIsSender").build()


@ABIRegister(RouterFunction.SWEEP)
def _build_sweep() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.SWEEP.name)
    return builder.add_address("token").add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.PAY_PORTION)
def _build_pay_portion() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.PAY_PORTION.name)
    return builder.add_address("token").add_address("recipient").add_uint256("bips").build()


@ABIRegister(RouterFunction.TRANSFER)
def _build_transfer() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.TRANSFER.name)
    return builder.add_address("token").add_address("recipient").add_uint256("value").build()


@ABIRegister(RouterFunction.V4_SWAP)
def _build_v4_swap() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V4_SWAP.name)
    return builder.add_bytes("actions").add_bytes_array("params").build()


def _v4_pool_key_struct_builder() -> FunctionABIBuilder:
    builder = FunctionABIBuilder.create_struct("PoolKey")
    builder.add_address("currency0").add_address("currency1").add_uint24("fee").add_int24("tickSpacing")
    return builder.add_address("hooks")


@ABIRegister(V4Actions.SWAP_EXACT_IN_SINGLE)
def _build_v4_swap_exact_in_single() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN_SINGLE.name)
    pool_key = _v4_pool_key_struct_builder()
    outer_struct = builder.create_struct("exact_in_single_params")
    outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountIn").add_uint128("amountOutMinimum")
    outer_struct.add_bytes("hookData")
    return builder.add_struct(outer_struct).build()


@ABIRegister(RouterFunction.V4_INITIALIZE_POOL)
def _build_v4_initialize_pool() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.V4_INITIALIZE_POOL.name)
    pool_key = _v4_pool_key_struct_builder()
    return builder.add_struct(pool_key).add_uint256("sqrtPriceX96").build()


@ABIRegister(RouterFunction.V4_POSITION_MANAGER_CALL)
def _build_modify_liquidities() -> FunctionABI:
    builder = FunctionABIBuilder("modifyLiquidities")
    return builder.add_bytes("unlockData").add_uint256("deadline").build()


@ABIRegister(MiscFunctions.UNLOCK_DATA)
def _build_unlock_data() -> FunctionABI:
    builder = FunctionABIBuilder("unlockData")
    return builder.add_bytes("actions").add_bytes_array("params").build()


@ABIRegister(V4Actions.MINT_POSITION)
def _build_v4_mint_position() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.MINT_POSITION.name)
    pool_key = _v4_pool_key_struct_builder()
    builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper").add_uint256("liquidity")
    builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
    return builder.build()


@ABIRegister(V4Actions.SETTLE_PAIR)
def _build_v4_settle_pair() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SETTLE_PAIR.name)
    return builder.add_address("currency0").add_address("currency1").build()


@ABIRegister(V4Actions.SETTLE)
def _build_v4_settle() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SETTLE.name)
    return builder.add_address("currency").add_uint256("amount").add_bool("payerIsUser").build()


@ABIRegister(V4Actions.CLOSE_CURRENCY)
def _build_v4_close_currency() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.CLOSE_CURRENCY.name)
    return builder.add_address("currency").build()


@ABIRegister(V4Actions.SWEEP)
def _build_v4_sweep() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SWEEP.name)
    return builder.add_address("currency").add_address("to").build()


@ABIRegister(RouterFunction.PERMIT2_TRANSFER_FROM)
def _build_permit2_transfer_from() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.PERMIT2_TRANSFER_FROM.name)
    return builder.add_address("token").add_address("recipient").add_uint256("amount").build()


def _allowance_transfer_details_struct_array_builder() -> FunctionABIBuilder:
    builder = FunctionABIBuilder.create_struct_array("AllowanceTransferDetails")
    return builder.add_address("from").add_address("to").add_uint160("amount").add_address("token")


@ABIRegister(RouterFunction.PERMIT2_TRANSFER_FROM_BATCH)
def _build_permit2_transfer_from_batch() -> FunctionABI:
    builder = FunctionABIBuilder(RouterFunction.PERMIT2_TRANSFER_FROM_BATCH.name)
    return builder.add_struct_array(_allowance_transfer_details_struct_array_builder()).build()


@ABIRegister(V4Actions.TAKE_ALL)
def _build_v4_take_all() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.TAKE_ALL.name)
    return builder.add_address("currency").add_uint256("minAmount").build()


@ABIRegister(V4Actions.SETTLE_ALL)
def _build_v4_settle_all() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SETTLE_ALL.name)
    return builder.add_address("currency").add_uint256("maxAmount").build()


@ABIRegister(MiscFunctions.EXECUTE)
def _build_execute() -> FunctionABI:
    builder = FunctionABIBuilder("execute")
    return builder.add_bytes("commands").add_bytes_array("inputs").build()


@ABIRegister(MiscFunctions.EXECUTE_WITH_DEADLINE)
def _build_execute_with_deadline() -> FunctionABI:
    builder = FunctionABIBuilder("execute")
    return builder.add_bytes("commands").add_bytes_array("inputs").add_uint256("deadline").build()


@ABIRegister(MiscFunctions.V4_POOL_ID)
def _build_v4_pool_id() -> FunctionABI:
    builder = FunctionABIBuilder("v4_pool_id")
    pool_key = _v4_pool_key_struct_builder()
    return builder.add_struct(pool_key).build()


def _v4_path_key_struct_array_builder() -> FunctionABIBuilder:
    builder = FunctionABIBuilder.create_struct_array("PathKeys")
    builder.add_address("intermediateCurrency").add_uint24("fee").add_int24("tickSpacing")
    return builder.add_address("hooks").add_bytes("hookData")


@ABIRegister(MiscFunctions.STRICT_V4_SWAP_EXACT_IN)
def _build_strict_v4_swap_exact_in() -> FunctionABI:
    builder = FunctionABIBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_IN.name)
    builder.add_address("currencyIn")
    builder.add_struct_array(_v4_path_key_struct_array_builder())
    return builder.add_uint128("amountIn").add_uint128("amountOutMinimum").build()


@ABIRegister(V4Actions.MINT_POSITION_FROM_DELTAS)
def _build_v4_mint_position_from_deltas() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.MINT_POSITION_FROM_DELTAS.name)
    pool_key = _v4_pool_key_struct_builder()
    builder.add_struct(pool_key).add_int24("tickLower").add_int24("tickUpper")
    builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
    return builder.build()


@ABIRegister(V4Actions.WRAP)
def _build_v4_wrap_eth() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.WRAP.name)
    return builder.add_uint256("amount").build()


@ABIRegister(V4Actions.UNWRAP)
def _build_v4_unwrap_weth() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.UNWRAP.name)
    return builder.add_uint256("amount").build()


@ABIRegister(V4Actions.SWAP_EXACT_OUT_SINGLE)
def _build_v4_swap_exact_out_single() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT_SINGLE.name)
    pool_key = _v4_pool_key_struct_builder()
    outer_struct = builder.create_struct("exact_out_single_params")
    outer_struct.add_struct(pool_key).add_bool("zeroForOne").add_uint128("amountOut").add_uint128("amountInMaximum")
    outer_struct.add_bytes("hookData")
    return builder.add_struct(outer_struct).build()


@ABIRegister(MiscFunctions.STRICT_V4_SWAP_EXACT_OUT)
def _build_strict_v4_swap_exact_out() -> FunctionABI:
    builder = FunctionABIBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_OUT.name)
    builder.add_address("currencyOut")
    builder.add_struct_array(_v4_path_key_struct_array_builder())
    return builder.add_uint128("amountOut").add_uint128("amountInMaximum").build()


@ABIRegister(V4Actions.TAKE_PAIR)
def _build_v4_take_pair() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.TAKE_PAIR.name)
    return builder.add_address("currency0").add_address("currency1").add_address("recipient").build()


@ABIRegister(V4Actions.CLEAR_OR_TAKE)
def _build_v4_clear_or_take() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.CLEAR_OR_TAKE.name)
    return builder.add_address("currency").add_uint256("amountMax").build()


@ABIRegister(V4Actions.TAKE_PORTION)
def _build_v4_take_portion() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.TAKE_PORTION.name)
    return builder.add_address("currency").add_address("recipient").add_uint256("bips").build()


@ABIRegister(V4Actions.TAKE)
def _build_v4_take() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.TAKE.name)
    return builder.add_address("currency").add_address("recipient").add_uint256("amount").build()


@ABIRegister(V4Actions.SWAP_EXACT_IN)
def _build_v4_swap_exact_in() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_IN.name)
    return builder.add_v4_exact_input_params().build()


@ABIRegister(V4Actions.SWAP_EXACT_OUT)
def _build_v4_swap_exact_out() -> FunctionABI:
    builder = FunctionABIBuilder(V4Actions.SWAP_EXACT_OUT.name)
    return builder.add_v4_exact_output_params().build()
