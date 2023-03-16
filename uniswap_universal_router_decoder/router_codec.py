"""
Decode and encode data sent to Uniswap universal router functions.

* Author: Elnaril (https://www.fiverr.com/elnaril, https://github.com/Elnaril).
* License: MIT.
* Doc: https://github.com/Elnaril/uniswap-universal-router-decoder
"""
from datetime import datetime
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)

from eth_account.messages import (
    encode_structured_data,
    SignableMessage,
)
from web3 import Web3
from web3.types import (
    ChecksumAddress,
    Wei,
)

from uniswap_universal_router_decoder._abi_builder import _ABIBuilder
from uniswap_universal_router_decoder._constants import _structured_data_permit
from uniswap_universal_router_decoder._decoder import _Decoder
from uniswap_universal_router_decoder._encoder import _Encoder


__author__ = "Elnaril"
__license__ = "MIT"
__status__ = "Development"


class RouterCodec:
    def __init__(self, w3: Optional[Web3] = None, rpc_endpoint: Optional[str] = None) -> None:
        self._abi_map = _ABIBuilder().build_abi_map()
        if w3:
            self._w3 = w3
        elif rpc_endpoint:
            self._w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        else:
            self._w3 = Web3()
        self.decode = _Decoder(self._w3, self._abi_map)
        self.encode = _Encoder(self._w3, self._abi_map)

    @staticmethod
    def get_default_deadline(valid_duration: int = 180) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 180
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def get_default_expiration(valid_duration: int = 30 * 24 * 3600) -> int:
        """
        :return: timestamp corresponding to now + valid_duration seconds. valid_duration default is 30 days
        """
        return int(datetime.now().timestamp() + valid_duration)

    @staticmethod
    def get_max_expiration() -> int:
        """
        :return: max timestamp allowed for permit expiration
        """
        return 2 ** 48 - 1

    @staticmethod
    def create_permit2_signable_message(
            token_address: ChecksumAddress,
            amount: Wei,
            expiration: int,
            nonce: int,
            spender: ChecksumAddress,
            deadline: int,
            chain_id: int = 1) -> Tuple[Dict[str, Any], SignableMessage]:
        """
        Create a eth_account.messages.SignableMessage that will be sent to the UR/Permit2 contracts
        to set token permissions through signature validation.

        See https://docs.uniswap.org/contracts/permit2/reference/allowance-transfer#single-permit

        See https://eips.ethereum.org/EIPS/eip-712 for EIP712 structured data signing.

        In addition to this step, the Permit2 contract has to be approved through the token contract.

        :param token_address: The address of the token for which an allowance will be given to the UR
        :param amount: The allowance amount in Wei. Max = 2 ** 160 - 1
        :param expiration: The Unix timestamp at which a spender's token allowances become invalid
        :param nonce: An incrementing value indexed per owner,token,and spender for each signature
        :param spender: The spender (ie: the UR) address
        :param deadline: The deadline, as a Unix timestamp, on the permit signature
        :param chain_id: What it says on the box. Default to 1.
        :return: A tuple: (PermitSingle, SignableMessage).
            The first element is the first parameter of permit2_permit().
            The second element must be signed with eth_account.signers.local.LocalAccount.sign_message() in your code
            and the resulting SignedMessage is the 2nd parameter of permit2_permit().
        """
        permit_details = {
            "token": token_address,
            "amount": amount,
            "expiration": expiration,
            "nonce": nonce,
        }
        permit_single = {
            "details": permit_details,
            "spender": spender,
            "sigDeadline": deadline,
        }
        structured_data = dict(_structured_data_permit)
        structured_data["domain"]["chainId"] = chain_id
        structured_data["message"] = permit_single
        return permit_single, encode_structured_data(primitive=structured_data)
