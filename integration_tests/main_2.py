import os
import subprocess
import time

from eth_utils import keccak
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
chain_id = 1337
block_number = 17621078
gas_limit = 800_000

account = Account.from_key(keccak(text="moo"))
assert account.address == "0xcd7328a5D376D5530f054EAF0B9D235a4Fd36059"
init_amount = 100 * 10**18
transient_eth_balance = init_amount

erc20_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'  # noqa
weth_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'  # noqa
weth_address = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
weth_contract = w3.eth.contract(address=weth_address, abi=weth_abi)

usdc_address = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)

ur_address = Web3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD")

codec = RouterCodec()


def launch_ganache():
    ganache_process = subprocess.Popen(
        f"""ganache
        --logging.quiet='true'
        --fork.url='{web3_provider}'
        --fork.blockNumber='{block_number}'
        --miner.defaultGasPrice='15000000000'
        --wallet.accounts='{account.key.hex()}','{init_amount}'
        """.replace("\n", " "),
        shell=True,
    )
    time.sleep(3)
    parent_id = ganache_process.pid
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
    assert w3.eth.chain_id == chain_id  # 1337
    assert w3.eth.block_number == block_number + 1
    assert w3.eth.get_balance(account.address) == init_amount
    assert usdc_contract.functions.balanceOf(account.address).call() == 0
    print(" => Initialization: OK")


def send_transaction(value, encoded_data):
    trx_params = {
        "from": account.address,
        "to": ur_address,
        "gas": gas_limit,
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": Wei(30 * 10**9),
        "type": '0x2',
        "chainId": chain_id,
        "value": value,
        "nonce": w3.eth.get_transaction_count(account.address),
        "data": encoded_data,
    }
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).rawTransaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    return trx_hash


def wrap_unwrap():
    global transient_eth_balance
    in_amount = 10**18
    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, in_amount)
        .unwrap_weth(FunctionRecipient.SENDER, in_amount)
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(in_amount, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    trx_fee = receipt["gasUsed"] * receipt["effectiveGasPrice"]
    eth_balance = w3.eth.get_balance(account.address)
    assert eth_balance == transient_eth_balance - trx_fee, f"eth_balance: {eth_balance}, transient_eth_balance: {transient_eth_balance},trx_fee: {trx_fee}"  # noqa E501
    transient_eth_balance = eth_balance


def buy_usdc_from_v2_and_sell_to_v3():
    global transient_eth_balance
    # Wrap, Buy for 0.3 eth of usdc from v2, Sell to v3 and Unwrap
    v2_path = [weth_address, usdc_address]
    v2_in_amount = 3 * 10**17
    v2_out_amount = 581526000  # with slippage
    v3_path = [usdc_address, 500, weth_address]
    v3_out_amount = int(2.98 * 10**17)  # with slippage
    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, v2_in_amount)
        .v2_swap_exact_in(FunctionRecipient.ROUTER, v2_in_amount, v2_out_amount, v2_path, payer_is_sender=False)
        .v3_swap_exact_in_from_balance(FunctionRecipient.ROUTER, v3_out_amount, v3_path, payer_is_sender=False)
        .unwrap_weth(FunctionRecipient.SENDER, 0)
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(v2_in_amount, encoded_input)

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
    v3_in_amount = 3 * 10 ** 17
    v3_out_amount = 581526000  # with slippage

    v2_path = [usdc_address, weth_address]
    v2_out_amount = int(2.98 * 10 ** 17)  # with slippage

    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, v3_in_amount)
        .v3_swap_exact_in(FunctionRecipient.ROUTER, v3_in_amount, v3_out_amount, v3_path, payer_is_sender=False)
        .v2_swap_exact_in_from_balance(FunctionRecipient.ROUTER, v2_out_amount, v2_path, payer_is_sender=False)
        .unwrap_weth(FunctionRecipient.SENDER, 0)
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(v3_in_amount, encoded_input)

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
    ganache_pid = launch_ganache()
    try:
        launch_integration_tests()
        print_success_message()
    finally:
        kill_processes(ganache_pid)


if __name__ == "__main__":
    main()
