# -*- coding: utf-8 -*-
from plugin.wrapper import EvmLoaderProgram
from solana.rpc.api import Client
from solana.account import Account
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction, Transaction
import unittest
import time
import os

solana_url = os.environ.get("SOLANA_URL")
if solana_url is None:
    print("Please set SOLANA_URL environment")
    exit(1)
http_client = Client(solana_url)

evm_loader = os.environ.get("EVM_LOADER")  #"CLBfz3DZK4VBYAu6pCgDrQkNwLsQphT9tg41h6TQZAh3"

if evm_loader is None:
    print("Please set EVM_LOADER environment")
    exit(1)

def confirm_transaction(client, tx_sig):
    """Confirm a transaction."""
    TIMEOUT = 30  # 30 seconds  pylint: disable=invalid-name
    elapsed_time = 0
    while elapsed_time < TIMEOUT:
        sleep_time = 3
        if not elapsed_time:
            sleep_time = 7
            time.sleep(sleep_time)
        else:
            time.sleep(sleep_time)
        resp = client.get_confirmed_transaction(tx_sig)
        if resp["result"]:
#            print('Confirmed transaction:', resp)
            break
        elapsed_time += sleep_time
    if not resp["result"]:
        raise RuntimeError("could not confirm transaction: ", tx_sig)
    return resp

class EvmLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acc = Account(b'\xdc~\x1c\xc0\x1a\x97\x80\xc2\xcd\xdfn\xdb\x05.\xf8\x90N\xde\xf5\x042\xe2\xd8\x10xO%/\xe7\x89\xc0<')
        print('Account:', cls.acc.public_key(), bytes(cls.acc.public_key()).hex())
        print('Private:', cls.acc.secret_key())
        balance = http_client.get_balance(cls.acc.public_key())['result']['value']
        if balance == 0:
            tx = http_client.request_airdrop(cls.acc.public_key(), 10*10**9)
            confirm_transaction(http_client, tx['result'])
            balance = http_client.get_balance(cls.acc.public_key())['result']['value']
        print('Balance:', balance)

        # caller created with "50b41b481f04ac2949c9cc372b8f502aa35bddd1" ethereum address
        cls.caller = PublicKey("A8semLLUsg5ZbhACjD2Vdvn8gpDZV1Z2dPwoid9YUr4S")

    def test_createAccount(self):
        program = EvmLoaderProgram()
        # lamports, space, ether, signer_key, program_key, system_program_key
        trx = Transaction().add(
            program.createAccount(1000, 1000, sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3])
            )
        result = http_client.send_transaction(trx, self.acc)

if __name__ == '__main__':
    unittest.main()
