# Uniswap Universal Router Decoder & Encoder
⚠ This version introduces breaking changes compared to v0.5, because it uses now web3 v6
This upgrade was necessary to implement a working PERMIT2_PERMIT encoding (because of a bug in EIP712 signatures, fixed in a web3 v6 dependency).
Also, it allows to use Python 3.11.

The v0.5 code is visible on its own [branch](https://github.com/Elnaril/uniswap-universal-router-decoder/tree/v0.5)

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

## Release Notes
### V0.7.0
 - Add support for encoding V2_SWAP_EXACT_OUT
 - Add support for encoding V3_SWAP_EXACT_OUT
 - Fix V3_SWAP_EXACT_OUT ABI
 - Fix typos in README
### V0.6.0
 - Breaking changes: use Web3.py v6 i/o v5
 - Add support for the PERMIT2_PERMIT function
 - Add support for chaining PERMIT2_PERMIT and V2_SWAP_EXACT_IN in the same transaction

## Overview and Points of Attention

The object of this library is to decode & encode the transaction input sent to the Uniswap universal router (UR)
(address [`0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B`](https://etherscan.io/address/0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B) 
on Ethereum Mainnet).

⚠ This library has not been audited, so use at your own risk !

⚠ There is no guarantee of compatibility between 2 versions: consider forcing the version in your dependency requirements.

⚠ This project is a work in progress so not all commands are decoded yet. Below the list of the already implemented ones.
Also, only one command can be encoded in a single transaction input data at the moment.


| Command Id | Function Name | Decode | Encode
| ---------- | ------------- |:------:|:------:
| 0x00 | V3_SWAP_EXACT_IN | ✅ | ✅
| 0x01 | V3_SWAP_EXACT_OUT | ✅ | ✅
| 0x02 - 0x06 |  | ❌ | ❌
| 0x07 | placeholder  | N/A | N/A
| 0x08 | V2_SWAP_EXACT_IN | ✅ | ✅
| 0x09 | V2_SWAP_EXACT_OUT | ✅ | ✅
| 0x0a | PERMIT2_PERMIT | ✅ | ✅
| 0x0b | WRAP_ETH | ✅ | ✅
| 0x0c | UNWRAP_WETH | ✅ | ❌
| 0x0d | PERMIT2_TRANSFER_FROM_BATCH | ❌ | ❌
| 0x0e - 0x0f | placeholders | N/A | N/A
| 0x10 - 0x1d |  | ❌ | ❌
| 0x1e - 0x3f | placeholders | N/A | N/A

## Installation
A good practice is to use [Python virtual environments](https://python.readthedocs.io/en/latest/library/venv.html), here is a [tutorial](https://realpython.com/python-virtual-environments-a-primer/).

The library can be pip installed from [pypi.org](https://pypi.org/project/uniswap-universal-router-decoder/) as usual:

```bash
# update pip to latest version if needed
pip install -U pip

# install the decoder from pypi.org
pip install uniswap-universal-router-decoder
```

## Usage

The library exposes a class, `RouterDecoder` with several public methods that can be used to decode or encode UR data.

### How to decode a transaction input
To decode a transaction input, use the `decode_function_input` method as follows:

```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

trx_input = "0x3593564c000000000000000000 ... 90095b5c4e9f5845bba"  # the trx input to decode
decoder = RouterDecoder()
decoded_trx_input = decoder.decode_function_input(trx_input)
```

Example of decoded input returned by `decode_function_input`:
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
                }
            ),
            (
                <Function V3_SWAP_EXACT_IN(address,uint256,uint256,bytes,bool)>,  # the function corresponding to the second command
                {                                                                 # and its parameters
                    'recipient': '0x0000000000000000000000000000000000000001',  # code indicating the sender will receive the output of this command
                    'amountIn': 4500000000000000000,  # the exact amount sent
                    'amountOutMin': 6291988002,  # the min amount expected of the bought token for the swap to be executed 
                    'path': b"\xc0*\xaa9\xb2#\xfe\x8d\n\x0e\\O'\xea\xd9\x08<ul\xc2"  # the V3 path (tokens + pool fees)
                           b'\x00\x01\xf4\xa0\xb8i\x91\xc6!\x8b6\xc1\xd1\x9dJ.'  # can be decoded with the method decode_v3_path()
                           b'\x9e\xb0\xce6\x06\xebH',
                    'payerIsSender': False  # a bool indicating if the input tokens come from the sender or are already in the UR
                }
            )
        ],
        'deadline': 1678441619  # The deadline after which the transaction is not valid any more.
    }
)
```

### How to decode a transaction
It's also possible to decode the whole transaction, given its hash 
and providing the decoder has been built with either a valid Web3 instance or the link to a rpc endpoint:

```python
# Using a web3 instance
from web3 import Web3
from uniswap_universal_router_decoder.router_decoder import RouterDecoder
w3 = Web3(...)  # your web3 instance
decoder = RouterDecoder(w3=w3)
```

```python
# Using a rpc endpoint
from web3 import Web3
from uniswap_universal_router_decoder.router_decoder import RouterDecoder
rpc_link = "https://..."  # your rpc endpoint
decoder = RouterDecoder(rpc_endpoint=rpc_link)
```

And then the decoder will get the transaction from the blockchain and decode it, along with its input data:
```python
trx_hash = "0x52e63b7 ... 11b979dd9"
decoded_transaction = decoder.decode_transaction(trx_hash)
```

### How to decode an Uniswap V3 swap path
The `RouterDecoder` class exposes also the static method `decode_v3_path` which can be used to decode a given Uniswap V3 path.

```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

