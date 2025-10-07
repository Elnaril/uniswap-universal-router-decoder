# PERMIT2_PERMIT_BATCH Integration Test

This integration test validates the complete PERMIT2_PERMIT_BATCH workflow using Foundry Anvil.

## Prerequisites

1. **Install Foundry** (if not already installed):
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```

2. **Verify Anvil is installed**:
   ```bash
   anvil --version
   ```

## Running the Test

### Step 1: Start Anvil with Mainnet Fork

In a separate terminal window, start Anvil with a mainnet fork:

```bash
anvil --fork-url https://eth.llamarpc.com --fork-block-number 21000000
```

This will:
- Fork Ethereum mainnet at block 21000000
- Start a local Ethereum node at `http://127.0.0.1:8545`
- Provide 10 test accounts with 10,000 ETH each
- Use the first account (0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266) for testing

### Step 2: Run the Integration Test

In your main terminal, run the test:

```bash
cd integration_tests
python3 test_permit2_batch.py
```

Or using pytest:

```bash
python3 -m pytest integration_tests/test_permit2_batch.py -v -s
```

## What the Test Does

The test performs a complete end-to-end validation:

1. **Creates a batch permit** for 3 tokens (DAI, USDC, USDT)
2. **Generates EIP-712 signable message** using the RouterCodec
3. **Signs the message** with the test account's private key
4. **Encodes the PERMIT2_PERMIT_BATCH command** with the signature
5. **Submits the transaction** to the Universal Router on Anvil
6. **Waits for confirmation** and verifies transaction success
7. **Decodes the transaction** to verify the command was properly encoded/decoded

## Expected Output

```
Test account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Account balance: 10000.0 ETH

1. Creating EIP-712 signable message...
Domain: {...}
Message types: ['PermitDetails', 'PermitBatch']
Primary type: PermitBatch

2. Signing EIP-712 message...
Signature: 0x...
Signature length: 132 chars (65 bytes)

3. Encoding PERMIT2_PERMIT_BATCH command...
Encoded input length: ... chars
Encoded input (first 100 chars): 0x3593564c...

4. Preparing transaction...
Transaction: {...}

5. Signing and sending transaction...
Transaction hash: 0x...

6. Waiting for transaction receipt...
Transaction receipt:
  Status: 1
  Block number: ...
  Gas used: ...
  Logs: ... events emitted

7. Decoding transaction to verify...
Decoded transaction:
  Function: execute
  Number of commands: 1

✓ Integration test passed!
✓ Successfully executed PERMIT2_PERMIT_BATCH for 3 tokens
✓ Transaction: 0x...
```

## Configuration

The test uses the following configuration:

- **Chain**: Ethereum Mainnet (forked)
- **RPC URL**: `http://127.0.0.1:8545` (Anvil default)
- **Universal Router**: `0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD`
- **Permit2 Contract**: `0x000000000022D473030F116dDEE9F6B43aC78BA3`
- **Test Account**: First Anvil account
- **Tokens**: DAI, USDC, USDT

You can customize the RPC URL by setting the `ANVIL_RPC` environment variable:

```bash
export ANVIL_RPC="http://localhost:8545"
python3 test_permit2_batch.py
```

## Troubleshooting

### "Cannot connect to Anvil"
- Make sure Anvil is running in a separate terminal
- Verify the RPC URL matches (default: `http://127.0.0.1:8545`)

### "Transaction failed"
- Check that the fork block number is recent enough
- Ensure the Universal Router and Permit2 contracts are deployed at the expected addresses

### "Test account has no ETH"
- This shouldn't happen with default Anvil accounts
- If using a custom account, fund it with ETH in Anvil

## Notes

- This test does NOT require real ETH or tokens
- All execution happens on a local Anvil fork
- The test validates both encoding AND decoding of PERMIT2_PERMIT_BATCH
- EIP-712 signature validation is tested implicitly through transaction success
