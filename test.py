import web3

from snet.sdk import SnetSDK

from snet.snet_cli.utils.utils import get_address_from_private, get_contract_object, normalize_private_key

import test_pb2_grpc
import eth_utils
import test_pb2
from snet.sdk.training import training

org_id = "test-ilya-goerli-id"
service_id = "ilya_test_service"
group_name = "default_groups"

config = {
    "private_key": "e7638fd785fdb5cf12df0b1d7b5584cc20d4e8526403f0df105aadf23728f538",
    "eth_rpc_endpoint": "https://goerli.infura.io/v3/92a117f286914f259e30d3338aad054d",
}

snet_sdk = SnetSDK(config)
print("snet_sdk")

service_client = snet_sdk.create_service_client(org_id, service_id, test_pb2_grpc.CalculatorStub, group_name)
print("2")

# print("service_client")
account = snet_sdk.account
# tx = snet_sdk.mpe_contract.channel_extend(account=account, channel_id=17, expiration=1)
# snet_sdk.mpe_contract.open_channel()
# print(tx)
balance = snet_sdk.mpe_contract.balance(address=account.address)
print(account.address)
# print(balance)
# tx = snet_sdk.mpe_contract.channel_add_funds(account=account, channel_id=17, amount=100000000)
# tx = snet_sdk.mpe_contract.deposit_and_open_channel(account=account, payment_address=account.address, group_id=group_name, amount=1, expiration=10)
# print(tx)
# block_offset = 240
# default_expiration = service_client.default_channel_expiration()
# service_call_price = service_client.get_price()
# payment_channel = service_client.deposit_and_open_channel(service_call_price, default_expiration + block_offset)
# print(payment_channel)
# request = example_service_pb2.Numbers(a=20, b=3)
# print("request")
# print(eth_utils.to_normalized_address())
print("get_address_from_private: ", get_address_from_private(config["private_key"]))
# print(web3.Web3.to_text(eth_utils.to_canonical_address(get_address_from_private(account.signer_private_key))))
tr = training.TrainingModel()
resp = tr.create_model(service_client)

# current_block_number = service_client.get_current_block_number()
# message = web3.Web3.solidity_keccak(
#     ["string", "address", "uint256"],
#     ["__CreateModel", web3.Web3.to_checksum_address(service_client.account.address)
#         , 1200]
# )
# print(message)
# print(str(message))
# print(service_client.generate_signature(message))

import hashlib
import codecs
from Crypto.Hash import keccak
from ecdsa import SigningKey, SECP256k1

# text = "__CreateModel"
block_number = 1200  # Your block number here

# message = b''.join([
#     text.encode('utf-8'),
#     service_client.account.address.encode('utf-8'),
#     block_number.to_bytes(32, byteorder='big')
# ])
#
# print("message bytes: ", message)
# print("message bytes py view: ", codecs.decode(message, 'unicode_escape'))
# print("message str: ", str(message))
#
# hash_1 = keccak.new(digest_bits=256)
# hash_1.update(b'\x19Ethereum Signed Message:\n')
# hash_1.update(len(message).to_bytes(32, byteorder='big'))
# hash_1.update(message)
#
# hash_2 = keccak.new(digest_bits=256)
# hash_2.update(hash_1.digest())
#
# print("hash: ", hash_2.hexdigest())
# print("hash str: ", hash_2.hexdigest())

import hashlib
import ecdsa
import codecs

# private_key_str = "e7638fd785fdb5cf12df0b1d7b5584cc20d4e8526403f0df105aadf23728f538"
#
# # Преобразование строки в байты
# private_key_bytes = codecs.decode(private_key_str, 'hex')
#
# # Используем кривую secp256k1 (стандартная кривая для Ethereum)
# curve = ecdsa.curves.SECP256k1
#
# # Создаем объект приватного ключа
# private_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=curve)

#
# def get_signature(text, block_number, private_key):
#     message = b"".join([
#         text.encode('utf-8'),
#         private_key.get_verifying_key().to_string('compressed'),
#         block_number.to_bytes(32, byteorder='big')  # Используем 32 байта для номера блока
#     ])
#     hash_message = hashlib.sha3_256(message).digest()
#     signature = private_key.sign_digest(hash_message, sigencode=ecdsa.util.sigencode_der_canonize)
#     return signature


# Пример использования функции get_signature
# text_to_sign = "__CreateModel"
# block_number_to_sign = 1200
#
# signature = get_signature(text_to_sign, block_number_to_sign, private_key)
# print("Подпись:", signature.hex())
# print("Подпись:", signature)
#
# print("signature: ", codecs.encode(signature, 'hex').decode('utf-8'))

# result = service_client.service.mul(request)
# print("result")
# print("Performing 20 + 3: {}".format(result))   # Performing 20 * 3: value: 60
