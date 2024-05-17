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
permit2_address = Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")

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


def buy_usdc():
    amount_in = 1 * 10**18
    amount_out_min = 0
    v3_path = [weth_address, 500, usdc_address]
    encoded_input = (
        codec
        .encode
        .chain()
        .wrap_eth(FunctionRecipient.ROUTER, amount_in)
        # can chain one of the 2 following v3 swap functions:
        .v3_swap_exact_in_from_balance(FunctionRecipient.SENDER, amount_out_min, v3_path)
        # .v3_swap_exact_in(FunctionRecipient.SENDER, amount_in, amount_out_min, v3_path, payer_is_sender=False)
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(amount_in, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    assert usdc_balance == 1956854186

    print(" => BUY USDC: OK")


def approve_permit2_for_usdc():
    contract_function = usdc_contract.functions.approve(permit2_address, 2**256 - 1)
    trx_params = contract_function.build_transaction(
        {
            "from": account.address,
            "gas": gas_limit,
            "maxPriorityFeePerGas": w3.eth.max_priority_fee,
            "maxFeePerGas": Wei(30 * 10**9),
            "type": '0x2',
            "chainId": chain_id,
            "value": 0,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    raw_transaction = w3.eth.account.sign_transaction(trx_params, account.key).rawTransaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success
    print(" => APPROVE PERMIT2 FOR USDC: OK")


def sell_usdc_part_1():
    amount_in = 500 * 10**6
    amount_out_min = 0
    v3_path = [usdc_address, 500, weth_address]

    amount, expiration, nonce = codec.fetch_permit2_allowance(account.address, usdc_address)
    assert amount == expiration == nonce == 0, "Wrong Permit2 allowance"
    print("Permit2 allowance before sell part 1:", amount, expiration, nonce)

    permit_data, signable_message = codec.create_permit2_signable_message(
        usdc_address,
        amount_in,  # max/infinite = 2**160 - 1
        # 2**160 - 1,
        codec.get_default_expiration(),  # 30 days
        nonce,  # Permit2 nonce
        ur_address,
        codec.get_default_deadline(),
        chain_id,
    )
    signed_message = account.sign_message(signable_message)

    encoded_input = (
        codec
        .encode
        .chain()
        .permit2_permit(permit_data, signed_message)
        .v3_swap_exact_in(FunctionRecipient.SENDER, amount_in, amount_out_min, v3_path, payer_is_sender=True)  # /!\  payer is sender  # noqa
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(0, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    assert usdc_balance == 1456854186

    weth_balance = weth_contract.functions.balanceOf(account.address).call()
    assert weth_balance == 255256875527333931

    print(" => SELL USDC for WETH PART 1: OK")


def sell_usdc_part_2():
    amount_in = 500 * 10**6
    amount_out_min = 0
    v3_path = [usdc_address, 500, weth_address]

    amount, expiration, nonce = codec.fetch_permit2_allowance(account.address, usdc_address)
    assert amount == 0, "Wrong Permit2 allowance amount"  # allowance fully used in sell_usdc_part_1()
    assert expiration > 0, "Wrong Permit2 allowance expiration"
    assert nonce == 1, "Wrong Permit2 allowance nonce"
    print("Permit2 allowance before sell part 2:", amount, expiration, nonce)

    permit_data, signable_message = codec.create_permit2_signable_message(
        usdc_address,
        # amount_in,  # max/infinite = 2**160 - 1
        2**160 - 1,
        codec.get_default_expiration(40 * 24 * 3600),  # 30 days
        nonce,  # Permit2 nonce
        ur_address,
        codec.get_default_deadline(),
        chain_id,
    )
    signed_message = account.sign_message(signable_message)

    encoded_input = (
        codec
        .encode
        .chain()
        .permit2_permit(permit_data, signed_message)
        .v3_swap_exact_in(FunctionRecipient.SENDER, amount_in, amount_out_min, v3_path, payer_is_sender=True)  # /!\  payer is sender  # noqa
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(0, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx success

    usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
    assert usdc_balance == 956854186

    weth_balance = weth_contract.functions.balanceOf(account.address).call()
    assert weth_balance == 510513624712717843

    amount, expiration, nonce = codec.fetch_permit2_allowance(account.address, usdc_address)
    assert amount == 2**160 - 1, "Wrong Permit2 allowance amount"  # infinite allowance
    assert expiration > 0, "Wrong Permit2 allowance expiration"
    assert nonce == 2, "Wrong Permit2 allowance nonce"
    print("Permit2 allowance after sell part 2:", amount, expiration, nonce)

    print(" => SELL USDC for WETH PART 2: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    buy_usdc()
    approve_permit2_for_usdc()
    sell_usdc_part_1()
    sell_usdc_part_2()


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
