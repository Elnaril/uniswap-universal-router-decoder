import hashlib
import os
import subprocess
import time

from eth_account.account import LocalAccount
from web3 import (
    Account,
    Web3,
)
from web3.types import Wei

from uniswap_universal_router_decoder import (
    AllowanceTransferDetails,
    FunctionRecipient,
    PermitDetails,
    RouterCodec,
)


web3_provider = os.environ['WEB3_HTTP_PROVIDER_URL_ETHEREUM_MAINNET']
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

account: LocalAccount = Account.from_key("0xf7e96bcf6b5223c240ec308d8374ff01a753b00743b3a0127791f37f00c56514")
assert account.address == "0x1e46c294f20bC7C27D93a9b5f45039751D8BCc3e"

chain_id = 1
initial_block_number = 24485322

# recipients
recipients = tuple(
    Account.from_key("0x" + hashlib.sha256(f"uniswap_test_recipient_{i}_anvil_fork".encode()).hexdigest())
    for i in range(5)
)

# Tokens
eth_address = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

weth_address = Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
weth_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'  # noqa
weth_contract = w3.eth.contract(address=weth_address, abi=weth_abi)

wbtc_address = Web3.to_checksum_address("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599")
wbtc_abi = '[{"constant":true,"inputs":[],"name":"mintingFinished","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_token","type":"address"}],"name":"reclaimToken","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"unpause","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"value","type":"uint256"}],"name":"burn","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"claimOwnership","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"paused","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_subtractedValue","type":"uint256"}],"name":"decreaseApproval","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"renounceOwnership","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"finishMinting","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"pause","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_addedValue","type":"uint256"}],"name":"increaseApproval","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"pendingOwner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"anonymous":false,"inputs":[],"name":"Pause","type":"event"},{"anonymous":false,"inputs":[],"name":"Unpause","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"burner","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"amount","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[],"name":"MintFinished","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"previousOwner","type":"address"}],"name":"OwnershipRenounced","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"previousOwner","type":"address"},{"indexed":true,"name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]'  # noqa
wbtc_contract = w3.eth.contract(address=wbtc_address, abi=wbtc_abi)

# Instantiate SDK
codec = RouterCodec()

# Pools
eth_wbtc_pool_key = codec.encode.v4_pool_key(eth_address, wbtc_address, 3000, 60)

# Uniswap contracts
ur_address = Web3.to_checksum_address("0x66a9893cC07D91D95644AEDD05D03f95e1dBA8Af")
permit2_address = Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")


# Tests
def launch_anvil():
    anvil_process = subprocess.Popen(
        " ".join(
            [
                "anvil -vvvvv",
                f"--fork-url {web3_provider}",
                f"--fork-block-number {initial_block_number}",
                "--mnemonic-seed-unsafe 8721345628937456298",
            ]
        ),
        shell=True,
    )
    time.sleep(2)
    parent_id = anvil_process.pid
    return parent_id


def kill_processes(parent_id):
    processes = [str(parent_id), ]
    pgrep_process = subprocess.run(
        f"pgrep -P {parent_id}", shell=True, text=True, capture_output=True
    ).stdout.strip("\n")
    children_ids = pgrep_process.split("\n") if len(pgrep_process) > 0 else []
    processes.extend(children_ids)
    print(f"Killing processes: {' '.join(processes)}")
    subprocess.run(f"kill {' '.join(processes)}", shell=True, text=True, capture_output=True)


def check_initialization():
    assert w3.eth.chain_id == chain_id
    assert w3.eth.block_number == initial_block_number
    assert w3.eth.get_balance(account.address) == 10000 * 10**18

    assert weth_contract.functions.balanceOf(account.address).call() == 0
    assert wbtc_contract.functions.balanceOf(account.address).call() == 0
    for recipient in recipients:
        assert 0 == weth_contract.functions.balanceOf(recipient.address).call()
        assert 0 == wbtc_contract.functions.balanceOf(recipient.address).call()

    weth_permit2_allowance = codec.fetch_permit2_allowance(account.address, weth_address, ur_address)
    print("weth_permit2_allowance:", weth_permit2_allowance)
    assert weth_permit2_allowance == (0, 0, 0)

    wbtc_permit2_allowance = codec.fetch_permit2_allowance(account.address, wbtc_address, ur_address)
    print("wbtc_permit2_allowance:", wbtc_permit2_allowance)
    assert wbtc_permit2_allowance == (0, 0, 0)

    print(" => Initialization: OK")


