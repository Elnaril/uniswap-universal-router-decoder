import os
import subprocess
import time

from eth_account.account import LocalAccount
from web3 import (
    Account,
    Web3,
)

from uniswap_universal_router_decoder import RouterCodec


web3_provider = os.environ['WEB3_HTTP_PROVIDER_URL_ETHEREUM_MAINNET']
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

account: LocalAccount = Account.from_key("0xf7e96bcf6b5223c240ec308d8374ff01a753b00743b3a0127791f37f00c56514")
assert account.address == "0x1e46c294f20bC7C27D93a9b5f45039751D8BCc3e"

chain_id = 1
initial_block_number = 26174325
initial_eth_amount = 10000 * 10**18  # Anvil provides 10000 ETH by default

# Universal Router v2.1.2 address
ur_address = Web3.to_checksum_address("0x23617e59A5925b2A4Bf75d73ff6711cD0b29De85")

# V3 position manager (NonfungiblePositionManager)
v3_position_manager_address = Web3.to_checksum_address("0xC36442b4a4522E871399CD717aBDD847Ab11FE88")
v3_position_manager_abi = '[{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"positions","outputs":[{"internalType":"uint96","name":"nonce","type":"uint96"},{"internalType":"address","name":"operator","type":"address"},{"internalType":"address","name":"token0","type":"address"},{"internalType":"address","name":"token1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"feeGrowthInside0LastX128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthInside1LastX128","type":"uint256"},{"internalType":"uint128","name":"tokensOwed0","type":"uint128"},{"internalType":"uint128","name":"tokensOwed1","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"index","type":"uint256"}],"name":"tokenByIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501
v3_position_manager_contract = w3.eth.contract(address=v3_position_manager_address, abi=v3_position_manager_abi)

# The address that will be approved for the V3 position
spender = Web3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD")

codec = RouterCodec()


def launch_anvil():
    anvil_process = subprocess.Popen(
        " ".join([
            "anvil",
            f"--fork-url {web3_provider}",
            f"--fork-block-number {initial_block_number}",
            "--mnemonic-seed-unsafe 8721345628937456298",
        ]),
        shell=True,
    )
    time.sleep(5)
    parent_id = anvil_process.pid
    return parent_id


def kill_processes(parent_id):
    processes = [str(parent_id), ]
    pgrep_process = subprocess.run(
        f"pgrep -P {parent_id}", shell=True, text=True, capture_output=True
    ).stdout.strip("\n")
    children_ids = pgrep_process.split("\n") if len(pgrep_process) > 0 else []
    processes.extend(children_ids)
    subprocess.run(f"kill {' '.join(processes)}", shell=True, text=True, capture_output=True)


def check_initialization():
    assert w3.eth.chain_id == chain_id
    assert w3.eth.block_number == initial_block_number
    assert w3.eth.get_balance(account.address) == initial_eth_amount
    print(" => Initialization: OK")


def send_transaction(value, encoded_data):
    trx_params = {
        "from": account.address,
        "to": ur_address,
        "gas": 1_000_000,
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": w3.eth.gas_price + w3.eth.max_priority_fee,
        "type": '0x2',
        "chainId": chain_id,
        "value": value,
        "nonce": w3.eth.get_transaction_count(account.address),
        "data": encoded_data,
    }
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    return trx_hash


def acquire_a_v3_position():
    """
    The test account needs to own a V3 position (NFT) to be able to sign a permit for it.
    Anvil provides no position, so we impersonate the owner of an existing position and transfer it
    to the test account.
    """
    total_supply = v3_position_manager_contract.functions.totalSupply().call()
    token_id = None
    owner = None
    # scan the most recently minted positions until we find one owned by an EOA
    for index in range(total_supply - 1, total_supply - 100, -1):
        candidate_token_id = v3_position_manager_contract.functions.tokenByIndex(index).call()
        candidate_owner = v3_position_manager_contract.functions.ownerOf(candidate_token_id).call()
        if w3.eth.get_code(candidate_owner) == b"":
            token_id = candidate_token_id
            owner = candidate_owner
            break
    assert token_id is not None, "Could not find an EOA-owned V3 position"
    assert owner != account.address, "The test account already owns this V3 position"

    # impersonate the owner to transfer the position to the test account
    w3.provider.make_request("anvil_impersonateAccount", [owner])
    w3.provider.make_request("anvil_setBalance", [owner, hex(10 ** 18)])
    trx_params = v3_position_manager_contract.functions.transferFrom(owner, account.address, token_id).build_transaction({  # noqa: E501
        "from": owner,
        "gas": 300_000,
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": w3.eth.gas_price + w3.eth.max_priority_fee,
        "type": '0x2',
        "chainId": chain_id,
        "value": 0,
        "nonce": w3.eth.get_transaction_count(owner),
    })
    trx_hash = w3.eth.send_transaction(trx_params)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'
    w3.provider.make_request("anvil_stopImpersonatingAccount", [owner])

    assert v3_position_manager_contract.functions.ownerOf(token_id).call() == account.address
    print(f" => Acquired V3 position #{token_id} (transferred from {owner})")
    return token_id


def v3_position_manager_permit(token_id):
    """
    Approve a spender for a V3 position owned by the test account, using the UR V3_POSITION_MANAGER_PERMIT command.
    """
    nonce = v3_position_manager_contract.functions.positions(token_id).call()[0]
    deadline = codec.get_default_deadline()

    assert v3_position_manager_contract.functions.getApproved(token_id).call() != spender

    permit_params, signable_message = codec.create_v3_position_manager_permit_signable_message(
        spender,
        token_id,
        nonce,
        deadline,
    )
    signed_message = account.sign_message(signable_message)

    encoded_input = (
        codec
        .encode
        .chain()
        .v3_position_manager_permit(permit_params, signed_message)
        .build(deadline)
    )

    trx_hash = send_transaction(0, encoded_input)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'

    # the spender is now approved for the position
    assert v3_position_manager_contract.functions.getApproved(token_id).call() == spender
    # the permit consumed the nonce
    assert v3_position_manager_contract.functions.positions(token_id).call()[0] == nonce + 1

    print(" => V3_POSITION_MANAGER_PERMIT: OK")


def v3_position_manager_permit_reverts_on_stale_nonce(token_id):
    """
    A permit signed with a stale nonce must revert, since the position manager recomputes the digest
    with the current nonce.
    """
    stale_nonce = v3_position_manager_contract.functions.positions(token_id).call()[0] - 1
    deadline = codec.get_default_deadline()

    permit_params, signable_message = codec.create_v3_position_manager_permit_signable_message(
        spender,
        token_id,
        stale_nonce,
        deadline,
    )
    signed_message = account.sign_message(signable_message)

    encoded_input = (
        codec
        .encode
        .chain()
        .v3_position_manager_permit(permit_params, signed_message)
        .build(deadline)
    )

    trx_hash = send_transaction(0, encoded_input)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 0, f'receipt["status"] is actually {receipt["status"]}'

    print(" => V3_POSITION_MANAGER_PERMIT reverts on stale nonce: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    token_id = acquire_a_v3_position()
    v3_position_manager_permit(token_id)
    v3_position_manager_permit_reverts_on_stale_nonce(token_id)


def print_success_message():
    print("------------------------------------------")
    print("| Integration tests are successful !! :) |")
    print("------------------------------------------")


def main():
    anvil_pid = launch_anvil()
    try:
        launch_integration_tests()
        print_success_message()
    finally:
        kill_processes(anvil_pid)


if __name__ == "__main__":
    main()
