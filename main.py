import argparse
from web3 import Web3
from constants import (
    USDC_ADDRESS,
    CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS,
    NEG_RISK_ADAPTER_ADDRESS,
    USDCE_DIGITS,
)
from utils import get_index_set, load_abi
from gnosis_safe import sign_and_execute_safe_transaction, aggregate_transaction
from types import SafeTransaction, OperationType


def main():
    parser = argparse.ArgumentParser(description="Interact with Polymarket Safe Wallets.")
    parser.add_argument("command", choices=["split", "merge", "redeem", "convert", "batch"])
    parser.add_argument("--safe-address", required=True, help="Address of the Gnosis Safe wallet.")
    parser.add_argument("--condition-id", help="The condition ID of the market.")
    parser.add_argument("--amount", type=int, help="The amount to split, merge, or convert.")
    parser.add_argument("--neg-risk", action="store_true", help="Whether the market has negative risk.")
    parser.add_argument("--question-ids", nargs="+", help="Question IDs for conversion.")
    parser.add_argument("--market-id", help="Market ID for conversion.")
    parser.add_argument("--redeem-amounts", nargs=2, type=int, help="Amounts to redeem for neg risk markets.")

    args = parser.parse_args()

    ctf_contract = Web3().eth.contract(abi=load_abi("ctfAbi"))
    neg_risk_adapter_contract = Web3().eth.contract(abi=load_abi("negRiskAdapterAbi"))
    gas_options = {'gasPrice': 200000000000}

    if args.command == "split":
        to = NEG_RISK_ADAPTER_ADDRESS if args.neg_risk else CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS
        data = ctf_contract.encodeABI(
            fn_name="splitPosition",
            args=[
                USDC_ADDRESS,
                bytes.fromhex("00" * 32),
                bytes.fromhex(args.condition_id[2:]),
                [1, 2],
                args.amount * (10**USDCE_DIGITS),
            ],
        )
        txn: SafeTransaction = {
            "to": to,
            "value": 0,
            "data": bytes.fromhex(data[2:]),
            "operation": OperationType.CALL,
        }
        sign_and_execute_safe_transaction(args.safe_address, txn, gas_options)

    elif args.command == "merge":
        to = NEG_RISK_ADAPTER_ADDRESS if args.neg_risk else CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS
        data = ctf_contract.encodeABI(
            fn_name="mergePositions",
            args=[
                USDC_ADDRESS,
                bytes.fromhex("00" * 32),
                bytes.fromhex(args.condition_id[2:]),
                [1, 2],
                args.amount * (10**USDCE_DIGITS),
            ],
        )
        txn: SafeTransaction = {
            "to": to,
            "value": 0,
            "data": bytes.fromhex(data[2:]),
            "operation": OperationType.CALL,
        }
        sign_and_execute_safe_transaction(args.safe_address, txn, gas_options)

    elif args.command == "redeem":
        to = NEG_RISK_ADAPTER_ADDRESS if args.neg_risk else CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS
        if args.neg_risk:
            data = neg_risk_adapter_contract.encodeABI(
                fn_name="redeemPositions",
                args=[bytes.fromhex(args.condition_id[2:]), args.redeem_amounts],
            )
        else:
            data = ctf_contract.encodeABI(
                fn_name="redeemPositions",
                args=[
                    USDC_ADDRESS,
                    bytes.fromhex("00" * 32),
                    bytes.fromhex(args.condition_id[2:]),
                    [1, 2],
                ],
            )
        txn: SafeTransaction = {
            "to": to,
            "value": 0,
            "data": bytes.fromhex(data[2:]),
            "operation": OperationType.CALL,
        }
        sign_and_execute_safe_transaction(args.safe_address, txn, gas_options)

    elif args.command == "convert":
        index_set = get_index_set(args.question_ids)
        data = neg_risk_adapter_contract.encodeABI(
            fn_name="convertPositions",
            args=[
                bytes.fromhex(args.market_id[2:]),
                index_set,
                args.amount * (10**USDCE_DIGITS),
            ],
        )
        txn: SafeTransaction = {
            "to": NEG_RISK_ADAPTER_ADDRESS,
            "value": 0,
            "data": bytes.fromhex(data[2:]),
            "operation": OperationType.CALL,
        }
        sign_and_execute_safe_transaction(args.safe_address, txn, gas_options)

    elif args.command == "batch":
        # Example of batching two split transactions
        to = CONDITIONAL_TOKENS_FRAMEWORK_ADDRESS
        data1 = ctf_contract.encodeABI(
            fn_name="splitPosition",
            args=[
                USDC_ADDRESS,
                bytes.fromhex("00" * 32),
                bytes.fromhex(args.condition_id[2:]),
                [1, 2],
                args.amount * (10**USDCE_DIGITS),
            ],
        )
        txn1: SafeTransaction = {
            "to": to,
            "value": 0,
            "data": bytes.fromhex(data1[2:]),
            "operation": OperationType.CALL,
        }

        data2 = ctf_contract.encodeABI(
            fn_name="splitPosition",
            args=[
                USDC_ADDRESS,
                bytes.fromhex("00" * 32),
                bytes.fromhex(args.condition_id[2:]),
                [1, 2],
                (args.amount + 1) * (10**USDCE_DIGITS), # a different amount
            ],
        )
        txn2: SafeTransaction = {
            "to": to,
            "value": 0,
            "data": bytes.fromhex(data2[2:]),
            "operation": OperationType.CALL,
        }

        batched_txn = aggregate_transaction([txn1, txn2])
        sign_and_execute_safe_transaction(args.safe_address, batched_txn, gas_options)

if __name__ == "__main__":
    main()