def permit2_batch_weth_btc():
    print("START PERMIT2 UNIVERSAL ROUTER for WETH and BTC")
    expiration = codec.get_default_expiration()
    permit2_details: list[PermitDetails] = [
        {
            "token": weth_address,
            "amount": Wei(2**160 - 1),
            "expiration": expiration,
            "nonce": 0,
        },
        {
            "token": wbtc_address,
            "amount": Wei(10 * 10**8),
            "expiration": expiration,
            "nonce": 0,
        },
    ]
    data, signable_message = codec.create_permit2_batch_signable_message(
        permit2_details,
        ur_address,
        codec.get_default_deadline(),
        chain_id,
    )
    signed_message = account.sign_message(signable_message)
    trx_params = (
        codec.
        encode.
        chain().
        permit2_permit_batch(data, signed_message).
        build_transaction(account.address, block_identifier=w3.eth.block_number)
    )

    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # status == 1 => trx success

    weth_permit2_allowance = codec.fetch_permit2_allowance(account.address, weth_address, ur_address)
    print("weth_permit2_allowance:", weth_permit2_allowance)
    assert weth_permit2_allowance == (Wei(2**160 - 1), expiration, 1)

    wbtc_permit2_allowance = codec.fetch_permit2_allowance(account.address, wbtc_address, ur_address)
    print("wbtc_permit2_allowance:", wbtc_permit2_allowance)
    assert wbtc_permit2_allowance == (Wei(10 * 10**8), expiration, 1)

    print("PERMIT2 UNIVERSAL ROUTER for WETH and BTC => OK\n")


def get_weth_and_btc():
    print("START GET WETH AND BTC")
    eth_for_weth_amount = Wei(1000 * 10**18)
    eth_for_btc_amount = Wei(1000 * 10**18)
    value = eth_for_weth_amount + eth_for_btc_amount

    trx_params = (
        codec.
        encode.
        chain().
        wrap_eth(FunctionRecipient.SENDER, eth_for_weth_amount).
        v4_swap().
        swap_exact_in_single(
            pool_key=eth_wbtc_pool_key,
            zero_for_one=True,
            amount_in=eth_for_btc_amount,
            amount_out_min=Wei(0),
        ).
        take_all(wbtc_address, Wei(0)).
        settle_all(eth_address, eth_for_btc_amount).
        build_v4_swap().
        build_transaction(account.address, value, block_identifier=w3.eth.block_number)
    )
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # status == 1 => trx success

    eth_balance = w3.eth.get_balance(account.address)
    print("ETH balance:", eth_balance / 10 ** 18)
    assert 7999 * 10**18 < eth_balance < 8000 * 10**18

    weth_balance = weth_contract.functions.balanceOf(account.address).call()
    print("WETH balance:", weth_balance / 10 ** 18)
    assert weth_balance == eth_for_weth_amount, f"actual wbtc balance is {weth_balance}"

    wbtc_balance = wbtc_contract.functions.balanceOf(account.address).call()
    print("WBTC balance:", wbtc_balance / 10 ** 8)
    assert wbtc_balance == 2692025946, f"actual wbtc balance is {wbtc_balance}"

    print("GET WETH AND BTC => OK")


def approve_permit2_for_token(token_contract):
    print(f"START APPROVE PERMIT2 FOR token: {token_contract.address}")
    contract_function = token_contract.functions.approve(permit2_address, 2 ** 256 - 1)
    trx_params = contract_function.build_transaction(
        {
            "from": account.address,
            "gas": 800_000,
            "maxPriorityFeePerGas": w3.eth.max_priority_fee,
            "maxFeePerGas": Wei(10 * 10 ** 9),
            "type": '0x2',
            "chainId": chain_id,
            "value": 0,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )

    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # status == 1 => trx success

    allowance = token_contract.functions.allowance(account.address, permit2_address).call()
    print(allowance)
    assert allowance == 2 ** 256 - 1

    print(f"APPROVE PERMIT2 FOR token: {token_contract.address} => OK\n")


def permit2_transfer_from_batch():
    print("START PERMIT2_TRANSFER_FROM_BATCH")
    # Will send 1 WETH and 1 WBTC to all recipients
    weth_amount = Wei(1 * 10**18)
    wbtc_amount = Wei(1 * 10**8)
    batch_details: list[AllowanceTransferDetails] = [
        {
            'from': account.address,
            'to': recipient.address,
            'amount': weth_amount,
            'token': weth_address,
        }
        for recipient in recipients
    ]
    batch_details.extend(
        [
            {
                'from': account.address,
                'to': recipient.address,
                'amount': wbtc_amount,
                'token': wbtc_address,
            }
            for recipient in recipients
        ]
    )

    trx_params = (
        codec.
        encode.
        chain().
        permit2_transfer_from_batch(batch_details).
        build_transaction(account.address, block_identifier=w3.eth.block_number)
    )

    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # status == 1 => trx success

    for recipient in recipients:
        assert weth_amount == weth_contract.functions.balanceOf(recipient.address).call()
        assert wbtc_amount == wbtc_contract.functions.balanceOf(recipient.address).call()

    print("PERMIT2_TRANSFER_FROM_BATCH => OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()

    permit2_batch_weth_btc()
    get_weth_and_btc()

    approve_permit2_for_token(weth_contract)
    approve_permit2_for_token(wbtc_contract)

    permit2_transfer_from_batch()


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
