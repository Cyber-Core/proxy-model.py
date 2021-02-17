# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.
"""
import random
from datetime import datetime
from typing import List, Tuple
from urllib import parse as urlparse
import json
import unittest

from solana.rpc.api import Client
from solana.account import Account as sol_Account
from solana.transaction import AccountMeta, TransactionInstruction, Transaction
from solana.sysvar import *

from ..common.constants import DEFAULT_BUFFER_SIZE, DEFAULT_HTTP_PORT
from ..common.utils import socket_connection, text_, build_http_response
from ..http.codes import httpStatusCodes
from ..http.parser import HttpParser
from ..http.websocket import WebsocketFrame
from ..http.server import HttpWebServerBasePlugin, httpProtocolTypes

from .eth_proto import Trx as EthTrx

from solana.rpc.api import Client as SolanaClient
from solana.rpc.types import TxOpts
from solana.account import Account as SolanaAccount
from solana.transaction import AccountMeta, TransactionInstruction, Transaction
from sha3 import keccak_256
import base58
import traceback
from .erc20_wrapper import EthereumAddress, create_program_address, sender_eth, evm_loader_id, getLamports, \
    getAccountInfo,  call, deploy, transaction_history, solana_cli, solana_url


class Account:
    def __init__(self, balance):
        self.balance = balance
        self.trxCount = 1

    def __repr__(self):
        return str(self.__dict__)

class Receipt:
    def __init__(self, receiptId, sender, receiver):
        self.block = None
        self.index = None
        self.id = receiptId
        self.sender = sender
        self.receiver = receiver

    def initBlock(self, block, index):
        if self.block: raise Exception("Transaction already included in block {}".format(block.number))
        (self.block, self.index) = (block, index)


class EthereumModel:
    def __init__(self):
        # Initialize user account
        cli = solana_cli(solana_url)
        res = cli.call("config get")
        res = res.splitlines()[-1]
        substr = "Keypair Path: "
        if not res.startswith(substr):
            raise Exception("cannot get keypair path")
        path = res[len(substr):]
        with open(path.strip(), mode='r') as file:
            pk = (file.read())
            nums = list(map(int, pk.strip("[]").split(',')))
            nums = nums[0:32]
            values = bytes(nums)
            self.signer = sol_Account(values)

        self.client = SolanaClient('http://localhost:8899')
        self.signatures = {}
        self.vrs = {}
        self.eth_sender = {}
        self.contract_address = {}
        # self.signer = SolanaAccount(b'\xdc~\x1c\xc0\x1a\x97\x80\xc2\xcd\xdfn\xdb\x05.\xf8\x90N\xde\xf5\x042\xe2\xd8\x10xO%/\xe7\x89\xc0<')

        self.contracts = {}
        self.accounts = {}
        self.caller_ether = bytes.fromhex(sender_eth)
        (self.caller, self.caller_nonce) = create_program_address(self.caller_ether.hex(), evm_loader_id)

        pass

    def eth_chainId(self):
        return "0x10"

    def net_version(self):
        return '1600243666737'

    def eth_gasPrice(self):
        return 0

    def eth_estimateGas(self, param):
        return 0

    def __repr__(self):
        return str(self.__dict__)

    def eth_blockNumber(self):
        slot = self.client.get_slot()['result']
        print("eth_blockNumber", hex(slot))
        return hex(slot)

    def eth_getBalance(self, account, tag):
        """account - address to check for balance.
           tag - integer block number, or the string "latest", "earliest" or "pending"
        """
        eth_acc = EthereumAddress(account)
        print('eth_getBalance:', account, eth_acc)
        balance = getLamports(self.client, evm_loader_id, eth_acc)
        return hex(balance*10**9)

    def eth_getBlockByNumber(self, tag, full):
        """Returns information about a block by block number.
            tag - integer of a block number, or the string "earliest", "latest" or "pending", as in the default block parameter.
            full - If true it returns the full transaction objects, if false only the hashes of the transactions.
        """
        if tag in ('earliest', 'latest', 'pending'): raise Exception("Invalid tag {}".format(tag))
        number = int(tag, 16)
        response = self.client.get_confirmed_block(number)
        if 'error' in response:
            raise Exception(response['error']['message'])

        block = response['result']
        signatures = [trx['transaction']['signatures'][0] for trx in block['transactions']]
        eth_signatures = []
        for signature in signatures:
            eth_signature = '0x'+keccak_256(base58.b58decode(signature)).hexdigest()
            self.signatures[eth_signature] = signature
            eth_signatures.append(eth_signature)

        return {
            "number": number,
            "gasLimit": "0x6691b7",
            "transactions": eth_signatures,
        }

#       {
#            "number":tag,
#            "hash":"0x40baaba3f7cd6397ebdfe105a778854418112f6218969ae0600907936dea7077",
#            "parentHash":"0x312f4c211e84a7f8cd53e7ecb90ad194e58bcea15dfdfed4314412a5d7f4c8bf",
#            "mixHash":"0x0000000000000000000000000000000000000000000000000000000000000000",
#            "nonce":"0x0000000000000000",
#            "sha3Uncles":"0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
#            "logsBloom":"0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
#            "transactionsRoot":"0x0f1662bc2d4cca30a1e039d72b4fc39fe2fbb32f4d79e4ec21add97c446a3352",
#            "stateRoot":"0x9714bb6d61f0c6095cb14f526a98e546e6dd35d8ac60e11682fc5f984c7ce761",
#            "receiptsRoot":"0x056b23fbba480696b65fe5a59b8f2148a1299103c4f57df839233af2cf4ca2d2",
#            "miner":"0x0000000000000000000000000000000000000000",
#            "difficulty":"0x0",
#            "totalDifficulty":"0x0",
#            "extraData":"0x",
#            "size":"0x3e8",
#            "gasLimit":"0x6691b7",
#            "gasUsed":"0x5208",
#            "timestamp":"0x5f61ea48",
#            "transactions":[
#                "0x7fe4d5e32ad2099940654c7871079a7dcdf84b592823ad6a2f7835a55453fae1"
#            ],
#            "uncles":[]
#        }

    def eth_call(self, obj, tag):
        """Executes a new message call immediately without creating a transaction on the block chain.
           Parameters
            obj - The transaction call object
                from: DATA, 20 Bytes - (optional) The address the transaction is sent from.
                to: DATA, 20 Bytes - The address the transaction is directed to.
                gas: QUANTITY - (optional) Integer of the gas provided for the transaction execution. eth_call consumes zero gas, but this parameter may be needed by some executions.
                gasPrice: QUANTITY - (optional) Integer of the gasPrice used for each paid gas
                value: QUANTITY - (optional) Integer of the value sent with this transaction
                data: DATA - (optional) Hash of the method signature and encoded parameters. For details see Ethereum Contract ABI in the Solidity documentation
            tag - integer block number, or the string "latest", "earliest" or "pending", see the default block parameter
        """
        if not obj['data']: raise Exception("Missing data")
        try:
            input = bytearray.fromhex(obj['data'][2:])
            input[0:0] = bytearray.fromhex("03")

            (contract_sol, contract_nonce) = create_program_address(obj['to'][2:], evm_loader_id)
            (res, log) = call(input, evm_loader_id, contract_sol, self.caller, self.signer, self.client)
            if not res.startswith("Program log: "):
                raise Exception("Invalid program logs: no result")
            else:
                return "0x"+res[13:]
        except:
            return '0x'

    def eth_getTransactionCount(self, account, tag):
        print('eth_getTransactionCount:', account)
        try:
            info = getAccountInfo(self.client, evm_loader_id, EthereumAddress(account))
            return hex(info.trx_count)
        except:
            return hex(0)

    def eth_getTransactionReceipt(self, trxId):
        receipt = self.signatures.get(trxId, None)
        print('getTransactionReceipt:', trxId, receipt)
        if not receipt:
            print ("Not found receipt")
            return {
            "transactionHash":'0x0',
            "transactionIndex":'0x0',
            "blockHash":'0x0',
            "blockNumber":'0x0',
            "from":'0x0',
            "to":'0x0',
            "gasUsed":'0x0',
            "cumulativeGasUsed":'0x0',
            "contractAddress":'0x0',
            "logs":[],
            "status":"0x0",
            "logsBloom":'0x0'
            }

        trx = self.client.get_confirmed_transaction(receipt)
        # print('RECEIPT:', json.dumps(trx, indent=3))
        if trx['result'] is None: return None

        block = self.client.get_confirmed_block(trx['result']['slot'])
        # print('BLOCK:', json.dumps(block, indent=3))

        data = base58.b58decode(trx['result']['transaction']['message']['instructions'][0]['data'])
        print('DATA:', data.hex())

        return {
            "transactionHash":trxId,
            "transactionIndex":hex(0),
            "blockHash":'0x%064x'%trx['result']['slot'],
            "blockNumber":hex(trx['result']['slot']),
            "from":'0x'+self.eth_sender[trxId],
            "to":'0x'+data[17:37].hex(),
            "gasUsed":'0x%x' % trx['result']['meta']['fee'],
            "cumulativeGasUsed":'0x%x' % trx['result']['meta']['fee'],
            "contractAddress":self.contract_address.get(trxId),
            "logs":[],
            "status":"0x1",
            "logsBloom":"0x"+'0'*512
        }

    def eth_getTransactionByHash(self, trxId):
        receipt = self.signatures.get(trxId, None)
        print('getTransactionReceipt:', trxId, receipt)
        if not receipt:
            print ("Not found receipt")
            return {
                "blockHash":'0x0',
                "blockNumber":'0x0',
                "from":'0x0',
                "gas":'0x0',
                "gasPrice":'0x0',
                "hash":'0x0',
                "input":'0x0',
                "nonce":'0x0',
                "to":'0x0',
                "transactionIndex":'0x0',
                "value":'0x0',
                "v":'0x0',
                "r":'0x0',
                "s":'0x0'
            }

        trx = self.client.get_confirmed_transaction(receipt)
        # print('RECEIPT:', json.dumps(trx, indent=3))
        if trx['result'] is None: return None

        block = self.client.get_confirmed_block(trx['result']['slot'])
        # print('BLOCK:', json.dumps(block, indent=3))

        data = base58.b58decode(trx['result']['transaction']['message']['instructions'][0]['data'])
        print('DATA:', data.hex())
        sender =  self.eth_sender[trxId]
        # nonce = int(self.eth_getTransactionCount('0x'+data[sender].hex(), ""), 16)
        nonce = 0
        # if nonce > 0 :
        #     nonce = nonce - 1
        ret = {
            "blockHash":'0x%064x'%trx['result']['slot'],
            "blockNumber":hex(trx['result']['slot']),
            "from":'0x'+sender,
            "gas":'0x%x' % trx['result']['meta']['fee'],
            "gasPrice":'0x00',
            "hash":trxId,
            "input":"0x"+data.hex(),
            "nonce":hex(nonce),
            "to":'0x'+data[17:37].hex(),
            "transactionIndex":hex(0),
            "value":'0x00',
            "v":hex(self.vrs[trxId][0]),
            "r":hex(self.vrs[trxId][1]),
            "s":hex(self.vrs[trxId][2])
        }
        print ("eth_getTransactionByHash:", ret);
        return ret

    def eth_getCode(self, param,  param1):
        return "0x01"

#{'jsonrpc': '2.0', 'result': {
#    'meta': {
#        'err': None,
#        'fee': 5000,
#        'innerInstructions': [
#            {
#                'index': 0,
#                'instructions': [{'accounts': [0, 1], 'data': '11119WdDob9tURrs1mPLQsrxBNt4Hgrq7j8oszjq1UwKoypjtc1QY25xrACwsSDQHQ4Xjg', 'programIdIndex': 3}]
#            }],
#        'postBalances': [9857358240, 928, 1072563840, 1],
#        'preBalances': [9857364240, 0, 1072563840, 1],
#        'status': {'Ok': None}},
#        'slot': 172315,
#        'transaction': {
#            'message': {
#                'accountKeys': [
#                    'Bfj8CF5ywavXyqkkuKSXt5AVhMgxUJgHfQsQjPc1JKzj',
#                    'GTeuLioCKcJ5cm7Dq7swaZT9u1VQsvVauHTRRJ6cL1mW',
#                    'CEU7e6wxzZgAYLeECkSGbfzuKd5Jha4F4JT7Y7UwEaGz',
#                    '11111111111111111111111111111111'],
#                'header': {
#                    'numReadonlySignedAccounts': 0,
#                    'numReadonlyUnsignedAccounts': 2,
#                    'numRequiredSignatures': 1},
#                'instructions': [
#                    {
#                        'accounts': [1, 2, 3, 0],
#                        'data': 'JJ91ggb4n23E5XiMHmXxJRKYi8RJfcZqqMeyAnmdPh23NVygpyeWrRAZEX74ypk53WGsCEstgAWdSvoef9ZUn2FdHVANoQfgU2pD',
#                        'programIdIndex': 2
#                    }],
#                'recentBlockhash': '4nSmpVWkwTEH8Z9wZd8dXAYK3ZLvAbHPg943UMwTgH2W'
#            },
#            'signatures': ['4m3r2stsX18edAJWpEFAubMYAvCoJqbfHjZMtfq3n6t9jDuxiRJznVveoCpzrKdLaAcBqWyxFtVXFqepvF9zf2wZ']
#        }
#    },
#    'id': 27}

#            "transactionHash":receipt,
#            "transactionIndex":"0x0",
#            "blockHash":receipt,
#            "blockNumber":"0x%x" % self.blockNumber,
#            "from":sender,
#            "to":toAddress,
#            "gasUsed":"0x5208",
#            "cumulativeGasUsed":"0x5208",
#            "contractAddress":None,
#            "logs":[],
#            "status":"0x1",
#            "logsBloom":"0x"+'0'*512

    def eth_sendRawTransaction(self, rawTrx):
        trx = EthTrx.fromString(bytearray.fromhex(rawTrx[2:]))
        print(json.dumps(trx.__dict__, cls=JsonEncoder, indent=3))

        sender = trx.sender()
        print('Sender:', sender)

        if trx.value and trx.callData:
            raise Exception("Simultaneous transfer of both the native and application tokens is not supported")
        elif trx.value:
            raise Exception("transfer native tokens is not implemented")
        elif trx.callData:
            if (trx.toAddress is None):
                eth_contract_addr = deploy(trx.callData, evm_loader_id)["ethereum"]
                print("DEPLOY", eth_contract_addr)
                signature = transaction_history(self.signer.public_key())
                print("SIGNATURE", signature)
                eth_signature = '0x' + keccak_256(base58.b58decode(signature)).hexdigest()
                print("ETH_SIGNATURE", eth_signature)
                self.signatures[eth_signature] = signature
                self.eth_sender[eth_signature] = sender
                self.vrs[eth_signature] = [trx.v, trx.r, trx.s]
                self.contract_address[eth_signature] = eth_contract_addr
                return eth_signature
            else:
                try:
                    input = bytearray(trx.callData)
                    input[0:0] = bytearray.fromhex("03")

                    (contract_sol, contract_nonce) = create_program_address(bytes(trx.toAddress).hex(), evm_loader_id)
                    (sender_sol, sender_nonce) = create_program_address(sender, evm_loader_id)
                    (res, log) = call(input, evm_loader_id, contract_sol, sender_sol, self.signer, self.client)

                    if not res.startswith("Program log: "):
                        print("Invalid program logs: no result")
                        raise Exception("Invalid program logs: no result")
                    else:
                        signature = log["result"]["transaction"]["signatures"][0]
                        print('Transaction signature:', signature)
                        eth_signature = '0x' + keccak_256(base58.b58decode(signature)).hexdigest()
                        self.signatures[eth_signature] = signature
                        self.vrs[eth_signature] = [trx.v, trx.r, trx.s]
                        self.eth_sender[eth_signature] = sender
                        print('Ethereum signature:', eth_signature)
                        return eth_signature
                except:
                    return '0x0'
        else:
            raise Exception("Missing token for transfer")


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return json.JSONEncoder.default(self, obj)


class SolanaContractTests(unittest.TestCase):
    def setUp(self):
        self.model = EthereumModel()
        self.owner = '0xc1566af4699928fdf9be097ca3dc47ece39f8f8e'
        self.token1 = '0x49a449cd7fd8fbcf34d103d98f2c05245020e35b'
#        self.assertEqual(self.getBalance(self.owner), 1000*10**18)
#        self.assertEqual(self.getBalance(self.token1), 0)

    def getBalance(self, account):
        return int(self.model.eth_getBalance(account, 'latest'), 16)

    def getBlockNumber(self):
        return int(self.model.eth_blockNumber(), 16)

    def getTokenBalance(self, token, account):
        return self.model.contracts[token].balances.get(account, 0)

    def test_transferFunds(self):
        (sender, receiver, amount) = (self.owner, '0x8d900bfa2353548a4631be870f99939575551b60', 123*10**18)
        senderBalance = self.getBalance(sender)
        receiverBalance = self.getBalance(receiver)
        blockNumber = self.getBlockNumber()

        receiptId = self.model.eth_sendRawTransaction('0xf8730a85174876e800825208948d900bfa2353548a4631be870f99939575551b608906aaf7c8516d0c0000808602e92be91e86a040a2a5d73931f66185e8526f09c4d0dc1f389c1b9fcd5e37a012839e6c5c70f0a00554615806c3fa7dc7c8096b3bfed5a29354045e56982bdf3ee11f649e53d51e')
        print('ReceiptId:', receiptId)

        self.assertEqual(self.getBalance(sender), senderBalance - amount)
        self.assertEqual(self.getBalance(receiver), receiverBalance + amount)
        self.assertEqual(self.getBlockNumber(), blockNumber+1)

        receipt = self.model.eth_getTransactionReceipt(receiptId)
        print('Receipt:', receipt)

        block = self.model.eth_getBlockByNumber(receipt['blockNumber'], False)
        print('Block:', block)

        self.assertTrue(receiptId in block['transactions'])

    def test_transferTokens(self):
        (token, sender, receiver, amount) = ('0xcf73021fde8654e64421f67372a47aa53c4341a8', '0x324726ca9954ed9bd567a62ae38a7dd7b4eaad0e', '0xb937ad32debafa742907d83cb9749443160de0c4', 32)
        senderBalance = self.getTokenBalance(token, sender)
        receiverBalance = self.getTokenBalance(token, receiver)
        blockNumber = self.getBlockNumber()


        receiptId = self.model.eth_sendRawTransaction('0xf8b018850bdfd63e00830186a094b80102fd2d3d1be86823dd36f9c783ad0ee7d89880b844a9059cbb000000000000000000000000cac68f98c1893531df666f2d58243b27dd351a8800000000000000000000000000000000000000000000000000000000000000208602e92be91e86a05ed7d0093a991563153f59c785e989a466e5e83bddebd9c710362f5ee23f7dbaa023a641d304039f349546089bc0cb2a5b35e45619fd97661bd151183cb47f1a0a')
        print('ReceiptId:', receiptId)

        self.assertEqual(self.getTokenBalance(token, sender), senderBalance - amount)
        self.assertEqual(self.getTokenBalance(token, receiver), receiverBalance + amount)

        receipt = self.model.eth_getTransactionReceipt(receiptId)
        print('Receipt:', receipt)

        block = self.model.eth_getBlockByNumber(receipt['blockNumber'], False)
        print('Block:', block)

        self.assertTrue(receiptId in block['transactions'])



class SolanaProxyPlugin(HttpWebServerBasePlugin):
    """Extend in-built Web Server to add Reverse Proxy capabilities.
    """

    SOLANA_PROXY_LOCATION: str = r'/solana$'
    SOLANA_PROXY_PASS = [
        b'http://localhost:8545/'
    ]

    def __init__(self, *args):
        HttpWebServerBasePlugin.__init__(self, *args)
        self.model = SolanaProxyPlugin.getModel()

    @classmethod
    def getModel(cls):
        if not hasattr(cls, 'modelInstance'):
            cls.modelInstance = EthereumModel()
        return cls.modelInstance

    def routes(self) -> List[Tuple[int, str]]:
        return [
            (httpProtocolTypes.HTTP, SolanaProxyPlugin.SOLANA_PROXY_LOCATION),
            (httpProtocolTypes.HTTPS, SolanaProxyPlugin.SOLANA_PROXY_LOCATION)
        ]

    def handle_request(self, request: HttpParser) -> None:
        print('< ', request.body.decode('utf8'))
        req = json.loads(request.body)
        res = {'id':req['id'], 'jsonrpc':'2.0'}

        try:
            method = getattr(self.model, req['method'])
            res['result'] = method(*req['params'])
        except Exception as err:
            traceback.print_exc()
            res['error'] = {'code': -32000, 'message': str(err)}
#            with socket_connection(('localhost', 8545)) as conn:
#                conn.send(request.build())
#                orig = HttpParser.response(memoryview(conn.recv(DEFAULT_BUFFER_SIZE)))
#                print('- ', orig.body.decode('utf8'))

        print('> ', json.dumps(res))

        self.client.queue(memoryview(build_http_response(
            httpStatusCodes.OK, body=json.dumps(res).encode('utf8'),
            headers={b'Content-Type': b'application/json'})))

    def on_websocket_open(self) -> None:
        pass

    def on_websocket_message(self, frame: WebsocketFrame) -> None:
        pass

    def on_websocket_close(self) -> None:
        pass

