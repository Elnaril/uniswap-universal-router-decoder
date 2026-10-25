# Uniswap Universal Router Decoder & Encoder

<!-- mcp-name: io.github.Elnaril/uniswap-universal-router-decoder -->

> Many thanks to **everyone** who has ☕️ [offered some **coffees**!](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions/11) ☕️
> or ⭐ [**starred** this project!](https://github.com/Elnaril/uniswap-universal-router-decoder/stargazers) ⭐  
> It is **greatly** appreciated! :)

---

<p align="center">
  <img width="75%" src="https://raw.githubusercontent.com/Elnaril/uniswap-universal-router-decoder/master/python_uniswap_universal_router_sdk_small.jpg">
</p>


---


#### Project Information
[![Tests & Lint](https://github.com/Elnaril/uniswap-universal-router-decoder/actions/workflows/tests.yml/badge.svg)](https://github.com/Elnaril/uniswap-universal-router-decoder/actions/workflows/tests.yml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/uniswap-universal-router-decoder)](https://pypi.org/project/uniswap-universal-router-decoder/)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Elnaril/uniswap-universal-router-decoder)](https://github.com/Elnaril/uniswap-universal-router-decoder/releases)
[![PyPi Repository](https://img.shields.io/badge/repository-pipy.org-blue)](https://pypi.org/project/uniswap-universal-router-decoder/)
[![GitHub](https://img.shields.io/github/license/Elnaril/uniswap-universal-router-decoder)](https://github.com/Elnaril/uniswap-universal-router-decoder/blob/master/LICENSE)

#### Code Quality
[![CodeQL](https://github.com/elnaril/uniswap-universal-router-decoder/workflows/CodeQL/badge.svg)](https://github.com/Elnaril/uniswap-universal-router-decoder/actions/workflows/github-code-scanning/codeql)
[![Test Coverage](https://img.shields.io/badge/dynamic/json?color=blueviolet&label=coverage&query=%24.totals.percent_covered_display&suffix=%25&url=https%3A%2F%2Fraw.githubusercontent.com%2FElnaril%2Funiswap-universal-router-decoder%2Fmaster%2Fcoverage.json)](https://github.com/Elnaril/uniswap-universal-router-decoder/blob/master/coverage.json)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type Checker: basedpyright](https://img.shields.io/badge/%20type%20checker-basedpyright-%231674b1?style=flat&labelColor=ef8336)](https://docs.basedpyright.com/)
[![Linter: flake8](https://img.shields.io/badge/%20linter-flake8-%231674b1?style=flat&labelColor=ef8336)](https://flake8.pycqa.org/en/latest/)

---

## Release Notes
See the [release notes page](https://github.com/Elnaril/uniswap-universal-router-decoder/wiki/Release_Notes)

### v4.0.0 - breaking changes
- Update COMMAND_TYPE_MASK to 0x7f to match UR
- Add support for the PAY_PORTION_FULL_PRECISION command (0x07)
- Add support for the BALANCE_CHECK_ERC20 command (0x0e)
- Add support for the V3_POSITION_MANAGER_PERMIT command (0x11)
- Add support for the V3_POSITION_MANAGER_CALL command (0x12)
- Add support for the EXECUTE_SUB_PLAN command (0x21)
- Add `revert_on_fail` to the encoder methods for the commands whose failure the UR can tolerate
- Make the chained function builders public and expose the `encoder` & `decoder` modules
- Reduce CI time
- Add a `publish.yml` GitHub Actions workflow that automatically publishes the package to PyPI and the MCP Registry with OIDC
  Trusted Publishing
- Agent-friendly changes:
  - Add `Encoder.function_input()` / `AsyncEncoder.function_input()` to rebuild the calldata from a decoded call
  - Add `decoded_input_to_dict()` and `transaction_to_dict()` to render the decoder output as JSON-friendly dicts
  - Add the `ur-decode` and `ur-encode` command line tools, including `ur-encode v3-path` and its `encode_v3_path` MCP
    counterpart
  - Add the `ur-mcp` MCP server (optional `mcp` extra) so AI agents can drive the codec
  - The command descriptions (`ur-encode list` / `describe` and the `list_commands` / `describe_command` MCP tools) now
    describe the decoded call format and its ABI parameters, instead of the encoder methods
  - Add the MCP Registry metadata (`server.json`) to make the `ur-mcp` server discoverable
  - Add `AGENTS.md` and `llms.txt` for AI agents, plus a `mcp` PyPI keyword
  - Add `tests/test_version_consistency.py` to keep the packaging version, `server.json` and the README `mcp-name:`
    marker in sync

### v3.1.0
- Update UR address and abi to match v2.1.2
- Add support for web3 v8

### v3.0.0 - breaking changes
- Update UR address and abi to match v2.1.1
- Add support for UR v2.1.1 swaps
- Add async support
- Remove support for Python 3.9
- Remove support for Web3 < 7.14
- Full pyproject.toml support (remove requirements.txt files)
- Replace Mypy with Basedpyright
- Refactor abi builder - part 2
- Improve typing
- Add pep-561 marker file (py.typed)
- Add tick, sqrtPriceX96, and liquidity related functions
- Possibility to call directly the encoder i/o using chain()
- Make `decode.transaction()` and `decode.function_input()` outputs consistent

---

## Overview and Points of Attention

The object of this library is to decode & encode transactions sent to the Uniswap Universal Router (UR)
on Ethereum Mainnet, though it would work on any compatible chain where the UR is deployed. See Version Mapping below.
This Python SDK is based on, and intended to be used with [web3.py](https://github.com/ethereum/web3.py)

The target audience is Python developers who are familiar with the Ethereum blockchain concepts and web3.py, and how DEXes work.
The same codec is also available without Python, through the `ur-decode` / `ur-encode` command line tools and the optional
`ur-mcp` MCP server (see "Command line interface" and "MCP server" below): both print JSON, so shell scripts and AI
agents can drive it too.

⚠ Before using this library, ensure you are familiar with general blockchain concepts. The Python API also expects
[web3.py](https://github.com/ethereum/web3.py) knowledge in particular.

⚠ Not all UR functions supported by this SDK are available through the CLI or MCP tools: 
run `ur-encode list` and look for the "rebuildable" flag.

### List of supported Uniswap Universal Router Functions

| Command Id  | Universal Router Function   | Underlying Action - Function | Supported |
|-------------|-----------------------------|------------------------------|:---------:|
| 0x00        | V3_SWAP_EXACT_IN            |                              |     ✅     |
| 0x01        | V3_SWAP_EXACT_OUT           |                              |     ✅     |
| 0x02        | PERMIT2_TRANSFER_FROM       |                              |     ✅     |
| 0x03        | PERMIT2_PERMIT_BATCH        |                              |     ✅     |
| 0x04        | SWEEP                       |                              |     ✅     |
| 0x05        | TRANSFER                    |                              |     ✅     |
| 0x06        | PAY_PORTION                 |                              |     ✅     |
| 0x07        | PAY_PORTION_FULL_PRECISION  |                              |     ✅     |
| 0x08        | V2_SWAP_EXACT_IN            |                              |     ✅     |
| 0x09        | V2_SWAP_EXACT_OUT           |                              |     ✅     |
| 0x0a        | PERMIT2_PERMIT              |                              |     ✅     |
| 0x0b        | WRAP_ETH                    |                              |     ✅     |
| 0x0c        | UNWRAP_WETH                 |                              |     ✅     |
| 0x0d        | PERMIT2_TRANSFER_FROM_BATCH |                              |     ✅     |
| 0x0e        | BALANCE_CHECK_ERC20         |                              |     ✅     |
| 0x0f        | placeholder                 |                              |    N/A    |
| 0x10        | V4_SWAP                     |                              |     ✅     |
|             |                             | 0x06 - SWAP_EXACT_IN_SINGLE  |     ✅     |
|             |                             | 0x07 - SWAP_EXACT_IN         |     ✅     |
|             |                             | 0x08 - SWAP_EXACT_OUT_SINGLE |     ✅     |
|             |                             | 0x09 - SWAP_EXACT_OUT        |     ✅     |
|             |                             | 0x0b - SETTLE                |     ✅     |
|             |                             | 0x0c - SETTLE_ALL            |     ✅     |
|             |                             | 0x0e - TAKE                  |     ✅     |
|             |                             | 0x0f - TAKE_ALL              |     ✅     |
|             |                             | 0x10 - TAKE_PORTION          |     ✅     |
| 0x11        | V3_POSITION_MANAGER_PERMIT  |                              |     ✅     |
| 0x12        | V3_POSITION_MANAGER_CALL    |                              |     ✅     |
| 0x13        | V4_INITIALIZE_POOL          |                              |     ✅     |
| 0x14        | V4_POSITION_MANAGER_CALL    |                              |     ✅     |
|             |                             | 0x02 - MINT_POSITION         |     ✅     |
|             |                             | 0x0b - SETTLE                |     ✅     |
|             |                             | 0x0d - SETTLE_PAIR           |     ✅     |
|             |                             | 0x0e - TAKE                  |     ✅     |
|             |                             | 0x11 - TAKE_PAIR             |     ✅     |
|             |                             | 0x12 - CLOSE_CURRENCY        |     ✅     |
|             |                             | 0x13 - CLEAR_OR_TAKE         |     ✅     |
|             |                             | 0x14 - SWEEP                 |     ✅     |
|             |                             | 0x15 - WRAP                  |     ✅     |
|             |                             | 0x16 - UNWRAP                |     ✅     |
| 0x15 - 0x20 | placeholders                |                              |    N/A    |
| 0x21        | EXECUTE_SUB_PLAN            |                              |     ✅     |
| 0x22 - 0x3f | placeholders                |                              |    N/A    |
| 0x40        | ACROSS_V4_DEPOSIT_V3        |                              |     ❌     |

All the ✅ commands can be decoded and encoded. `V4_SWAP`, `V4_POSITION_MANAGER_CALL` and `EXECUTE_SUB_PLAN` can also
be decoded, but they cannot be rebuilt from a decoded call (see "How to rebuild the calldata from a decoded call").


### Version Mapping
Here is the mapping between the Universal Router versions and the SDK ones

| UR Version | UR address on Ethereum | Python SDK version|
|:----------:|------------|:-----------------:|
| v2.1.2     | [`0x23617e59A5925b2A4Bf75d73ff6711cD0b29De85`](https://etherscan.io/address/0x23617e59A5925b2A4Bf75d73ff6711cD0b29De85) | v3.1.0 |
| v2.1.1     | [`0x4C82D1fBFe28C977cBB58D8C7FF8FCF9F70a2cCA`](https://etherscan.io/address/0x4C82D1fBFe28C977cBB58D8C7FF8FCF9F70a2cCA) | v3.0.0 |
| v2         | [`0x66a9893cC07D91D95644AEDD05D03f95e1dBA8Af`](https://etherscan.io/address/0x66a9893cC07D91D95644AEDD05D03f95e1dBA8Af) | v2.0.0 & v2.1.0 |
| v1.2         | [`0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD`](https://etherscan.io/address/0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD) | v0.9.0 to v1.2.1 |
| v1         | [`0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B`](https://etherscan.io/address/0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B) | v0.8.0 |

---

## Installation
A good practice is to use [Python virtual environments](https://python.readthedocs.io/en/latest/library/venv.html), here is a [tutorial](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).

The library can be pip installed from [pypi.org](https://pypi.org/project/uniswap-universal-router-decoder/) as usual:

```bash
# update pip to latest version if needed
pip install -U pip

# install the decoder from pypi.org
pip install uniswap-universal-router-decoder
```

To install it from source:
```bash
pip install .
```

or for contributors:
```bash
pip install -e '.[mcp]' --group dev
```

---

## Usage

The library exposes 2 classes, `RouterCodec` and `AsyncRouterCodec` with several public methods 
that can be used to decode or encode UR data and transactions.  
Both `RouterCodec` and `AsyncRouterCodec` are used the same way but either synchronously 
or asynchronously for the relevant parts, ie when doing rpc calls.

### How to instantiate the router codec

1/ When no need for rpc calls  
```python
from web3 import Web3
from uniswap_universal_router_decoder import RouterCodec
codec = RouterCodec()
```

2/ Using the URL of an rpc endpoint  

Sync code:
```python
# Using an rpc endpoint
from uniswap_universal_router_decoder import RouterCodec
rpc_link = "https://..."  # your rpc endpoint
codec = RouterCodec(rpc_endpoint=rpc_link)
```

Async code:
```python
# Using an rpc endpoint
from uniswap_universal_router_decoder import AsyncRouterCodec
rpc_link = "https://..."  # your rpc endpoint
codec = AsyncRouterCodec(rpc_endpoint=rpc_link)
```

3/ Using a Web3/AsyncWeb3 instance  

Sync code:
```python
# Using a web3 instance
from web3 import Web3
from uniswap_universal_router_decoder import RouterCodec
w3 = Web3(...)  # your Web3 instance
codec = RouterCodec(w3=w3)
```

Async code:
```python
# Using an AsyncWeb3 instance
from web3 import AsyncWeb3
from uniswap_universal_router_decoder import AsyncRouterCodec
async_w3 = AsyncWeb3(...)  # your AsyncWeb3 instance
codec = AsyncRouterCodec(async_w3=async_w3)
```

### How to decode a Uniswap Universal Router transaction input
To decode a transaction input, use the `decode.function_input()` method as follows:

```python
from uniswap_universal_router_decoder import RouterCodec

trx_input = "0x3593564c000000000000000000 ... 90095b5c4e9f5845bba"  # the trx input to decode
codec = RouterCodec()
decoded_trx_input = codec.decode.function_input(trx_input)
```

Example of decoded input returned by `decode.function_input()`:
```python
(
    <Function execute(bytes,bytes[],uint256)>,  # the UR function that executes all commands
    {
        'commands': b'\x0b\x00',  # the list of commands sent to the UR
        'inputs': [  # the inputs used for each command
            (
                <Function WRAP_ETH(address,uint256)>,  # the function corresponding to the first command
                {                                      # and its parameters
                    'recipient': '0x0000000000000000000000000000000000000002',  # code indicating the recipient of this command is the router
                    'amountMin': 4500000000000000000  # the amount in WEI to wrap
                },
                {
                    'revert_on_fail': True  # flag indicating if the transaction must revert when this command fails
                },
            ),
            (
                <Function V3_SWAP_EXACT_IN(address,uint256,uint256,bytes,bool)>,  # the function corresponding to the second command
                {                                                                 # and its parameters
                    'recipient': '0x0000000000000000000000000000000000000001',  # code indicating the sender will receive the output of this command
                    'amountIn': 4500000000000000000,  # the exact amount sent
                    'amountOutMin': 6291988002,  # the min amount expected of the bought token for the swap to be executed
                    'path': b"\xc0*\xaa9\xb2#\xfe\x8d\n\x0e\\O'\xea\xd9\x08<ul\xc2"  # the V3 path (tokens + pool fees)
                           b'\x00\x01\xf4\xa0\xb8i\x91\xc6!\x8b6\xc1\xd1\x9dJ.'  # can be decoded with the method decode.v3_path()
                           b'\x9e\xb0\xce6\x06\xebH',
                    'payerIsSender': False  # a bool indicating if the input tokens come from the sender or are already in the UR
                },
                {
                    'revert_on_fail': True  # flag indicating if the transaction must revert when this command fails
                },
            )
        ],
        'deadline': 1678441619  # The deadline after which the transaction is no longer valid
    }
)
```
> **Tip**: You can format the decoded input like above with this [Gedit plugin](https://github.com/Elnaril/gedit-plugin-collection?tab=readme-ov-file#prettifier) ;) 

### How to decode a Uniswap Universal Router transaction
It's also possible to decode the whole transaction, given its hash 
and providing the codec has been built with either a valid `Web3` instance or the link to a rpc endpoint.

The decoder will get the transaction from the blockchain and decode it, along with its input data:
```python
# sync code
trx_hash = "0x52e63b7 ... 11b979dd9"
decoded_transaction = codec.decode.transaction(trx_hash)
```

```python
# async code
trx_hash = "0x52e63b7 ... 11b979dd9"
decoded_transaction = await codec.decode.transaction(trx_hash)
```

### How to encode/decode a Uniswap V3 swap path
`RouterCodec` exposes two mirror methods: `encode.v3_path()` builds a Uniswap V3 path from the ordered tokens and the
pool fees between them, and `decode.v3_path()` reads one back.

```python
from uniswap_universal_router_decoder import RouterCodec

codec = RouterCodec()
fn_name = "V3_SWAP_EXACT_IN"  # Or V3_SWAP_EXACT_OUT

encoded_path = codec.encode.v3_path(fn_name, [token_in_address, 3000, token_out_address])  # bytes

uniswap_v3_path = b"\xc0*\xaa9\xb2#\xfe\x8d\n\x0e ... \xd7\x89"  # bytes or str hex
decoded_path = codec.decode.v3_path(fn_name, uniswap_v3_path)
```
`decode.v3_path()` returns a tuple, starting with the "in-token" and ending with the "out-token", with the pool fees
between each pair. Both methods use that same order: `V3_SWAP_EXACT_OUT` reverses the path when encoding, and the
decoder reverses it back.


### How to get the decoded data as JSON-friendly dicts
The decoder returns rich Python objects (web3 contract functions, raw bytes, ...) that are not directly serialisable.
Two helpers render that output as plain dicts/lists/strings, ready to be printed as JSON or sent to another system:

- `decoded_input_to_dict()` takes the output of `decode.function_input()`
- `transaction_to_dict()` takes the output of `decode.transaction()`

```python
import json
from uniswap_universal_router_decoder import RouterCodec, decoded_input_to_dict, transaction_to_dict

codec = RouterCodec()

# from the decoded input
decoded_input = codec.decode.function_input(trx_input)
print(json.dumps(decoded_input_to_dict(decoded_input), indent=2))

# or from the decoded transaction
decoded_transaction = codec.decode.transaction(trx_hash)
print(json.dumps(transaction_to_dict(decoded_transaction), indent=2))
```

Bytes are rendered as "0x"-prefixed hex strings, and each decoded command becomes a dict with a `command` name,
its `params`, and a `revert_on_fail` flag:
```json
{
  "function": "execute",
  "params": {
    "commands": "0x0b00",
    "inputs": [
      {
        "command": "WRAP_ETH",
        "params": {"recipient": "0x0000000000000000000000000000000000000002", "amountMin": 4500000000000000000},
        "revert_on_fail": true
      }
    ],
    "deadline": 1678441619
  }
}
```


### How to encode
The Uniswap Universal Router allows the chaining of several functions in the same transaction.
This codec supports it (at least for supported functions) and exposes public methods that can be chained.

The chaining starts with the `encode.chain()` method and ends with the `build()` one which returns the full encoded data to be included in the transaction.
Below some examples of encoded data for one function and one example for 2 functions.  
Starting with v3.0.0, it is possible to start the chaining with `encode()` instead of `encode.chain()`, making the code a bit more concise.

Default values for deadlines and expirations can be computed with the static methods `get_default_deadline()` and `get_default_expiration()` respectively.
```python
from uniswap_universal_router_decoder import RouterCodec

default_deadline = RouterCodec.get_default_deadline()
default_expiration = RouterCodec.get_default_expiration()

```
These 2 functions accept a custom duration in seconds as argument.

`revert_on_fail` can be passed to the methods whose command the UR can tolerate failing: `permit2_permit()`,
`permit2_permit_batch()`, `balance_check_erc20()`, `v3_position_manager_permit()`, `v3_decrease_liquidity()`,
`v3_collect()`, `v3_burn()`, `v4_initialize_pool()`, `build_v4_posm_call()` and `execute_sub_plan()`. It defaults to
`True`; set it to `False` to let the transaction continue if that command fails. The other methods don't accept it,
because the UR ignores that flag for their command.


### How to rebuild the calldata from a decoded call
As an alternative to chaining the encoder methods, `encode.function_input()` builds the calldata from the decoded form
of an `execute` call. It is the mirror of `decode.function_input()`: where the decoder turns a function input into
commands, this turns the decoded commands back into a function input, so a route can be decoded, edited, and re-encoded.

The expected shape is the one produced by `decoded_input_to_dict()` (and by the `ur-decode` CLI and the MCP server):
its `params.inputs` hold the commands, using the names and parameters the decoder reports (the Universal Router ABI
names).
```python
from uniswap_universal_router_decoder import RouterCodec, decoded_input_to_dict

codec = RouterCodec()
plan = decoded_input_to_dict(codec.decode.function_input(trx_input))

# tweak the decoded route, then rebuild the calldata from it
plan["params"]["inputs"][0]["params"]["amountMin"] = 2 * 10 ** 18
encoded_data = codec.encode.function_input(plan)

# then in your transaction dict:
transaction["data"] = encoded_data
```

The `function` key is optional and defaults to `execute`, and the `commands` bytes are ignored: the command list is
rebuilt from the `inputs` entries. The `deadline` key is optional too; when it is absent, the plain
`execute(bytes,bytes[])` form is used instead of `execute(bytes,bytes[],uint256)`.

Commands the decoder expands into structures (`V4_SWAP`, `V4_POSITION_MANAGER_CALL`, `EXECUTE_SUB_PLAN`) cannot be
rebuilt this way and raise a `ValueError`.

`revert_on_fail` is honoured only for the commands whose failure the UR can tolerate (`PERMIT2_PERMIT`,
`PERMIT2_PERMIT_BATCH`, `BALANCE_CHECK_ERC20`, `V3_POSITION_MANAGER_PERMIT`, `V3_POSITION_MANAGER_CALL`,
`V4_INITIALIZE_POOL`, `V4_POSITION_MANAGER_CALL`, `EXECUTE_SUB_PLAN`). For every other command the UR ignores the
flag, so it is always cleared. The same applies to the encoder methods: those commands take a `revert_on_fail`
argument (default `True`), the others do not.

`AsyncRouterCodec` exposes the same method (`encode.function_input()`); it is synchronous, so no `await` is needed.


### How to encode a call to the Uniswap Universal Router function WRAP_ETH
This function can be used to convert eth to weth using the UR.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().wrap_eth(FunctionRecipient.SENDER, amount_in_wei).build(1676825611)  # to convert amount_in_wei eth to weth, and send them to the transaction sender.

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### How to encode a call to the Uniswap V2 function V2_SWAP_EXACT_IN
This function can be used to swap tokens on a V2 pool. Correct allowances must have been set before sending such transaction.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().v2_swap_exact_in(
        FunctionRecipient.SENDER,  # the output tokens are sent to the transaction sender
        amount_in,  # in Wei
        min_amount_out,  # in Wei
        [
            in_token_address,  # checksum address of the token sent to the UR 
            out_token_address,  # checksum address of the received token
        ],
    ).build(timestamp)  # unix timestamp after which the trx will not be valid any more

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```
For more details, see this [tutorial](https://hackernoon.com/how-to-buy-a-token-on-the-uniswap-universal-router-with-python)

### How to encode a call to the Uniswap V2 function V2_SWAP_EXACT_OUT
This function can be used to swap tokens on a V2 pool. Correct allowances must have been set before sending such transaction.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().v2_swap_exact_out(
        FunctionRecipient.SENDER,
        amount_out,  # in Wei
        max_amount_in,  # in Wei
        [
            in_token_address,
            out_token_address,
        ],
    ).build(timestamp)  # unix timestamp after which the trx will not be valid any more

# then in your transaction dict:
transaction["data"] = encoded_data
# you can now sign and send the transaction to the UR
```

### How to encode a call to the Uniswap V3 function V3_SWAP_EXACT_IN
This function can be used to swap tokens on a V3 pool. Correct allowances must have been set before sending such transaction.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().v3_swap_exact_in(
        FunctionRecipient.SENDER,
        amount_in,  # in Wei
        min_amount_out,  # in Wei
        [
            in_token_address,
            pool_fee,
            out_token_address,
        ],
    ).build(timestamp)  # unix timestamp after which the trx will not be valid any more

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### How to encode a call to the Uniswap V3 function V3_SWAP_EXACT_OUT
This function can be used to swap tokens on a V3 pool. Correct allowances must have been set before sending such transaction.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().v3_swap_exact_out(
        FunctionRecipient.SENDER,
        amount_out,  # in Wei
        max_amount_in,  # in Wei
        [
            in_token_address,
            pool_fee,
            out_token_address,
        ],
    ).build(timestamp)  # unix timestamp after which the trx will not be valid any more

# then in your transaction dict:
transaction["data"] = encoded_data
# you can now sign and send the transaction to the UR
```

### How to encode a call to the Uniswap Universal Router function PERMIT2_PERMIT
This function is used to give an allowance to the universal router via the Permit2 contract ([`0x000000000022D473030F116dDEE9F6B43aC78BA3`](https://etherscan.io/address/0x000000000022D473030F116dDEE9F6B43aC78BA3)).
It is also necessary to approve the Permit2 contract using the token approve function.
See this [tutorial](https://hackernoon.com/python-how-to-use-permit2-with-the-uniswap-universal-router)
```python
from uniswap_universal_router_decoder import RouterCodec

codec = RouterCodec()
data, signable_message = codec.create_permit2_signable_message(
    token_address,
    amount,  # max = 2**160 - 1
    expiration,
    nonce,  # Permit2 nonce, see below how to get it
    spender,  # The UR checksum address
    deadline,
    1,  # chain id
)

# Then you need to sign the message:
signed_message = acc.sign_message(signable_message)  # where acc is your LocalAccount

# And now you can encode the data:
encoded_data = codec.encode.chain().permit2_permit(data, signed_message).build(deadline)

# Then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```
After that, you can swap tokens using the Uniswap universal router.

#### How to get the current permit2 allowance, expiration and nonce
You can get the nonce you need to build the permit2 signable message like this:
```python
amount, expiration, nonce = codec.fetch_permit2_allowance(acc.address, token_address)  # where acc is your LocalAccount
```

### How to chain a call to PERMIT2_PERMIT and V2_SWAP_EXACT_IN in the same transaction
Don't forget to give a token allowance to the Permit2 contract as well.

```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()

# Permit signature
data, signable_message = codec.create_permit2_signable_message(
    token_address,
    amount,  # max = 2**160 - 1
    expiration,
    nonce,  # Permit2 nonce
    spender,  # The UR checksum address
    deadline,
    1,  # chain id
)

# Then you need to sign the message:
signed_message = acc.sign_message(signable_message)  # where acc is your LocalAccount

# Permit + v2 swap encoding
path = [token_in_address, token_out_address]
encoded_data = (
    codec
        .encode
        .chain()
        .permit2_permit(data, signed_message)
        .v2_swap_exact_in(FunctionRecipient.SENDER, Wei(10**18), Wei(0), path)
        .build(deadline)
)

# Then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### Uniswap V4 Functions
#### How to build a Uniswap V4 pool key
PoolKey is used to identify a pool. 
```python
from uniswap_universal_router_decoder import RouterCodec
codec = RouterCodec()

pool_key = codec.encode.v4_pool_key(
    token_0_address,  # or "0x0000000000000000000000000000000000000000" for ETH
    token_1_address,
    fee,  # ex: 3000
    tick_spacing,  # ex: 60
    hooks,  # address or "0x0000000000000000000000000000000000000000"
)
```

#### How to build a Uniswap V4 path key
PathKey is used to identify pools in a multi-hop swaps.
```python
from uniswap_universal_router_decoder import RouterCodec
codec = RouterCodec()

path_key = codec.encode.v4_path_key(
        intermediate_token_address,
        fee,  # ex: 3000
        tick_spacing,  # ex: 60
        hooks,  # address or "0x0000000000000000000000000000000000000000"
        hook_data,  # ex: b"" if no data
    )
```

#### How to encode a Uniswap V4 pool id
Pool ids are used by V4 contracts to identify pools. For example, you'll need it to request the `StateView` contract.
```python
from uniswap_universal_router_decoder import RouterCodec
codec = RouterCodec()

pool_id = codec.encode.v4_pool_id(pool_key=pool_key)
```

#### How to initialize a Uniswap V4 pool with the Universal Router function V4_INITIALIZE_POOL
```python
trx_params = (
        codec
        .encode
        .chain()
        .v4_initialize_pool(pool_key, 1, 1)
        .build_transaction(sender_address, ur_address=ur_address)
    )
```

#### How to mint a Uniswap V4 position with the Universal Router function V4_POSITION_MANAGER_CALL
Example where a position on a ETH/TOKEN pool is minted between tick_0 and tick_1

```python
from uniswap_universal_router_decoder import V4Constants

trx_params = (
    codec.
    encode.
    chain().
    permit2_transfer_from(  # send tokens to the V4 position manager. UR needs to be permit2'ed
        FunctionRecipient.CUSTOM,
        token_address,
        token_amount,
        posm_address
    ).
    v4_pm_call().  # start encoding the V4 position manager call
        mint_position(
            pool_key,  # a PoolKey object
            tick_0,
            tick_1,
            liquidity,  # the provided liquidity
            amount_0_max,  # slippage protection
            amount_1_max,  # slippage protection
            sender_address,
            hook_data,  # or b"" if no hook data
        ).
        settle(token_address, V4Constants.OPEN_DELTA.value, False).
        close_currency(eth_address).  # eth address is "0x0000000000000000000000000000000000000000"
        sweep(eth_address, sender_address).  # get back unused ETH
        sweep(token_address, sender_address).    # get back unused tokens
        build_v4_pm_call(codec.get_default_deadline()).  # build the V4 position manager call
    build_transaction(  # build the UR transaction (see "How to build directly a transaction")
        sender_address,
        eth_amount,
        ur_address=ur_address,
    )
)
```

#### How to perform a Uniswap V4 swap with the Universal Router function V4_SWAP
###### Example using the V4 SWAP_EXACT_IN_SINGLE function to swap ETH for a token
```python
pool_key = codec.encode.v4_pool_key(
    eth_address,  # "0x0000000000000000000000000000000000000000"
    token_address,
    pool_fee,  # ex: 3000
    tick_spacing,  # ex: 60
)

trx_params = (
    codec.
    encode.
    chain().
    v4_swap().
        swap_exact_in_single(
            pool_key=pool_key,
            zero_for_one=True,
            amount_in=eth_amount,
            amount_out_min=token_amount_min,
        ).
        take_all(token_address, Wei(0)).
        settle_all(eth_address, eth_amount).  # with eth_address = "0x0000000000000000000000000000000000000000"
        build_v4_swap().
    build_transaction(account.address, eth_amount, ur_address=ur_address)
)

raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
trx_hash = w3.eth.send_raw_transaction(raw_transaction)
```

###### Example using the V4 SWAP_EXACT_IN function to swap ETH for a token through 2 pools
path: eth -> token a -> token b

```python
path_key_eth_token_a = codec.encode.v4_path_key(
    token_a_address,
    fee,
    tick_spacing,
)
path_key_token_a_token_b = codec.encode.v4_path_key(
    token_b_address,
    fee,
    tick_spacing,
)

trx_params = (
    codec.
    encode.
    chain().
    v4_swap().
        swap_exact_in(
            eth_address,
            [path_key_eth_token_a, path_key_token_a_token_b],
            amount_in,
            amount_out_min,
        ).
        take_all(token_b_address, Wei(0)).
        settle_all(eth_address, amount_in).
        build_v4_swap().
    build_transaction(
        account.address,
        amount_in,
        ur_address=ur_address,
    )
)
```


### Other chainable functions
(See integration tests for full examples) 

#### PAY_PORTION
Example where a recipient is paid 1% of the USDC amount:
```python
.pay_portion(FunctionRecipient.CUSTOM, usdc_address, 100, recipient_address)

```
#### PAY_PORTION_FULL_PRECISION
Same as PAY_PORTION but with full precision, where 10**18 represents 100%.
Example where a recipient is paid 50% of the USDC amount:
```python
.pay_portion_full_precision(FunctionRecipient.CUSTOM, usdc_address, 5 * 10**17, recipient_address)

```
#### SWEEP
Example where the sender gets back all remaining USDC:
```python
.sweep(FunctionRecipient.SENDER, usdc_address, 0)
```

#### TRANSFER
Example where a USDC amount is sent to a recipient:
```python
.transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount, recipient_address)
```

#### BALANCE_CHECK_ERC20
Reverts if the owner's balance of the given ERC20 token is lower than the minimum amount.
Example where the router must hold at least 1 USDC:
```python
.balance_check_erc20(ur_address, usdc_address, 1 * 10 ** 6)
```

#### EXECUTE_SUB_PLAN
Executes a nested plan of commands. The Universal Router calls itself to run the sub-plan, so its commands
are executed in the same transaction and share the same context (recipients, balances, ...).
The sub-plan is built with `encode.chain()` just like the main plan.
Example where a sub-plan transferring USDC is nested in the main plan:
```python
sub_plan = codec.encode.chain().transfer(FunctionRecipient.SENDER, usdc_address, usdc_amount)
codec.encode.chain().execute_sub_plan(sub_plan).build()
```

#### V3_POSITION_MANAGER_PERMIT
Approves a spender for a specific V3 position (NFT) using an EIP-712 signature instead of a transaction.
The signable message is built with `create_v3_position_manager_permit_signable_message()`, then signed.
Example where the spender is approved for the position `token_id`:
```python
permit_params, signable_message = codec.create_v3_position_manager_permit_signable_message(
    spender_address,
    token_id,
    nonce,  # the current nonce of the V3 position
    deadline,
)
signed_message = acc.sign_message(signable_message)  # where acc is your LocalAccount
codec.encode.chain().v3_position_manager_permit(permit_params, signed_message).build(deadline)
```

#### V3_POSITION_MANAGER_CALL
Calls one of the 3 V3 position manager functions the UR allows: `decreaseLiquidity`, `collect` or `burn`.
Only one function can be called per V3_POSITION_MANAGER_CALL command: the UR forwards the input as a single
call and rejects anything else (including `multicall`). To run several of them, chain several commands in the
same transaction (see the integration test).
The UR must be approved for the position first (see V3_POSITION_MANAGER_PERMIT).

- `decreaseLiquidity` removes liquidity from the position. The freed tokens are NOT sent out: they are recorded
  as `tokensOwed0`/`tokensOwed1` on the position, together with ALL the fees earned since the last update
  (fees are not prorated, even if only part of the liquidity is removed).
- `collect` sends `min(amountMax, tokensOwed)` to the recipient. `tokensOwed` holds both the principal freed by
  `decreaseLiquidity` and the fees, so `collect` alone harvests the fees without touching the liquidity.
- `burn` deletes the position (NFT). It requires the position to be empty (`liquidity == 0` and
  `tokensOwed0 == tokensOwed1 == 0`), hence the usual `decreaseLiquidity` -> `collect` -> `burn` order.

Note: `increaseLiquidity` and `mint` are not reachable through the UR (only the 3 functions above are allowed),
they must be called directly on the V3 position manager.

Example where the liquidity of a V3 position is decreased:
```python
.v3_decrease_liquidity(
    token_id,      # the id of the V3 position (NFT)
    liquidity,     # the amount of liquidity to remove
    amount_0_min,  # the minimum amount of token0 the decrease must free (kept as tokensOwed0, not sent out)
    amount_1_min,  # the minimum amount of token1 the decrease must free (kept as tokensOwed1, not sent out)
    deadline,      # when this call is not valid anymore
)
```
Example where the tokens owed to a V3 position are collected:
```python
.v3_collect(
    token_id,           # the id of the V3 position (NFT)
    recipient_address,  # the address receiving the collected tokens
    amount_0_max,       # the maximum amount of token0 to collect
    amount_1_max,       # the maximum amount of token1 to collect
)
```
Example where an empty V3 position is burned:
```python
.v3_burn(
    token_id,  # the id of the V3 position (NFT)
)
```

#### PERMIT2_TRANSFER_FROM
To use this function, the Universal Router needs to be `PERMIT2`'ed.  
Example where 1 `WETH` is transferred from the caller address to the v4 position manager
```python
.permit2_transfer_from(FunctionRecipient.CUSTOM, weth_address, Wei(1 * 10 ** 18), v4_posm_address)
```

### PERMIT2_PERMIT_BATCH & PERMIT2_TRANSFER_FROM_BATCH
Check the corresponding integration tests for an example of how to use these functions.


### How to build directly a transaction to the Uniswap Universal Router
The SDK provides a handy method to build very easily the full transaction in addition to the input data.
It can compute most of the transaction parameters (if the codec has been instantiated with a valid w3 or rpc url) 
or you can provide them.  

> See the corresponding integration tests for an async example

Example where a swap is encoded and a transaction is built automatically:
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec(w3)
trx_params = (
    codec.encode.chain().v2_swap_exact_in(
        FunctionRecipient.SENDER,  # the output tokens are sent to the transaction sender
        amount_in,  # in Wei
        min_amount_out,  # in Wei
        [
            in_token_address,  # checksum address of the token sent to the UR 
            out_token_address,  # checksum address of the received token
        ],
    ).build_transaction(
        sender_address,  # 'from'
        deadline=timestamp,  # the swap deadline
    )
)

```
And that's it! You can now sign and send this transaction.
A few other important parameters:
 - `value`: the quantity of ETH in wei you send to the Universal Router (for example when you wrap them before a swap)
 - `trx_speed`: an enum which influences the transaction rank in the block. Values are:
    - `TransactionSpeed.SLOW`
    - `TransactionSpeed.AVERAGE`
    - `TransactionSpeed.FAST` (default)
    - `TransactionSpeed.FASTER`
 - `max_fee_per_gas_limit`: if the computed `max_fee_per_gas` is greater than `max_fee_per_gas_limit` a `ValueError` will be raised to allow you to stay in control. Default is 100 gwei.

How to use the `trx_speed` parameter:
```python
from uniswap_universal_router_decoder import TransactionSpeed

.build_transaction(sender_address, trx_speed=TransactionSpeed.FASTER)
```

### Command line interface
The package installs two commands that print JSON to stdout, handy for shell scripts or to let an agent drive the codec:

- `ur-encode`: describe the decoded call format and the commands, rebuild calldata from a decoded call, or encode a V3 path
- `ur-decode`: decode a transaction, raw calldata, a custom error or a V3 path

```bash
# describe the decoded call format and the commands, then describe one of them
ur-encode list
ur-encode describe V3_SWAP_EXACT_IN

# rebuild the calldata of one command, from its name and parameters as decoded (see ur-decode)
ur-encode build --command WRAP_ETH --params '{"recipient": "0x0000000000000000000000000000000000000001", "amountMin": 1000000000000000000}'

# or of several commands at once, from a decoded call in a JSON file (or '-' for stdin)
ur-encode build --plan decoded_call.json --deadline 1676825611

# encode a V3 path: the tokens to swap through, with the pool fees between them
ur-encode v3-path V3_SWAP_EXACT_IN 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 3000 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

# the same path given as a JSON list
ur-encode v3-path V3_SWAP_EXACT_OUT '[0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2, 3000, 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48]'

# decode raw calldata
ur-decode calldata 0x3593564c0000...

# decode a transaction (needs an rpc endpoint via --rpc or the RPC_URL env var)
ur-decode tx 0x52e63b7... --rpc https://...
```

A plan file holds a decoded `execute` call, exactly as `ur-decode calldata` prints it:
```json
{
  "function": "execute",
  "params": {
    "inputs": [
      {"command": "WRAP_ETH", "params": {"recipient": "0x0000000000000000000000000000000000000001", "amountMin": 1000000000000000000}}
    ],
    "deadline": 1676825611
  }
}
```

### MCP server
The optional `mcp` extra installs `ur-mcp`, a side-effect free [Model Context
Protocol](https://modelcontextprotocol.io) server that exposes the codec to AI agents over stdio. Its tools only
inspect or derive Universal Router data: they never sign or broadcast a transaction.

```bash
pip install 'uniswap-universal-router-decoder[mcp]'
```

It provides seven tools:
- `list_commands` / `describe_command`: discover the decoded call format and the commands
- `decode_transaction`: fetch and decode a transaction sent to the UR (needs an RPC endpoint)
- `decode_calldata`, `decode_error`, `decode_v3_path`, `encode_v3_path`: decode/encode data without an RPC endpoint

`decode_transaction` uses the `rpc_url` tool argument, or the `RPC_URL` / `ETH_RPC_URL` environment variables, so a
host can be pointed at any chain by configuring the server environment.

To wire it into an MCP host (Zed, Claude Desktop, ...):
```json
{
  "mcpServers": {
    "uniswap-universal-router-decoder": {
      "command": "ur-mcp",  # or absolute path to ur-mcp in your virtual env.
      "env": {"RPC_URL": "https://..."}
    }
  }
}
```

### Utility functions

#### How to compute the gas fees
The SDK provides handy methods to compute the current "priority fee" and "max fee per gas":  

Sync code:
```python
from uniswap_universal_router_decoder.utils import compute_gas_fees
priority_fee, max_fee_per_gas = compute_gas_fees(w3)  # w3 is a valid Web3 instance
```

Async code:
```python
from uniswap_universal_router_decoder.utils import async_compute_gas_fees
priority_fee, max_fee_per_gas = await async_compute_gas_fees(async_w3)  # async_w3 is a valid AsyncWeb3 instance
```

#### Ticks, sqrtPriceX96 and liquidity
These functions can be useful to estimate the arguments needed to mint positions.

⚠️ The implementation of all tick, sqrtPriceX96, and liquidity related functions differs from the contracts: 
if you want the exact same results/numbers, do not use them.

They can be imported `from uniswap_universal_router_decoder.utils`.  
For examples, check the integration tests for Uniswap V4.

```python
compute_sqrt_price_x96()  # Compute the sqrtPriceX96 from the Wei amounts  
convert_sqrt_price_x96()  # Compute the price from the sqrtPriceX96  
sqrt_price_x96_to_floor_tick()  # Convert a sqrtPriceX96 to floor tick  
tick_to_sqrt_price_x96()  # Convert a tick to sqrtPriceX96  
tick_to_prices()  # Compute price_0 (with currency_0 as the quote currency) and price_1 (with currency_1 as the quote currency)
    at a given tick  
price_0_to_closest_tick()  # Compute the closest tick to a given price; useful to compute a price range lower and upper ticks  
compute_liquidity()  # Compute theoretical liquidity as used to mint positions.
```

## Tutorials and Recipes on the Uniswap Universal Router:
See the [SDK Wiki](https://github.com/Elnaril/uniswap-universal-router-decoder/wiki).

## News and Q&A:
See the [Discussions](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions) and [𝕏](https://twitter.com/ElnarilDev)
