"""
Integration test for PERMIT2_PERMIT_BATCH using Foundry Anvil.

This test validates the full workflow:
1. Encode PERMIT2_PERMIT_BATCH command
2. Create EIP-712 signable message
3. Sign the message with a test account
4. Execute the transaction on a forked mainnet (via Anvil)
5. Verify the permit batch was processed correctly
"""

import os
from decimal import Decimal

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from uniswap_universal_router_decoder import RouterCodec


# Test configuration
ANVIL_RPC = os.getenv("ANVIL_RPC", "http://127.0.0.1:8545")
CHAIN_ID = 1  # Mainnet

# Contract addresses (mainnet)
UNIVERSAL_ROUTER = "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"
PERMIT2_CONTRACT = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

# Test account (from Anvil's default accounts)
# Private key for first Anvil account: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def test_permit2_batch_integration():
    """
    Integration test for PERMIT2_PERMIT_BATCH command.
    
    Prerequisites:
    1. Foundry Anvil must be running with mainnet fork:
       anvil --fork-url https://eth.llamarpc.com --fork-block-number 21000000
    
    This test:
    - Creates a batch permit for 3 tokens (DAI, USDC, USDT)
    - Signs the EIP-712 message
    - Encodes the PERMIT2_PERMIT_BATCH command
    - Executes the transaction on Anvil
    - Verifies the permit batch was successful
    """
    # Setup Web3 connection
    w3 = Web3(Web3.HTTPProvider(ANVIL_RPC))
    assert w3.is_connected(), "Cannot connect to Anvil. Make sure it's running."
    
    # Setup test account
    test_account = Account.from_key(TEST_PRIVATE_KEY)
    print(f"Test account: {test_account.address}")
    
    # Verify account has funds
    balance = w3.eth.get_balance(test_account.address)
    assert balance > 0, f"Test account {test_account.address} has no ETH"
    print(f"Account balance: {Web3.from_wei(balance, 'ether')} ETH")
    
    # Initialize codec
    codec = RouterCodec()
    
    # Define permit batch parameters
    current_block = w3.eth.block_number
    current_timestamp = w3.eth.get_block(current_block)['timestamp']
    
    # Expiration 1 hour from now
    expiration = current_timestamp + 3600
    # Signature deadline 2 hours from now
    sig_deadline = current_timestamp + 7200
    
    permit_batch = {
        "details": [
            {
                "token": DAI_ADDRESS,
                "amount": 1000000000000000000000,  # 1000 DAI (18 decimals)
                "expiration": expiration,
                "nonce": 0
            },
            {
                "token": USDC_ADDRESS,
                "amount": 1000000000,  # 1000 USDC (6 decimals)
                "expiration": expiration,
                "nonce": 0
            },
            {
                "token": USDT_ADDRESS,
                "amount": 1000000000,  # 1000 USDT (6 decimals)
                "expiration": expiration,
                "nonce": 0
            }
        ],
        "spender": UNIVERSAL_ROUTER,
        "sigDeadline": sig_deadline
    }
    
    # Create EIP-712 signable message
    print("\n1. Creating EIP-712 signable message...")
    signable_message = codec.create_permit2_batch_signable_message(
        permit_batch=permit_batch,
        permit2_address=PERMIT2_CONTRACT,
        chain_id=CHAIN_ID
    )
    
    print(f"Domain: {signable_message['domain']}")
    print(f"Message types: {list(signable_message['types'].keys())}")
    print(f"Primary type: {signable_message['primaryType']}")
    
    # Encode the typed data
    encoded_message = encode_typed_data(full_message=signable_message)
    
    # Sign the message
    print("\n2. Signing EIP-712 message...")
    signed_message = test_account.sign_message(encoded_message)
    signature = signed_message.signature.hex()
    print(f"Signature: {signature}")
    print(f"Signature length: {len(signature)} chars ({len(signed_message.signature)} bytes)")
    
    # Encode the PERMIT2_PERMIT_BATCH command
    print("\n3. Encoding PERMIT2_PERMIT_BATCH command...")
    encoded_input = codec.encode.chain().permit2_permit_batch(
        permit_batch, 
        signed_message.signature
    ).build(
        encoded_message.address,  # recipient (the signer)
        value=Decimal(0),
        deadline=sig_deadline
    )
    
    print(f"Encoded input length: {len(encoded_input)} chars")
    print(f"Encoded input (first 100 chars): {encoded_input[:100]}...")
    
    # Prepare transaction
    print("\n4. Preparing transaction...")
    nonce = w3.eth.get_transaction_count(test_account.address)
    
    tx = {
        'from': test_account.address,
        'to': UNIVERSAL_ROUTER,
        'value': 0,
        'gas': 500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
        'chainId': CHAIN_ID,
        'data': encoded_input
    }
    
    print(f"Transaction: {tx}")
    
    # Sign and send transaction
    print("\n5. Signing and sending transaction...")
    signed_tx = test_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction hash: {tx_hash.hex()}")
    
    # Wait for transaction receipt
    print("\n6. Waiting for transaction receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    print("Transaction receipt:")
    print(f"  Status: {receipt['status']}")
    print(f"  Block number: {receipt['blockNumber']}")
    print(f"  Gas used: {receipt['gasUsed']}")
    print(f"  Logs: {len(receipt['logs'])} events emitted")
    
    # Verify transaction succeeded
    assert receipt['status'] == 1, "Transaction failed"
    
    # Decode the transaction to verify
    print("\n7. Decoding transaction to verify...")
    codec_w3 = RouterCodec(w3=w3)
    decoded_tx = codec_w3.decode.transaction(tx_hash.hex())
    
    print("Decoded transaction:")
    print(f"  Function: {decoded_tx['function']}")
    print(f"  Number of commands: {len(decoded_tx['decoded_input']['inputs'])}")

    
    # Verify decoded commands
    command_inputs = decoded_tx['decoded_input']['inputs']
    assert len(command_inputs) == 1, "Expected 1 command"
    
    # Verify it's PERMIT2_PERMIT_BATCH
    command = command_inputs[0]
    assert command[0].fn_name == "PERMIT2_PERMIT_BATCH", f"Expected PERMIT2_PERMIT_BATCH, got {command[0].fn_name}"
    
    # Verify parameters
    params = command[1]
    assert "struct" in params
    assert "data" in params
    
    struct_data = params["struct"]
    assert "details" in struct_data
    assert "spender" in struct_data
    assert "sigDeadline" in struct_data
    
    # Verify batch details
    details = struct_data["details"]
    assert len(details) == 3, f"Expected 3 permits in batch, got {len(details)}"
    
    # Verify token addresses
    assert details[0]["token"].lower() == DAI_ADDRESS.lower()
    assert details[1]["token"].lower() == USDC_ADDRESS.lower()
    assert details[2]["token"].lower() == USDT_ADDRESS.lower()
    
    # Verify spender
    assert struct_data["spender"].lower() == UNIVERSAL_ROUTER.lower()
    
    print("\n✓ Integration test passed!")
    print("✓ Successfully executed PERMIT2_PERMIT_BATCH for 3 tokens")
    print(f"✓ Transaction: {tx_hash.hex()}")


if __name__ == "__main__":
    test_permit2_batch_integration()
