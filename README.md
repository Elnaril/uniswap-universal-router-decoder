# Uniswap Universal Router Decoder

## Description

The object of this library is to decode the transaction input sent to the Uniswap universal router 
(address [`0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B`](https://etherscan.io/address/0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B) 
on Ethereum Mainnet).

⚠ Not all commands are decoded yet. Below a list of the commands that have already been implemented.

| Command Id | Function Name | Is Implemented
| ---------- | ------------- |:--------------:
| 0x00 | V3_SWAP_EXACT_IN | ✅
| 0x01 | V3_SWAP_EXACT_OUT | ✅
| 0x08 | V2_SWAP_EXACT_IN | ✅
| 0x09 | V2_SWAP_EXACT_OUT | ✅
| 0x0a | PERMIT2_PERMIT | ✅
| 0x0b | WRAP_ETH | ✅
| 0x0c | UNWRAP_WETH | ✅


## Installation

```bash
# update pip to latest version if needed
pip install -U pip

# install the decoder from pypi.org
pip install uniswap-universal-router-decoder
```

## Usage

The library exposes a class, `RouterDecoder` with 2 public methods `decode_function_input` and `decode_transaction`.
To decode a transaction input:

```python
from uniswap_universal_router_decoder.router_decoder import RouterDecoder

trx_input = "0x3593564c000000000000000000 ... 90095b5c4e9f5845bba"  # the trx input to decode
decoder = RouterDecoder()
decoded_trx_input = decoder.decode_transaction(trx_input)
```

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
rpc_link = "https://..."  # your rpc enpoint
decoder = RouterDecoder(rpc_endpoint=rpc_link)
```

And then the decoder will get the transaction from the blockchain and decode it, along with its input data:
```python
# Using a rpc endpoint
trx_hash = "0x52e63b7 ... 11b979dd9"
decoded_transaction = decoder.decode_transaction(trx_hash)
```
