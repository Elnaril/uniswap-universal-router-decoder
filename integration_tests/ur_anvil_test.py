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

chain_id = 1
initial_block_number = 23491937
initial_eth_amount = 10000 * 10**18  # Anvil provides 10000 ETH by default
transient_eth_balance = initial_eth_amount

erc20_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'  # noqa
weth_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'  # noqa
weth_address = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
weth_contract = w3.eth.contract(address=weth_address, abi=weth_abi)

usdc_address = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)

# Latest Universal Router address
ur_address = Web3.to_checksum_address("0x66a9893cc07d91d95644aedd05d03f95e1dba8af")

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
    time.sleep(5)  # Increased wait time for anvil to fully start
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
    assert usdc_contract.functions.balanceOf(account.address).call() == 0
    print(" => Initialization: OK")


def send_transaction(encoded_input, value):
    trx_params = encoded_input.build_transaction(
        account.address,
        value,
        block_identifier=w3.eth.block_number
    )
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    return trx_hash


def wrap_unwrap():
    global transient_eth_balance
    in_amount = Wei(10**18)
    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, in_amount)
        .unwrap_weth(FunctionRecipient.SENDER, in_amount)
    )
    trx_hash = send_transaction(encoded_input, in_amount)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    trx_fee = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    eth_balance = w3.eth.get_balance(account.address)
    assert eth_balance == transient_eth_balance - trx_fee, f"eth_balance: {eth_balance}, transient_eth_balance: {transient_eth_balance},trx_fee: {trx_fee}"  # noqa E501
    transient_eth_balance = eth_balance
    print(" => WRAP ETH and UNWRAP WETH: OK")


def buy_usdc_from_v2_and_sell_to_v3():
    global transient_eth_balance
    # Wrap, Buy for 0.3 eth of usdc from v2, Sell to v3 and Unwrap
    v2_path = [weth_address, usdc_address]
    v2_in_amount = Wei(3 * 10**17)
    v2_out_amount = Wei(817968342)  # with slippage
    v3_path = [usdc_address, 500, weth_address]
    v3_out_amount = Wei(int(2.98 * 10**17))  # with slippage
    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, v2_in_amount)
        .v2_swap_exact_in(FunctionRecipient.ROUTER, v2_in_amount, v2_out_amount, v2_path, payer_is_sender=False)
        .v3_swap_exact_in_from_balance(FunctionRecipient.ROUTER, v3_out_amount, v3_path)
        .unwrap_weth(FunctionRecipient.SENDER, 0)
    )
    trx_hash = send_transaction(encoded_input, v2_in_amount)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    trx_fee = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    eth_balance = w3.eth.get_balance(account.address)
    assert transient_eth_balance - v2_in_amount * 0.01 - trx_fee < eth_balance < transient_eth_balance - trx_fee, f"eth_balance: {eth_balance}, transient_eth_balance: {transient_eth_balance},trx_fee: {trx_fee}"  # noqa E501
    transient_eth_balance = eth_balance

    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    assert usdc_balance == 0, f"usdc balance is actually: {usdc_balance}"

    weth_balance = weth_contract.functions.balanceOf(account.address).call()
    assert weth_balance == 0, f"weth balance is actually: {weth_balance}"

    print(" => WRAP ETH, BUY USDC from V2, SELL USDC to V3, and UNWRAP WETH: OK")


def buy_usdc_from_v3_and_sell_to_v2():
    global transient_eth_balance
    # Wrap, Buy for 0.3 eth of usdc from v3, Sell to v2 and Unwrap
    v3_path = [weth_address, 500, usdc_address]
    v3_in_amount = Wei(3 * 10 ** 17)
    v3_out_amount = Wei(817968342)  # with slippage

    v2_path = [usdc_address, weth_address]
    v2_out_amount = Wei(int(2.98 * 10 ** 17))  # with slippage

    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, v3_in_amount)
        .v3_swap_exact_in(FunctionRecipient.ROUTER, v3_in_amount, v3_out_amount, v3_path, payer_is_sender=False)
        .v2_swap_exact_in_from_balance(FunctionRecipient.ROUTER, v2_out_amount, v2_path)
        .unwrap_weth(FunctionRecipient.SENDER, 0)
    )
    trx_hash = send_transaction(encoded_input, v3_in_amount)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    trx_fee = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    eth_balance = w3.eth.get_balance(account.address)
    assert transient_eth_balance - v3_in_amount * 0.01 - trx_fee < eth_balance < transient_eth_balance - trx_fee, f"eth_balance: {eth_balance}, transient_eth_balance: {transient_eth_balance},trx_fee: {trx_fee}"  # noqa E501
    transient_eth_balance = eth_balance

    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    assert usdc_balance == 0, f"usdc balance is actually: {usdc_balance}"

    weth_balance = weth_contract.functions.balanceOf(account.address).call()
    assert weth_balance == 0, f"weth balance is actually: {weth_balance}"

    print(" => WRAP ETH, BUY USDC from V3, SELL USDC to V2, and UNWRAP WETH: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    wrap_unwrap()
    buy_usdc_from_v2_and_sell_to_v3()
    buy_usdc_from_v3_and_sell_to_v2()


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
