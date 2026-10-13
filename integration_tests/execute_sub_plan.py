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
    FunctionRecipient,
    RouterCodec,
)


web3_provider = os.environ['WEB3_HTTP_PROVIDER_URL_ETHEREUM_MAINNET']
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

account: LocalAccount = Account.from_key("0xf7e96bcf6b5223c240ec308d8374ff01a753b00743b3a0127791f37f00c56514")
assert account.address == "0x1e46c294f20bC7C27D93a9b5f45039751D8BCc3e"

# Deterministic recipient, derived the same way as in test_transfers.py
recipient: LocalAccount = Account.from_key(
    "0x" + hashlib.sha256(b"uniswap_test_recipient_1_anvil_fork").hexdigest()
)

chain_id = 1
initial_block_number = 26174325
initial_eth_amount = 10000 * 10**18  # Anvil provides 10000 ETH by default

erc20_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'  # noqa

weth_address = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdc_address = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)

# Universal Router v2.1.2 address
ur_address = Web3.to_checksum_address("0x23617e59A5925b2A4Bf75d73ff6711cD0b29De85")

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
    assert w3.eth.get_balance(recipient.address) == 0
    assert usdc_contract.functions.balanceOf(account.address).call() == 0
    assert usdc_contract.functions.balanceOf(recipient.address).call() == 0
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


def sub_plan_balance_check_pay_portion_full_precision():
    """
    A single transaction exercising the 3 new commands:
      - root plan: WRAP_ETH, V3_SWAP_EXACT_IN, BALANCE_CHECK_ERC20, EXECUTE_SUB_PLAN
      - sub plan:  PAY_PORTION_FULL_PRECISION, SWEEP
    """
    amount_in = Wei(10**18)  # 1 ETH
    min_usdc_out = Wei(2500 * 10**6)  # 1 ETH ~ 2557 USD, so require at least 2500 USDC out
    v3_path = [weth_address, 500, usdc_address]
    portion = 5 * 10**17  # 50% (full precision: 10**18 represents 100%)

    # The sub-plan is a regular chain builder, it is not built on its own
    sub_plan = (
        codec
        .encode
        .chain()
        .pay_portion_full_precision(FunctionRecipient.CUSTOM, usdc_address, portion, recipient.address)
        .sweep(FunctionRecipient.SENDER, usdc_address, 0)
    )

    encoded_input = (
        codec
        .encode
        .chain()
        # wrap the sent ETH and swap it for USDC, keeping the output in the router
        .wrap_eth(FunctionRecipient.ROUTER, amount_in)
        .v3_swap_exact_in(FunctionRecipient.ROUTER, amount_in, min_usdc_out, v3_path, payer_is_sender=False)
        # the router must hold at least min_usdc_out USDC, otherwise the whole transaction reverts
        .balance_check_erc20(ur_address, usdc_address, min_usdc_out)
        # run the nested plan
        .execute_sub_plan(sub_plan)
        .build(codec.get_default_deadline())
    )

    trx_hash = send_transaction(amount_in, encoded_input)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'

    recipient_usdc = usdc_contract.functions.balanceOf(recipient.address).call()
    account_usdc = usdc_contract.functions.balanceOf(account.address).call()
    ur_usdc = usdc_contract.functions.balanceOf(ur_address).call()
    total_usdc = recipient_usdc + account_usdc

    assert total_usdc >= min_usdc_out, f"total usdc is {total_usdc}"
    assert recipient_usdc > 0, f"recipient usdc is {recipient_usdc}"
    assert account_usdc > 0, f"account usdc is {account_usdc}"

    # PAY_PORTION_FULL_PRECISION paid 50% of the router balance to the recipient
    assert recipient_usdc == total_usdc // 2, (
        f"recipient should get 50% of {total_usdc}, got {recipient_usdc}"
    )
    # SWEEP sent everything left in the router to the sender
    assert ur_usdc == 0, f"the router should have swept all usdc, it still holds {ur_usdc}"

    # the account paid amount_in ETH plus the gas fees
    gas_fee = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    assert w3.eth.get_balance(account.address) == initial_eth_amount - amount_in - gas_fee

    print(" => EXECUTE_SUB_PLAN with PAY_PORTION_FULL_PRECISION & BALANCE_CHECK_ERC20: OK")


def balance_check_reverts_on_insufficient_balance():
    """
    BALANCE_CHECK_ERC20 must revert the whole transaction when the owner's balance is too low.
    """
    account_usdc = usdc_contract.functions.balanceOf(account.address).call()
    assert account_usdc > 0

    encoded_input = (
        codec
        .encode
        .chain()
        # the account holds account_usdc, so asking for one more must fail
        .balance_check_erc20(account.address, usdc_address, account_usdc + 1)
        .build(codec.get_default_deadline())
    )

    trx_hash = send_transaction(0, encoded_input)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 0, f'receipt["status"] is actually {receipt["status"]}'

    # the reverted transaction did not move any USDC
    assert usdc_contract.functions.balanceOf(account.address).call() == account_usdc

    print(" => BALANCE_CHECK_ERC20 reverts on insufficient balance: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    sub_plan_balance_check_pay_portion_full_precision()
    balance_check_reverts_on_insufficient_balance()


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
