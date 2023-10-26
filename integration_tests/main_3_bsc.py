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


web3_provider = os.environ['QUICKNODE_BSC_MAINNET']
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
chain_id = 1337
block_number = 31096415
gas_limit = 800_000

account = Account.from_key(keccak(text="moo"))
assert account.address == "0xcd7328a5D376D5530f054EAF0B9D235a4Fd36059"
init_amount = 100 * 10**18
transient_eth_balance = init_amount

erc20_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'  # noqa
wbnb_abi = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'  # noqa
wbnb_address = Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
wbnb_contract = w3.eth.contract(address=wbnb_address, abi=wbnb_abi)

usdt_address = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")
usdt_contract = w3.eth.contract(address=usdt_address, abi=erc20_abi)

ur_address = Web3.to_checksum_address("0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD")
permit2_address = Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3")
permit2_abi = '[{"inputs":[{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"AllowanceExpired","type":"error"},{"inputs":[],"name":"ExcessiveInvalidation","type":"error"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"InsufficientAllowance","type":"error"},{"inputs":[{"internalType":"uint256","name":"maxAmount","type":"uint256"}],"name":"InvalidAmount","type":"error"},{"inputs":[],"name":"InvalidContractSignature","type":"error"},{"inputs":[],"name":"InvalidNonce","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSignatureLength","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[],"name":"LengthMismatch","type":"error"},{"inputs":[{"internalType":"uint256","name":"signatureDeadline","type":"uint256"}],"name":"SignatureExpired","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"address","name":"token","type":"address"},{"indexed":false,"internalType":"address","name":"spender","type":"address"}],"name":"Lockdown","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint48","name":"newNonce","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"oldNonce","type":"uint48"}],"name":"NonceInvalidation","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"token","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint160","name":"amount","type":"uint160"},{"indexed":false,"internalType":"uint48","name":"expiration","type":"uint48"},{"indexed":false,"internalType":"uint48","name":"nonce","type":"uint48"}],"name":"Permit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"word","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"mask","type":"uint256"}],"name":"UnorderedNonceInvalidation","type":"event"},{"inputs":[],"name":"DOMAIN_SEPARATOR","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint48","name":"newNonce","type":"uint48"}],"name":"invalidateNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"wordPos","type":"uint256"},{"internalType":"uint256","name":"mask","type":"uint256"}],"name":"invalidateUnorderedNonces","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"internalType":"struct IAllowanceTransfer.TokenSpenderPair[]","name":"approvals","type":"tuple[]"}],"name":"lockdown","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"nonceBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails[]","name":"details","type":"tuple[]"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitBatch","name":"permitBatch","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"uint48","name":"expiration","type":"uint48"},{"internalType":"uint48","name":"nonce","type":"uint48"}],"internalType":"struct IAllowanceTransfer.PermitDetails","name":"details","type":"tuple"},{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"sigDeadline","type":"uint256"}],"internalType":"struct IAllowanceTransfer.PermitSingle","name":"permitSingle","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions","name":"permitted","type":"tuple"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails","name":"transferDetails","type":"tuple"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"internalType":"struct ISignatureTransfer.TokenPermissions[]","name":"permitted","type":"tuple[]"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"internalType":"struct ISignatureTransfer.PermitBatchTransferFrom","name":"permit","type":"tuple"},{"components":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"requestedAmount","type":"uint256"}],"internalType":"struct ISignatureTransfer.SignatureTransferDetails[]","name":"transferDetails","type":"tuple[]"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"bytes32","name":"witness","type":"bytes32"},{"internalType":"string","name":"witnessTypeString","type":"string"},{"internalType":"bytes","name":"signature","type":"bytes"}],"name":"permitWitnessTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"internalType":"struct IAllowanceTransfer.AllowanceTransferDetails[]","name":"transferDetails","type":"tuple[]"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint160","name":"amount","type":"uint160"},{"internalType":"address","name":"token","type":"address"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa
permit2_contract = w3.eth.contract(address=permit2_address, abi=permit2_abi)

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
    assert usdt_contract.functions.balanceOf(account.address).call() == 0
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


def buy_usdt():
    amount_in = 1 * 10**18
    amount_out_min = 0
    v3_path = [wbnb_address, 500, usdt_address]
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

    usdt_balance = usdt_contract.functions.balanceOf(account.address).call()
    assert usdt_balance == 213931846540111575874, f"USDT balance was actually: {usdt_balance}"

    print(" => BUY USDT: OK")


def approve_permit2_for_usdt():
    contract_function = usdt_contract.functions.approve(permit2_address, 2**256 - 1)
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
    print(" => APPROVE PERMIT2 FOR USDT: OK")


def sell_usdt_part_1():
    amount_in = 100 * 10**18
    amount_out_min = 0
    v3_path = [usdt_address, 500, wbnb_address]

    amount, expiration, nonce = get_permit2_allowance()
    assert amount == expiration == nonce == 0, "Wrong Permit2 allowance"
    print("Permit2 allowance before sell part 1:", amount, expiration, nonce)

    permit_data, signable_message = codec.create_permit2_signable_message(
        usdt_address,
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

    usdt_balance = usdt_contract.functions.balanceOf(account.address).call()
    assert usdt_balance == 113931846540111575874, f"USDT balance was actually: {usdt_balance}"

    wbnb_balance = wbnb_contract.functions.balanceOf(account.address).call()
    assert wbnb_balance == 466978799145556691, f"WBNB balance was actually: {wbnb_balance}"

    print(" => SELL USDT for WBNB PART 1: OK")


def sell_usdt_part_2():
    amount_in = 100 * 10**18
    amount_out_min = 0
    v3_path = [usdt_address, 500, wbnb_address]

    amount, expiration, nonce = get_permit2_allowance()
    assert amount == 0, "Wrong Permit2 allowance amount"  # allowance fully used in sell_usdc_part_1()
    assert expiration > 0, "Wrong Permit2 allowance expiration"
    assert nonce == 1, "Wrong Permit2 allowance nonce"
    print("Permit2 allowance before sell part 2:", amount, expiration, nonce)

    permit_data, signable_message = codec.create_permit2_signable_message(
        usdt_address,
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

    usdt_balance = usdt_contract.functions.balanceOf(account.address).call()
    assert usdt_balance == 13931846540111575874, f"USDT balance was actually: {usdt_balance}"

    wbnb_balance = wbnb_contract.functions.balanceOf(account.address).call()
    assert wbnb_balance == 933944384948957177, f"WBNB balance was actually: {wbnb_balance}"

    amount, expiration, nonce = get_permit2_allowance()
    assert amount == 2**160 - 1, "Wrong Permit2 allowance amount"  # infinite allowance
    assert expiration > 0, "Wrong Permit2 allowance expiration"
    assert nonce == 2, "Wrong Permit2 allowance nonce"
    print("Permit2 allowance after sell part 2:", amount, expiration, nonce)

    print(" => SELL USDT for WBNB PART 2: OK")


def get_permit2_allowance():
    return permit2_contract.functions.allowance(account.address, usdt_address, ur_address).call()


def launch_integration_tests():
    print("------------------------------------------")
    print("| Launching integration tests            |")
    print("------------------------------------------")
    check_initialization()
    buy_usdt()
    approve_permit2_for_usdt()
    sell_usdt_part_1()
    sell_usdt_part_2()


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
