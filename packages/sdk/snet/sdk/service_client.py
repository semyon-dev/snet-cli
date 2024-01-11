import base64
import codecs
import collections
import importlib

import eth_utils
import hashlib
import ecdsa
import codecs
import grpc
import web3
from eth_account import Account

import snet.sdk.generic_client_interceptor as generic_client_interceptor
from eth_account.messages import defunct_hash_message, encode_defunct
from rfc3986 import urlparse
from snet.sdk.mpe.payment_channel_provider import PaymentChannelProvider
from snet.snet_cli.utils.utils import RESOURCES_PATH, add_to_path
from snet.sdk.root_certificate import root_certificate


class _ClientCallDetails(
    collections.namedtuple(
        '_ClientCallDetails',
        ('method', 'timeout', 'metadata', 'credentials')),
    grpc.ClientCallDetails):
    pass


class ServiceClient:
    def __init__(self, org_id, service_id, service_metadata, group, service_stub, payment_strategy,
                 options, mpe_contract, account, sdk_web3):
        self.org_id = org_id
        self.service_id = service_id
        self.options = options
        self.group = group
        self.service_metadata = service_metadata

        self.payment_strategy = payment_strategy
        self.expiry_threshold = self.group["payment"]["payment_expiration_threshold"]
        self.__base_grpc_channel = self._get_grpc_channel()
        self.grpc_channel = grpc.intercept_channel(self.__base_grpc_channel,
                                                   generic_client_interceptor.create(self._intercept_call))
        self.payment_channel_provider = PaymentChannelProvider(sdk_web3,
                                                               self._generate_payment_channel_state_service_client(),
                                                               mpe_contract)
        self.service = self._generate_grpc_stub(service_stub)
        self.payment_channels = []
        self.last_read_block = 0
        self.account = account
        self.sdk_web3 = sdk_web3
        self.mpe_address = mpe_contract.contract.address

    def _get_payment_expiration_threshold_for_group(self):
        pass

    def _generate_grpc_stub(self, service_stub):
        grpc_channel = self.__base_grpc_channel
        disable_blockchain_operations = self.options.get("disable_blockchain_operations", False)
        if disable_blockchain_operations is False:
            grpc_channel = self.grpc_channel
        stub_instance = service_stub(grpc_channel)
        return stub_instance

    def get_grpc_base_channel(self):
        return self.__base_grpc_channel

    def _get_grpc_channel(self):
        endpoint = self.options.get("endpoint", None)
        if endpoint is None:
            endpoint = self.service_metadata.get_all_endpoints_for_group(self.group["group_name"])[0]
        endpoint_object = urlparse(endpoint)
        if endpoint_object.port is not None:
            channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
        else:
            channel_endpoint = endpoint_object.hostname

        if endpoint_object.scheme == "http":
            return grpc.insecure_channel(channel_endpoint)
        elif endpoint_object.scheme == "https":
            return grpc.secure_channel(channel_endpoint,
                                       grpc.ssl_channel_credentials(root_certificates=root_certificate))
        else:
            raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))

    def _get_service_call_metadata(self):
        metadata = self.payment_strategy.get_payment_metadata(self)
        return metadata

    def _intercept_call(self, client_call_details, request_iterator, request_streaming,
                        response_streaming):
        metadata = []
        if client_call_details.metadata is not None:
            metadata = list(client_call_details.metadata)
        metadata.extend(self._get_service_call_metadata())
        client_call_details = _ClientCallDetails(
            client_call_details.method, client_call_details.timeout, metadata,
            client_call_details.credentials)
        return client_call_details, request_iterator, None

    def _filter_existing_channels_from_new_payment_channels(self, new_payment_channels):
        new_channels_to_be_added = []

        # need to change this logic ,use maps to manage channels so that we can easily navigate it
        for new_payment_channel in new_payment_channels:
            existing_channel = False
            for existing_payment_channel in self.payment_channels:
                if new_payment_channel.channel_id == existing_payment_channel.channel_id:
                    existing_channel = True
                    break

            if not existing_channel:
                new_channels_to_be_added.append(new_payment_channel)

        return new_channels_to_be_added

    def load_open_channels(self):
        current_block_number = self.sdk_web3.eth.block_number
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        new_payment_channels = self.payment_channel_provider.get_past_open_channels(self.account, payment_address,
                                                                                    group_id, self.last_read_block)
        self.payment_channels = self.payment_channels + self._filter_existing_channels_from_new_payment_channels(
            new_payment_channels)
        self.last_read_block = current_block_number
        return self.payment_channels

    def get_current_block_number(self):
        return self.sdk_web3.eth.block_number

    def update_channel_states(self):
        for channel in self.payment_channels:
            channel.sync_state()
        return self.payment_channels

    def default_channel_expiration(self):
        current_block_number = self.sdk_web3.eth.get_block("latest").number
        return current_block_number + self.expiry_threshold

    def _generate_payment_channel_state_service_client(self):
        grpc_channel = self.__base_grpc_channel
        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")
        return state_service_pb2_grpc.PaymentChannelStateServiceStub(grpc_channel)

    def open_channel(self, amount, expiration):
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        return self.payment_channel_provider.open_channel(self.account, amount, expiration, payment_address,
                                                          group_id)

    def deposit_and_open_channel(self, amount, expiration):
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        return self.payment_channel_provider.deposit_and_open_channel(self.account, amount, expiration,
                                                                      payment_address, group_id)

    def get_price(self):
        return self.group["pricing"][0]["price_in_cogs"]

    def generate_signature(self, message):
        signature = bytes(self.sdk_web3.eth.account.signHash(defunct_hash_message(message),
                                                             self.account.signer_private_key).signature)

        return signature

    # Функция для создания подписи
    def generate_training_signature2(self, text, address,  block_number):
        message = web3.Web3.solidity_keccak(
            ["string", "uint256"],
            [text, block_number]
        )
        signature = self.sdk_web3.eth.account.signHash(defunct_hash_message(message),
                                                       self.account.signer_private_key).signature

        # Создание подписи
        from eth_account.messages import encode_defunct
        # msghash = encode_defunct(text=text)
        print("MSG HASH: ", message)
        print("self.account.signer_private_key: ", self.account.signer_private_key)
        # signed_msg = Account.sign_message(message, self.account.signer_private_key)
        # print("signed_msg: ", signed_msg)

        # Получение подписи
        # self.account.signer_private_key
        # signed_message = self.sdk_web3.eth.account.sign_message(signed_msg, private_key=self.account.signer_private_key)
        return signature

    # def generate_training_signature(self, message, block_number, private_key_str: str):
    #     # Преобразование строки в байты
    #     private_key_bytes = codecs.decode(private_key_str, 'hex')
    #
    #     # Используем кривую secp256k1 (стандартная кривая для Ethereum)
    #     curve = ecdsa.curves.SECP256k1
    #
    #     # Создаем объект приватного ключа
    #     private_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=curve)
    #
    #     message = b"".join([
    #         message.encode('utf-8'),
    #         private_key.get_verifying_key().to_string('compressed'),
    #         block_number.to_bytes(32, byteorder='big')  # Используем 32 байта для номера блока
    #     ])
    #     hash_message = hashlib.sha3_256(message).digest()
    #     signature = private_key.sign_digest(hash_message, sigencode=ecdsa.util.sigencode_der_canonize)
    #
    #     return signature, message.hex()

    def get_free_call_config(self):
        return self.options['email'], self.options['free_call_auth_token-bin'], self.options[
            'free-call-token-expiry-block']

    def get_service_details(self):
        return self.org_id, self.service_id, self.group["group_id"], \
            self.service_metadata.get_all_endpoints_for_group(self.group["group_name"])[0]

    def get_concurrency_flag(self):
        return self.options.get('concurrency', True)

    def get_concurrency_token_and_channel(self):
        return self.payment_strategy.get_concurrency_token_and_channel(self)

    def set_concurrency_token_and_channel(self, token, channel):
        self.payment_strategy.concurrency_token = token
        self.payment_strategy.channel = channel
