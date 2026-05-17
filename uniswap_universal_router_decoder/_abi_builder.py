"""
Factory that builds the UR function ABIs used by the Uniswap Universal Router Codec

* Author: Elnaril (elnaril_dev@caramail.com, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from __future__ import annotations

from collections.abc import (
    Callable,
    Sequence,
)
from dataclasses import dataclass
from functools import wraps
from io import BytesIO
from typing import (
    Any,
    cast,
    Literal,
    Optional,
    TypedDict,
    Union,
)

from eth_abi import encode
from eth_abi.registry import registry
from eth_utils import keccak
from typing_extensions import Self
from web3 import (
    AsyncHTTPProvider,
    AsyncWeb3,
    Web3,
)

from uniswap_universal_router_decoder._enums import (
    MiscFunctions,
    RouterFunction,
    V4Actions,
)


ABIParamDict = TypedDict("ABIParamDict", {"name": str, "type": str})
ABIStructDict = TypedDict(
    "ABIStructDict",
    {
        "components": list[Union[ABIParamDict, "ABIStructDict"]],
        "name": str,
        "type": str,
    },
)
ABIFunctionDict = TypedDict(
    "ABIFunctionDict",
    {
        "inputs": list[
            Union[
                ABIParamDict,
                ABIStructDict,
            ]
        ],
        "name": str,
        "type": str,
    }
)


@dataclass(frozen=True)
class ABIParam:
    name: str
    type: str

    def get_abi_as_dict(self) -> ABIParamDict:
        return {"name": self.name, "type": self.type}

    def get_types_as_str(self) -> str:
        return self.type


class ABIStruct:
    def __init__(self, name: str, type: Literal["tuple", "tuple[]"]) -> None:
        self.name = name
        self.type = type
        self.params: list[Union[ABIParam, ABIStruct]] = []

    def __repr__(self) -> str:
        return f"ABIStruct(name='{self.name}', type='{self.type}', params={self.params})"

    def get_abi_as_dict(self) -> ABIStructDict:
        return {
            "components": [param.get_abi_as_dict() for param in self.params],
            "name": self.name,
            "type": self.type,
        }

    def get_types_as_str(self) -> str:
        brackets = self.type[5:]
        return f"({','.join([param.get_types_as_str() for param in self.params])}){brackets}"


class ABIFunction:
    def __init__(self, name: str) -> None:
        self.name = name
        self.type: Literal["function"] = "function"
        self.params: list[Union[ABIParam, ABIStruct]] = []

        self.full_abi: list[ABIFunctionDict] = []
        self.type_list: list[str] = []
        self.signature: str = ""
        self.selector: bytes

    def __repr__(self) -> str:
        return f"ABIFunction(name='{self.name}', params={self.params})"

    def finalize(self) -> None:
        self.full_abi = [self.get_abi_as_dict()]
        self.type_list = [param.get_types_as_str() for param in self.params]
        self.signature = f"{self.name}({','.join(self.get_types_as_list())})"
        self.selector = keccak(text=self.signature)[:4]

    def get_abi_as_dict(self) -> ABIFunctionDict:
        return {
            "inputs": [param.get_abi_as_dict() for param in self.params],
            "name": self.name,
            "type": self.type,
        }

    def get_types_as_list(self) -> list[str]:
        return [param.get_types_as_str() for param in self.params]

    def encode(self, args: Sequence[Any]) -> bytes:
        return encode(self.get_types_as_list(), args)


def _get_types_from_list(type_list: list[Union[ABIParamDict, ABIStructDict]]) -> list[str]:
    types: list[str] = []
    for item in type_list:
        if item["type"][:5] == "tuple":
            item = cast(ABIStructDict, item)
            brackets = item["type"][5:]
            types.append(f"({','.join(_get_types_from_list(item['components']))}){brackets}")
        else:
            types.append(item["type"])
    return types


def build_abi_type_list(abi_dict: ABIFunctionDict) -> list[str]:
    return _get_types_from_list(abi_dict["inputs"])


ABIMap = dict[Union[MiscFunctions, RouterFunction, V4Actions], ABIFunction]


class CommonABIBuilder:
    def __init__(self, abi: Union[ABIFunction, ABIStruct]) -> None:
        self.abi = abi

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(abi={self.abi})"

    def add_address(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "address"))
        return self

    def add_uint256(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint256"))
        return self

    def add_uint160(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint160"))
        return self

    def add_uint48(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint48"))
        return self

    def add_uint24(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint24"))
        return self

    def add_int24(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "int24"))
        return self

    def add_uint128(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint128"))
        return self

    def add_address_array(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "address[]"))
        return self

    def add_bool(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "bool"))
        return self

    def add_bytes(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "bytes"))
        return self

    def add_bytes_array(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "bytes[]"))
        return self

    def add_uint256_array(self, arg_name: str) -> Self:
        self.abi.params.append(ABIParam(arg_name, "uint256[]"))
        return self

    @staticmethod
    def create_struct(struct_name: str) -> ABIStructBuilder:
        return ABIStructBuilder(struct_name, "tuple")

    @staticmethod
    def create_struct_array(struct_name: str) -> ABIStructBuilder:
        return ABIStructBuilder(struct_name, "tuple[]")

    def add_struct(self, struct_abi: ABIStruct) -> Self:
        self.abi.params.append(struct_abi)
        return self

    def add_struct_array(self, struct_abi: ABIStruct) -> Self:
        self.abi.params.append(struct_abi)
        return self


class ABIFunctionBuilder(CommonABIBuilder):
    abi: ABIFunction

    def __init__(self, fct_name: str) -> None:
        super().__init__(ABIFunction(name=fct_name))

    def build(self) -> ABIFunction:
        self.abi.finalize()
        return self.abi

    def add_v4_exact_input_params(self, arg_name: str = "params") -> ABIFunctionBuilder:
        self.abi.params.append(ABIParam(arg_name, "ExactInputParams"))
        return self

    def add_v4_exact_output_params(self, arg_name: str = "params") -> ABIFunctionBuilder:
        self.abi.params.append(ABIParam(arg_name, "ExactOutputParams"))
        return self


class ABIStructBuilder(CommonABIBuilder):
    abi: ABIStruct

    def __init__(self, struct_name: str, type: Literal["tuple", "tuple[]"]) -> None:
        super().__init__(ABIStruct(name=struct_name, type=type))

    def build(self) -> ABIStruct:
        return self.abi


class ABIRegister:
    abi_map: ABIMap = {}

    def __init__(self, enum_key: Union[MiscFunctions, RouterFunction, V4Actions]) -> None:
        self.enum_key = enum_key

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        ABIRegister.abi_map[self.enum_key] = func()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)  # for some reason, coverage reports this line as missed  # pragma: no cover
        return wrapper


class ABIMapWrapper:
    def __init__(self, w3: Optional[Union[AsyncWeb3[AsyncHTTPProvider], Web3]] = None) -> None:
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
        sub_contract = self.w3.eth.contract(abi=fct_abi.full_abi)
        _, decoded_params = sub_contract.decode_function_input(fct_abi.selector + raw_data[32:])
        return decoded_params

    def encode_v4_exact_input_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_IN]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.type_list, args)
        return encoded_data

    def decode_v4_exact_output_params(self, stream: BytesIO) -> dict[str, Any]:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        raw_data = stream.read()
        sub_contract = self.w3.eth.contract(abi=fct_abi.full_abi)
        _, decoded_params = sub_contract.decode_function_input(fct_abi.selector + raw_data[32:])
        return decoded_params

    def encode_v4_exact_output_params(self, args: Sequence[Any]) -> bytes:
        fct_abi = self.abi_map[MiscFunctions.STRICT_V4_SWAP_EXACT_OUT]
        encoded_data = 0x20.to_bytes(32, "big") + encode(fct_abi.type_list, args)
        return encoded_data


@ABIRegister(RouterFunction.V2_SWAP_EXACT_IN)
def build_v2_swap_exact_in() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V2_SWAP_EXACT_IN.name)
    builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_address_array("path")
    return builder.add_bool("payerIsSender").add_uint256_array("minHopPriceX36").build()


@ABIRegister(RouterFunction.PERMIT2_PERMIT)
def build_permit2_permit() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.PERMIT2_PERMIT.name)
    inner_struct = builder.create_struct("details")
    inner_struct.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
    outer_struct = builder.create_struct("struct")
    outer_struct.add_struct(inner_struct.build()).add_address("spender").add_uint256("sigDeadline")
    return builder.add_struct(outer_struct.build()).add_bytes("data").build()


@ABIRegister(RouterFunction.PERMIT2_PERMIT_BATCH)
def build_permit2_permit_batch() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.PERMIT2_PERMIT_BATCH.name)
    inner_struct_array = builder.create_struct_array("details")
    inner_struct_array.add_address("token").add_uint160("amount").add_uint48("expiration").add_uint48("nonce")
    outer_struct = builder.create_struct("struct")
    outer_struct.add_struct_array(inner_struct_array.build()).add_address("spender").add_uint256("sigDeadline")
    return builder.add_struct(outer_struct.build()).add_bytes("data").build()


@ABIRegister(RouterFunction.UNWRAP_WETH)
def build_unwrap_weth() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.UNWRAP_WETH.name)
    return builder.add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.V3_SWAP_EXACT_IN)
def build_v3_swap_exact_in() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V3_SWAP_EXACT_IN.name)
    builder.add_address("recipient").add_uint256("amountIn").add_uint256("amountOutMin").add_bytes("path")
    return builder.add_bool("payerIsSender").add_uint256_array("minHopPriceX36").build()


@ABIRegister(RouterFunction.WRAP_ETH)
def build_wrap_eth() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.WRAP_ETH.name)
    return builder.add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.V2_SWAP_EXACT_OUT)
def build_v2_swap_exact_out() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V2_SWAP_EXACT_OUT.name)
    builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_address_array("path")
    return builder.add_bool("payerIsSender").add_uint256_array("minHopPriceX36").build()


@ABIRegister(RouterFunction.V3_SWAP_EXACT_OUT)
def build_v3_swap_exact_out() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V3_SWAP_EXACT_OUT.name)
    builder.add_address("recipient").add_uint256("amountOut").add_uint256("amountInMax").add_bytes("path")
    return builder.add_bool("payerIsSender").add_uint256_array("minHopPriceX36").build()


@ABIRegister(RouterFunction.SWEEP)
def build_sweep() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.SWEEP.name)
    return builder.add_address("token").add_address("recipient").add_uint256("amountMin").build()


@ABIRegister(RouterFunction.PAY_PORTION)
def build_pay_portion() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.PAY_PORTION.name)
    return builder.add_address("token").add_address("recipient").add_uint256("bips").build()


@ABIRegister(RouterFunction.TRANSFER)
def build_transfer() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.TRANSFER.name)
    return builder.add_address("token").add_address("recipient").add_uint256("value").build()


@ABIRegister(RouterFunction.V4_SWAP)
def build_v4_swap() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V4_SWAP.name)
    return builder.add_bytes("actions").add_bytes_array("params").build()


def _v4_pool_key_struct_builder() -> ABIStructBuilder:
    builder = CommonABIBuilder.create_struct("PoolKey")
    builder.add_address("currency0").add_address("currency1").add_uint24("fee").add_int24("tickSpacing")
    return builder.add_address("hooks")


@ABIRegister(V4Actions.SWAP_EXACT_IN_SINGLE)
def build_v4_swap_exact_in_single() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SWAP_EXACT_IN_SINGLE.name)
    pool_key_builder = _v4_pool_key_struct_builder()
    outer_struct = builder.create_struct("exact_in_single_params")
    outer_struct.add_struct(pool_key_builder.build()).add_bool("zeroForOne").add_uint128("amountIn")
    outer_struct.add_uint128("amountOutMinimum").add_uint256("minHopPriceX36").add_bytes("hookData")
    return builder.add_struct(outer_struct.build()).build()


@ABIRegister(RouterFunction.V4_INITIALIZE_POOL)
def build_v4_initialize_pool() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.V4_INITIALIZE_POOL.name)
    pool_key_builder = _v4_pool_key_struct_builder()
    return builder.add_struct(pool_key_builder.build()).add_uint256("sqrtPriceX96").build()


@ABIRegister(RouterFunction.V4_POSITION_MANAGER_CALL)
def build_modify_liquidities() -> ABIFunction:
    builder = ABIFunctionBuilder("modifyLiquidities")
    return builder.add_bytes("unlockData").add_uint256("deadline").build()


@ABIRegister(MiscFunctions.UNLOCK_DATA)
def build_unlock_data() -> ABIFunction:
    builder = ABIFunctionBuilder("unlockData")
    return builder.add_bytes("actions").add_bytes_array("params").build()


@ABIRegister(V4Actions.MINT_POSITION)
def build_v4_mint_position() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.MINT_POSITION.name)
    pool_key_builder = _v4_pool_key_struct_builder()
    builder.add_struct(pool_key_builder.build()).add_int24("tickLower").add_int24("tickUpper").add_uint256("liquidity")
    builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
    return builder.build()


@ABIRegister(V4Actions.SETTLE_PAIR)
def build_v4_settle_pair() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SETTLE_PAIR.name)
    return builder.add_address("currency0").add_address("currency1").build()


@ABIRegister(V4Actions.SETTLE)
def build_v4_settle() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SETTLE.name)
    return builder.add_address("currency").add_uint256("amount").add_bool("payerIsUser").build()


@ABIRegister(V4Actions.CLOSE_CURRENCY)
def build_v4_close_currency() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.CLOSE_CURRENCY.name)
    return builder.add_address("currency").build()


@ABIRegister(V4Actions.SWEEP)
def build_v4_sweep() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SWEEP.name)
    return builder.add_address("currency").add_address("to").build()


@ABIRegister(RouterFunction.PERMIT2_TRANSFER_FROM)
def build_permit2_transfer_from() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.PERMIT2_TRANSFER_FROM.name)
    return builder.add_address("token").add_address("recipient").add_uint256("amount").build()


def _allowance_transfer_details_struct_array_builder() -> ABIStructBuilder:
    builder = CommonABIBuilder.create_struct_array("AllowanceTransferDetails")
    return builder.add_address("from").add_address("to").add_uint160("amount").add_address("token")


@ABIRegister(RouterFunction.PERMIT2_TRANSFER_FROM_BATCH)
def build_permit2_transfer_from_batch() -> ABIFunction:
    builder = ABIFunctionBuilder(RouterFunction.PERMIT2_TRANSFER_FROM_BATCH.name)
    allowance_transfer_details_builder = _allowance_transfer_details_struct_array_builder()
    return builder.add_struct_array(allowance_transfer_details_builder.build()).build()


@ABIRegister(V4Actions.TAKE_ALL)
def build_v4_take_all() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.TAKE_ALL.name)
    return builder.add_address("currency").add_uint256("minAmount").build()


@ABIRegister(V4Actions.SETTLE_ALL)
def build_v4_settle_all() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SETTLE_ALL.name)
    return builder.add_address("currency").add_uint256("maxAmount").build()


@ABIRegister(MiscFunctions.EXECUTE)
def build_execute() -> ABIFunction:
    builder = ABIFunctionBuilder("execute")
    return builder.add_bytes("commands").add_bytes_array("inputs").build()


@ABIRegister(MiscFunctions.EXECUTE_WITH_DEADLINE)
def build_execute_with_deadline() -> ABIFunction:
    builder = ABIFunctionBuilder("execute")
    return builder.add_bytes("commands").add_bytes_array("inputs").add_uint256("deadline").build()


@ABIRegister(MiscFunctions.V4_POOL_ID)
def build_v4_pool_id() -> ABIFunction:
    builder = ABIFunctionBuilder("v4_pool_id")
    pool_key_builder = _v4_pool_key_struct_builder()
    return builder.add_struct(pool_key_builder.build()).build()


def _v4_path_key_struct_array_builder() -> ABIStructBuilder:
    builder = CommonABIBuilder.create_struct_array("PathKeys")
    builder.add_address("intermediateCurrency").add_uint24("fee").add_int24("tickSpacing")
    return builder.add_address("hooks").add_bytes("hookData")


@ABIRegister(MiscFunctions.STRICT_V4_SWAP_EXACT_IN)
def build_strict_v4_swap_exact_in() -> ABIFunction:
    builder = ABIFunctionBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_IN.name)
    builder.add_address("currencyIn")
    v4_path_key_builder = _v4_path_key_struct_array_builder()
    builder.add_struct_array(v4_path_key_builder.build())
    builder.add_uint256_array("minHopPriceX36")
    return builder.add_uint128("amountIn").add_uint128("amountOutMinimum").build()


@ABIRegister(V4Actions.MINT_POSITION_FROM_DELTAS)
def build_v4_mint_position_from_deltas() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.MINT_POSITION_FROM_DELTAS.name)
    pool_key_builder = _v4_pool_key_struct_builder()
    builder.add_struct(pool_key_builder.build()).add_int24("tickLower").add_int24("tickUpper")
    builder.add_uint128("amount0Max").add_uint128("amount1Max").add_address("recipient").add_bytes("hookData")
    return builder.build()


@ABIRegister(V4Actions.WRAP)
def build_v4_wrap_eth() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.WRAP.name)
    return builder.add_uint256("amount").build()


@ABIRegister(V4Actions.UNWRAP)
def build_v4_unwrap_weth() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.UNWRAP.name)
    return builder.add_uint256("amount").build()


@ABIRegister(V4Actions.SWAP_EXACT_OUT_SINGLE)
def build_v4_swap_exact_out_single() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SWAP_EXACT_OUT_SINGLE.name)
    pool_key_builder = _v4_pool_key_struct_builder()
    outer_struct = builder.create_struct("exact_out_single_params")
    outer_struct.add_struct(pool_key_builder.build()).add_bool("zeroForOne").add_uint128("amountOut")
    outer_struct.add_uint128("amountInMaximum").add_uint256("minHopPriceX36").add_bytes("hookData")
    return builder.add_struct(outer_struct.build()).build()


@ABIRegister(MiscFunctions.STRICT_V4_SWAP_EXACT_OUT)
def build_strict_v4_swap_exact_out() -> ABIFunction:
    builder = ABIFunctionBuilder(MiscFunctions.STRICT_V4_SWAP_EXACT_OUT.name)
    builder.add_address("currencyOut")
    v4_path_key_builder = _v4_path_key_struct_array_builder()
    builder.add_struct_array(v4_path_key_builder.build())
    builder.add_uint256_array("minHopPriceX36")
    return builder.add_uint128("amountOut").add_uint128("amountInMaximum").build()


@ABIRegister(V4Actions.TAKE_PAIR)
def build_v4_take_pair() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.TAKE_PAIR.name)
    return builder.add_address("currency0").add_address("currency1").add_address("recipient").build()


@ABIRegister(V4Actions.CLEAR_OR_TAKE)
def build_v4_clear_or_take() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.CLEAR_OR_TAKE.name)
    return builder.add_address("currency").add_uint256("amountMax").build()


@ABIRegister(V4Actions.TAKE_PORTION)
def build_v4_take_portion() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.TAKE_PORTION.name)
    return builder.add_address("currency").add_address("recipient").add_uint256("bips").build()


@ABIRegister(V4Actions.TAKE)
def build_v4_take() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.TAKE.name)
    return builder.add_address("currency").add_address("recipient").add_uint256("amount").build()


@ABIRegister(V4Actions.SWAP_EXACT_IN)
def build_v4_swap_exact_in() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SWAP_EXACT_IN.name)
    return builder.add_v4_exact_input_params().build()


@ABIRegister(V4Actions.SWAP_EXACT_OUT)
def build_v4_swap_exact_out() -> ABIFunction:
    builder = ABIFunctionBuilder(V4Actions.SWAP_EXACT_OUT.name)
    return builder.add_v4_exact_output_params().build()