uniswap_v3_path = b"\xc0*\xaa9\xb2#\xfe\x8d\n\x0e ... \xd7\x89"  # bytes or str hex
fn_name = "V3_SWAP_EXACT_IN"  # Or V3_SWAP_EXACT_OUT
decoded_path = RouterDecoder.decode_v3_path(fn_name, uniswap_v3_path)
```
The result is a tuple, starting with the "in-token" and ending with the "out-token", with the pool fees between each pair.


### How to encode a call to the function WRAP_ETH
This function can be used to convert eth to weth using the UR.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

decoder = RouterDecoder()
encoded_data = decoder.encode_data_for_wrap_eth(amount_in_wei)  # to convert amount_in_wei eth to weth

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```


### How to encode a call to the function V2_SWAP_EXACT_IN
This function can be used to swap tokens on a V2 pool. Correct allowances must have been set before using sending such transaction.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

decoder = RouterDecoder()
encoded_data = decoder.encode_data_for_v2_swap_exact_in(
        amount_in,  # in Wei
        min_amount_out,  # in Wei
        [
            in_token_address,
            out_token_address,
        ],
        timestamp,  # unix timestamp after which the trx will not be valid any more
    )

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### How to encode a call to the function V2_SWAP_EXACT_OUT
This function can be used to swap tokens on a V2 pool. Correct allowances must have been set before using sending such transaction.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder
decoder = RouterDecoder()
encoded_data = decoder.encode_data_for_v2_swap_exact_out(
        amount_out,  # in Wei
        max_amount_in,  # in Wei
        [
            in_token_address,
            out_token_address,
        ],
        timestamp,  # unix timestamp after which the trx will not be valid any more
    )
# then in your transaction dict:
transaction["data"] = encoded_data
# you can now sign and send the transaction to the UR
```

### How to encode a call to the function V3_SWAP_EXACT_IN
This function can be used to swap tokens on a V3 pool. Correct allowances must have been set before using sending such transaction.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

decoder = RouterDecoder()
encoded_data = decoder.encode_data_for_v3_swap_exact_in(
        amount_in,  # in Wei
        min_amount_out,  # in Wei
        [
            in_token_address,
            pool_fee,
            out_token_address,
        ],
        timestamp,  # unix timestamp after which the trx will not be valid any more
    )

# then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

### How to encode a call to the function V3_SWAP_EXACT_OUT
This function can be used to swap tokens on a V3 pool. Correct allowances must have been set before using sending such transaction.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder
decoder = RouterDecoder()
encoded_data = decoder.encode_data_for_v3_swap_exact_out(
        amount_out,  # in Wei
        max_amount_in,  # in Wei
        [
            in_token_address,
            pool_fee,
            out_token_address,
        ],
        timestamp,  # unix timestamp after which the trx will not be valid any more
    )
# then in your transaction dict:
transaction["data"] = encoded_data
# you can now sign and send the transaction to the UR
```

### How to encode a call to the function PERMIT2_PERMIT
This function is used to give an allowance to the universal router thanks to the Permit2 contract (([`0x000000000022D473030F116dDEE9F6B43aC78BA3`](https://etherscan.io/address/0x000000000022D473030F116dDEE9F6B43aC78BA3)).
It is also necessary to approve the Permit2 contract using the token approve function.
```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

decoder = RouterDecoder()
data, signable_message = decoder.create_permit2_signable_message(
    token_address,
    amount,  # max = 2**160 - 1
    expiration,
    nonce,  # Permit2 nonce
    spender,  # UR
    deadline,
    1,  # chain id
)

# Then you need to sign the message:
signed_message = acc.sign_message(signable_message)  # where acc is your LocalAccount

# And now you can encode the data:
encoded_data = decoder.encode_data_for_permit2_permit(data, signed_message)

# Then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```
After that, you can swap tokens using the Uniswap universal router.

### How to chain a call to PERMIT2_PERMIT and V2_SWAP_EXACT_IN in the same transaction
Don't forget to give a token allowance to the Permit2 contract as well.

```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

decoder = RouterDecoder()

# Permit signature
data, signable_message = decoder.create_permit2_signable_message(
    token_address,
    amount,  # max = 2**160 - 1
    expiration,
    nonce,  # Permit2 nonce
    spender,  # UR
    deadline,
    1,  # chain id
)

# Then you need to sign the message:
signed_message = acc.sign_message(signable_message)  # where acc is your LocalAccount

# Permit + v2 swap encoding
path = [token_in_address, token_out_address]
encoded_data = decoder.encode_data_for_v2_swap_exact_in_with_permit(
    permit_single=data,
    signed_permit_single=signed_message,
    amount_in=amount_in,
    amount_out_min=amount_out_min,
    path=path,
)

# Then in your transaction dict:
transaction["data"] = encoded_data

# you can now sign and send the transaction to the UR
```

---

[![](https://visitcount.itsvg.in/api?id=elnaril-uurd-repo&label=Project%20Views&color=8&icon=5&pretty=false)](https://visitcount.itsvg.in)
