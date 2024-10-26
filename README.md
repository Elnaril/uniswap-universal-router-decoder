# Uniswap Universal Router Decoder & Encoder

> Many thanks to **everyone** who has ☕️ [offered some **coffees**!](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions/11) ☕️
> or ⭐ [**starred** this project!](https://github.com/Elnaril/uniswap-universal-router-decoder/stargazers) ⭐  
> It is **greatly** appreciated! :)

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
[![Type Checker: mypy](https://img.shields.io/badge/%20type%20checker-mypy-%231674b1?style=flat&labelColor=ef8336)](https://mypy-lang.org/)
[![Linter: flake8](https://img.shields.io/badge/%20linter-flake8-%231674b1?style=flat&labelColor=ef8336)](https://flake8.pycqa.org/en/latest/)

---

## Release Notes
### v1.2.1
 - Add support for web3 v7
 - Add support for Python 3.12 & 3.13 
### v1.2.0
 - Add `compute_gas_fees()`: utility function to compute gas fees
 - Add `build_transaction()` method: It's now possible to build the full transaction i/o just the input data.
 - Add `fetch_permit2_allowance()`: Easy way to check the current Permit2 allowed amount, expiration and nonce. 
 - Make verifying contract (Permit2) configurable (Thanks to @speedssr and @freereaper)
 - Replace deprecated `eth_account.encode_structured_data()` with `eth_account.messages.encode_typed_data()`
### v1.1.0
 - Add support for the TRANSFER function
 - Add support for decoding the "revert on fail" flag and prepare for encoding on UR functions that support it.
 - Add support for encoding the `execute()` function without deadline

---

## Overview and Points of Attention

The object of this library is to decode & encode the transaction input sent to the Uniswap universal router (UR)
(address [`0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD`](https://etherscan.io/address/0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD) 
on Ethereum Mainnet). It is based on, and is intended to be used with [web3.py](https://github.com/ethereum/web3.py)  
The target audience is Python developers who are familiar with the Ethereum blockchain concepts and web3.py, and how DEXes work. 

⚠ This library has not been audited, so use at your own risk !

⚠ Before using this library, ensure you are familiar with general blockchain concepts and [web3.py](https://github.com/ethereum/web3.py) in particular.

⚠ This project is a work in progress so not all commands are decoded yet. Below the list of the already implemented ones.

| Command Id | Function Name | Decode | Encode
| ---------- | ------------- |:------:|:------:
| 0x00 | V3_SWAP_EXACT_IN | ✅ | ✅
| 0x01 | V3_SWAP_EXACT_OUT | ✅ | ✅
| 0x02 - 0x03 |  | ❌ | ❌
| 0x04 | SWEEP | ✅ | ✅
| 0x05 | TRANSFER | ✅ | ✅
| 0x06 | PAY_PORTION | ✅ | ✅
| 0x07 | placeholder  | N/A | N/A
| 0x08 | V2_SWAP_EXACT_IN | ✅ | ✅
| 0x09 | V2_SWAP_EXACT_OUT | ✅ | ✅
| 0x0a | PERMIT2_PERMIT | ✅ | ✅
| 0x0b | WRAP_ETH | ✅ | ✅
| 0x0c | UNWRAP_WETH | ✅ | ✅
| 0x0d | PERMIT2_TRANSFER_FROM_BATCH | ❌ | ❌
| 0x0e - 0x0f | placeholders | N/A | N/A
| 0x10 - 0x1d |  | ❌ | ❌
| 0x1e - 0x3f | placeholders | N/A | N/A

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

---

## Usage

The library exposes a class, `RouterCodec` with several public methods that can be used to decode or encode UR data.

### How to decode a transaction input
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
        'deadline': 1678441619  # The deadline after which the transaction is not valid any more.
    }
)
```

### How to decode a transaction
It's also possible to decode the whole transaction, given its hash 
and providing the codec has been built with either a valid `Web3` instance or the link to a rpc endpoint:

```python
# Using a web3 instance
from web3 import Web3
from uniswap_universal_router_decoder import RouterCodec
w3 = Web3(...)  # your web3 instance
codec = RouterCodec(w3=w3)
```

```python
# Using a rpc endpoint
from web3 import Web3
from uniswap_universal_router_decoder import RouterCodec
rpc_link = "https://..."  # your rpc endpoint
codec = RouterCodec(rpc_endpoint=rpc_link)
```

And then the decoder will get the transaction from the blockchain and decode it, along with its input data:
```python
trx_hash = "0x52e63b7 ... 11b979dd9"
decoded_transaction = codec.decode.transaction(trx_hash)
```

### How to decode an Uniswap V3 swap path
The `RouterCodec` class exposes also the method `decode.v3_path()` which can be used to decode a given Uniswap V3 path.

```python
from uniswap_universal_router_decoder import RouterCodec

uniswap_v3_path = b"\xc0*\xaa9\xb2#\xfe\x8d\n\x0e ... \xd7\x89"  # bytes or str hex
fn_name = "V3_SWAP_EXACT_IN"  # Or V3_SWAP_EXACT_OUT
codec = RouterCodec()
decoded_path = codec.decode.v3_path(fn_name, uniswap_v3_path)
```
The result is a tuple, starting with the "in-token" and ending with the "out-token", with the pool fees between each pair.


### How to encode
The Universal Router allows the chaining of several functions in the same transaction.
This codec supports it (at least for supported functions) and exposes public methods that can be chained.

The chaining starts with the `encode.chain()` method and ends with the `build()` one which returns the full encoded data to be included in the transaction.
Below some examples of encoded data for one function and one example for 2 functions.

Default values for deadlines and expirations can be computed with the static methods `get_default_deadline()` and `get_default_expiration()` respectively.
```python
from uniswap_universal_router_decoder import RouterCodec

default_deadline = RouterCodec.get_default_deadline()
default_expiration = RouterCodec.get_default_expiration()

```
These 2 functions accept a custom duration in seconds as argument.


### How to encode a call to the function WRAP_ETH
This function can be used to convert eth to weth using the UR.
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
encoded_data = codec.encode.chain().wrap_eth(FunctionRecipient.SENDER, amount_in_wei).build(1676825611)  # to convert amount_in_wei eth to weth, and send them to the transaction sender.

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### How to encode a call to the function V2_SWAP_EXACT_IN
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

### How to encode a call to the function V2_SWAP_EXACT_OUT
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

### How to encode a call to the function V3_SWAP_EXACT_IN
This function can be used to swap tokens on a V3 pool. Correct allowances must have been set before using sending such transaction.
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

### How to encode a call to the function V3_SWAP_EXACT_OUT
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

### How to encode a call to the function PERMIT2_PERMIT
This function is used to give an allowance to the universal router thanks to the Permit2 contract ([`0x000000000022D473030F116dDEE9F6B43aC78BA3`](https://etherscan.io/address/0x000000000022D473030F116dDEE9F6B43aC78BA3)).
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

### Other chainable functions
(See integration tests for full examples) 

#### PAY_PORTION
Example where a recipient is paid 1% of the USDC amount:
```python
.pay_portion(FunctionRecipient.CUSTOM, usdc_address, 100, recipient_address)

```
#### SWEEP
Example where the sender gets back all remaining USDC:
```python
.sweep(FunctionRecipient.SENDER, usdc_address, 0)
```

#### TRANSFER
Example where an USDC amount is sent to a recipient:
```python
.transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount, recipient_address)
```

### How to build directly a transaction
The SDK provides a handy method to build very easily the full transaction in addition to the input data.
It can compute most of the transaction parameters (if the codec has been instantiated with a valid w3 or rpc url) 
or you can provide them. 

Example where a swap is encoded and a transaction is built automatically:
```python
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec

codec = RouterCodec()
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
 - `value`: the quantity of ETH in wei you send to the Universal Router (for ex when you wrap them before a swap)
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

### Utility functions

#### How to compute the gas fees
The SDK provides a handy method to compute the current "priority fee" and "max fee per gas":
```python
from uniswap_universal_router_decoder.utils import compute_gas_fees
priority_fee, max_fee_per_gas = compute_gas_fees(w3)  # w3 is a valid Web3 instance
```

## Tutorials and Recipes:
See the [SDK Wiki](https://github.com/Elnaril/uniswap-universal-router-decoder/wiki).

## News and Q&A:
See the [Discussions](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions) and [𝕏](https://twitter.com/ElnarilDev)
