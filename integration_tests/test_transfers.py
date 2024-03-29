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
block_number = 19167456
gas_limit = 800_000

sender = Account.from_key(keccak(text="moo"))
assert sender.address == "0xcd7328a5D376D5530f054EAF0B9D235a4Fd36059"
init_amount = 100 * 10**18

recipients = tuple(Account.from_key(keccak(text=sound)) for sound in ("baa", "maa", "wehee", "oink", "gaggle", "kut"))

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
        --miner.defaultGasPrice='30000000000'
        --wallet.accounts='{sender.key.hex()}','{init_amount}'
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
    assert w3.eth.get_balance(sender.address) == init_amount
    for acc in recipients + (sender, ):
        assert usdc_contract.functions.balanceOf(acc.address).call() == 0
    print(" => Initialization: OK")


def send_transaction(value, encoded_data):
    trx_params = {
        "from": sender.address,
        "to": ur_address,
        "gas": gas_limit,
        "maxPriorityFeePerGas": w3.eth.max_priority_fee,
        "maxFeePerGas": w3.eth.gas_price + w3.eth.max_priority_fee,
        "type": '0x2',
        "chainId": chain_id,
        "value": value,
        "nonce": w3.eth.get_transaction_count(sender.address),
        "data": encoded_data,
    }
    raw_transaction = w3.eth.account.sign_transaction(trx_params, sender.key).rawTransaction
    trx_hash = w3.eth.send_raw_transaction(raw_transaction)
    return trx_hash


def buy_and_transfer():
    """
    Sender is going to use eth to:
      - send 100 USDC to 4 recipients and the sender (total: 500 usdc)
      - send 0.1 eth to the 2 other recipients (total: 0.2 eth)
    """
    usdc_amount_per_recipient = Wei(100 * 10**6)
    eth_amount_per_recipient = Wei(int(0.1 * 10**18))
    amount_in_max = Wei(int(0.22 * 10**18))  # for weth -> usdc swap
    amount_out = Wei(5 * usdc_amount_per_recipient)
    value = amount_in_max + 2 * eth_amount_per_recipient  # eth sent to the UR

    v3_path = [weth_address, 500, usdc_address]
    eth_address = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

    encoded_input = (
        codec
        .encode
        .chain()
        # weth conversion and swap
        .wrap_eth(FunctionRecipient.ROUTER, amount_in_max)
        .v3_swap_exact_out(FunctionRecipient.ROUTER, amount_out, amount_in_max, v3_path, payer_is_sender=False)
        # usdc transfer
        .transfer(FunctionRecipient.SENDER, usdc_address, usdc_amount_per_recipient)  # transfer usdc to sender
        .transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount_per_recipient, recipients[0].address)  # transfer usdc to 1st recipient  # noqa
        .transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount_per_recipient, recipients[1].address)  # transfer usdc to 2nd recipient  # noqa
        .transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount_per_recipient, recipients[2].address)  # transfer usdc to 3rd recipient  # noqa
        .transfer(FunctionRecipient.CUSTOM, usdc_address, usdc_amount_per_recipient, recipients[3].address)  # transfer usdc to 4th recipient  # noqa
        # eth transfer
        .transfer(FunctionRecipient.CUSTOM, eth_address, eth_amount_per_recipient, recipients[4].address)  # transfer eth to 5th recipient  # noqa
        .transfer(FunctionRecipient.CUSTOM, eth_address, eth_amount_per_recipient, recipients[5].address)  # transfer eth to 6th recipient  # noqa
        .unwrap_weth(FunctionRecipient.SENDER, 0)  # unwrap and send back all remaining eth to sender
        .build()
    )

    trx_hash = send_transaction(value, encoded_input)

    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx status

    assert usdc_contract.functions.balanceOf(sender.address).call() == usdc_amount_per_recipient
    for i in range(4):
        assert usdc_contract.functions.balanceOf(recipients[i].address).call() == usdc_amount_per_recipient

    for i in range(4, 6):
        assert w3.eth.get_balance(recipients[i].address) == eth_amount_per_recipient

    sender_eth_balance = w3.eth.get_balance(sender.address)
    print("Sender ETH balance", sender_eth_balance / 10**18)
    assert sender_eth_balance == 99573567178309372475, f"Actual ETH balance is {sender_eth_balance}"

    print(" => BUY & TRANSFER USDC/ETH: OK")


def simple_transfers():
    """
    48 ETH transfers in one transaction
    """
    value = Wei(10**18)
    total_value = 48 * value
    eth_address = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")

    chain = codec.encode.chain()
    for _ in range(8):
        for j in range(6):
            chain = chain.transfer(FunctionRecipient.CUSTOM, eth_address, value, recipients[j].address)

    encoded_input = chain.build()

    trx_hash = send_transaction(total_value, encoded_input)
    receipt = w3.eth.wait_for_transaction_receipt(trx_hash)
    assert receipt["status"] == 1, f'receipt["status"] is actually {receipt["status"]}'  # trx status

    for i in range(6):
        print(recipients[i].address, w3.eth.get_balance(recipients[i].address))
        assert w3.eth.get_balance(recipients[i].address) >= 8 * 10**18

    gas_used = receipt["gasUsed"]
    print("Gas used (total/per transfer):", gas_used, gas_used // 48)
    assert receipt["gasUsed"] == 557986 < 48 * 21000

    print(" => SIMPLE ETH MASS TRANSFERS: OK")


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    buy_and_transfer()
    simple_transfers()


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
