import os
import subprocess
import time

from web3 import (
    Account,
    Web3,
)
from web3.types import Wei

from uniswap_universal_router_decoder import (
    FunctionRecipient,
    RouterCodec,
)


web3_provider = os.environ["WEB3_HTTP_PROVIDER_URL_BASE_MAINNET"]
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
chain_id = 8453
block_number = 36307425  # More recent Base block
gas_limit = 800_000

account = Account.from_key(
    "0xf7e96bcf6b5223c240ec308d8374ff01a753b00743b3a0127791f37f00c56514"
)
assert account.address == "0x1e46c294f20bC7C27D93a9b5f45039751D8BCc3e"
init_amount = 10000 * 10**18

erc20_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'  # noqa
weth_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'  # noqa
weth_address = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")

usdc_address = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)  # 6 decimals

ur_address = Web3.to_checksum_address("0x6ff5693b99212da76ad316178a184ab56d299b43")

codec = RouterCodec()


def launch_anvil():
    anvil_process = subprocess.Popen(
        " ".join(
            [
                "anvil -vvvvv",
                f"--fork-url {web3_provider}",
                f"--fork-block-number {block_number}",
                "--mnemonic-seed-unsafe 8721345628937456298",
            ]
        ),
        shell=True,
    )
    time.sleep(2)
    parent_id = anvil_process.pid
    return parent_id


def kill_processes(parent_id):
    processes = [
        str(parent_id),
    ]
    pgrep_process = subprocess.run(
        f"pgrep -P {parent_id}", shell=True, text=True, capture_output=True
    ).stdout.strip("\n")
    children_ids = pgrep_process.split("\n") if len(pgrep_process) > 0 else []
    processes.extend(children_ids)
    subprocess.run(
        f"kill {' '.join(processes)}", shell=True, text=True, capture_output=True
    )


def check_initialization():
    assert w3.eth.chain_id == chain_id  # 8453
    assert w3.eth.block_number == block_number
    assert w3.eth.get_balance(account.address) == init_amount
    assert usdc_contract.functions.balanceOf(account.address).call() == 0
    print(" => Initialization: OK")


def send_transaction(value, encoded_data):
    trx_params = {
        "from": account.address,
        "to": ur_address,
        "gas": gas_limit,
        "maxPriorityFeePerGas": 1 * 10**9,
        "maxFeePerGas": 1 * 10**9,
        "type": "0x2",
        "chainId": chain_id,
        "value": value,
        "nonce": w3.eth.get_transaction_count(account.address),
        "data": encoded_data,
    }
    raw_transaction = w3.eth.account.sign_transaction(
        trx_params, account.key
    ).raw_transaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    return trx_hash


def buy_usdc_from_v2_and_v3():
    # Buying for 1 eth of usdc from v2 and v3 pools
    v2_path = [weth_address, usdc_address]
    v2_in_amount = 1 * 10**18
    v2_out_amount = 3200 * 10**6  # with slippage
    v3_path = [weth_address, 500, usdc_address]
    v3_in_amount = 1 * 10**18
    v3_out_amount = 3200 * 10**6  # with slippage
    total_in_amount = Wei(v2_in_amount + v3_in_amount)
    encoded_input = (
        codec.encode.chain()
        .wrap_eth(FunctionRecipient.ROUTER, total_in_amount)
        .v2_swap_exact_in(
            FunctionRecipient.SENDER,
            v2_in_amount,
            v2_out_amount,
            v2_path,
            payer_is_sender=False,
        )
        .v3_swap_exact_in(
            FunctionRecipient.SENDER,
            v3_in_amount,
            v3_out_amount,
            v3_path,
            payer_is_sender=False,
        )
        .build(codec.get_default_deadline())
    )
    trx_hash = send_transaction(total_in_amount, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1  # trx success
    assert w3.eth.get_balance(account.address) < init_amount - total_in_amount
    bought_usdc = usdc_contract.functions.balanceOf(account.address).call()
    print(f"Bought USDC: {bought_usdc}")
    assert (
        bought_usdc == 8743089218
    ), f"Expected exactly 8743089218 USDC, but got {bought_usdc}"

    print(" => BUY USDC: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    buy_usdc_from_v2_and_v3()


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
