
import os
from dotenv import load_dotenv
from typing import List
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.messages import encode_defunct
from utils import load_abi
from types import SafeTransaction, OperationType
from constants import SAFE_MULTISEND_ADDRESS

load_dotenv()

RPC_URL = os.getenv("RPC_URL")
PK = os.getenv("PK")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

account = Account.from_key(PK)

def get_safe_contract(safe_address: str):
    return w3.eth.contract(address=safe_address, abi=load_abi("safeAbi"))

def sign_transaction_hash(message_hash: bytes) -> bytes:
    signature = account.sign_message(encode_defunct(primitive=message_hash))
    # Adjust 'v' value for Gnosis Safe
    v = signature.v
    if v in (0, 1):
        v += 31
    elif v in (27, 28):
        v += 4
    return signature.r.to_bytes(32, 'big') + signature.s.to_bytes(32, 'big') + v.to_bytes(1, 'big')

def _create_safe_multisend_transaction(txns: List[SafeTransaction]) -> SafeTransaction:
    multisend_contract = w3.eth.contract(address=SAFE_MULTISEND_ADDRESS, abi=load_abi("multisendAbi"))
    encoded_txs = b''
    for txn in txns:
        encoded_txs += w3.codec.encode_abi(
            ['uint8', 'address', 'uint256', 'uint256', 'bytes'],
            [txn['operation'].value, txn['to'], txn['value'], len(txn['data']), txn['data']]
        )
    
    data = multisend_contract.encodeABI(fn_name="multiSend", args=[encoded_txs])
    return {
        "to": SAFE_MULTISEND_ADDRESS,
        "value": 0,
        "data": bytes.fromhex(data[2:]),
        "operation": OperationType.DELEGATE_CALL,
    }

def aggregate_transaction(txns: List[SafeTransaction]) -> SafeTransaction:
    if len(txns) == 1:
        return txns[0]
    return _create_safe_multisend_transaction(txns)

def sign_and_execute_safe_transaction(safe_address: str, txn: SafeTransaction, gas_options: dict = None):
    safe_contract = get_safe_contract(safe_address)
    nonce = safe_contract.functions.nonce().call()
    
    tx_hash = safe_contract.functions.getTransactionHash(
        txn['to'],
        txn['value'],
        txn['data'],
        txn['operation'].value,
        0,  # safeTxGas
        0,  # baseGas
        0,  # gasPrice
        "0x0000000000000000000000000000000000000000",  # gasToken
        "0x0000000000000000000000000000000000000000",  # refundReceiver
        nonce
    ).call()

    signature = sign_transaction_hash(tx_hash)

    tx_params = {
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
    }
    if gas_options:
        tx_params.update(gas_options)

    tx = safe_contract.functions.execTransaction(
        txn['to'],
        txn['value'],
        txn['data'],
        txn['operation'].value,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        signature
    ).build_transaction(tx_params)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PK)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)
