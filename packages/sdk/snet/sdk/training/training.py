import importlib
from urllib.parse import urlparse

import grpc
import web3
from eth_account import Account

from snet.sdk.payment_strategies.payment_staregy import PaymentStrategy
from snet.snet_cli.utils.utils import RESOURCES_PATH, add_to_path
from snet.sdk.root_certificate import root_certificate
from snet.snet_cli.resources.proto import training_pb2_grpc
from snet.snet_cli.resources.proto import training_pb2
from snet_cli.utils import config


# from packages.snet_cli.snet.snet_cli.resources.proto import training_pb2
# from packages.snet_cli.snet.snet_cli.resources.proto import training_pb2_grpc


# def generate_signature(service_client):
# org_id, service_id, group_id, daemon_endpoint = service_client.get_service_details()
# email, token_for_free_call, token_expiry_date_block = service_client.get_free_call_config()

# if token_expiry_date_block == 0 or len(email) == 0 or len(token_for_free_call) == 0:
#     raise Exception(
#         "You are using default 'FreeCallPaymentStrategy' to use this strategy you need to pass "
#         "'free_call_auth_token-bin','email','free-call-token-expiry-block' in config")

# current_block_number = service_client.get_current_block_number()
# message = web3.Web3.solidity_keccak(
#     ["string", "address", "uint256"],
#     ["__CreateModel", web3.Web3.to_checksum_address(service_client.account.address)
#         , 1200]
# )
# return

class TrainingModel:

    def create_model(self, service_client):
        try:
            # org_id, service_id, group_id, daemon_endpoint = service_client.get_service_details()
            daemon_endpoint = 'http://localhost:7000'
            # email, token_for_free_call, token_expiry_date_block = service_client.get_free_call_config()

            # if not token_for_free_call:
            #     return False

            # with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            #     training_pb2 = importlib.import_module("training_pb2")
            #
            # with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            #     training_pb2_grpc = importlib.import_module("training_pb2_grpc")

            endpoint_object = urlparse(daemon_endpoint)
            if endpoint_object.port is not None:
                channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
            else:
                channel_endpoint = endpoint_object.hostname

            if endpoint_object.scheme == "http":
                print("creating http channel: ", channel_endpoint)
                channel = grpc.insecure_channel(channel_endpoint)
            elif endpoint_object.scheme == "https":
                channel = grpc.secure_channel(channel_endpoint,
                                              grpc.ssl_channel_credentials(root_certificates=root_certificate))
            else:
                raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))

            stub = training_pb2_grpc.ModelStub(channel)

            # Создание подписи
            # from eth_account.messages import encode_defunct
            # msghash = encode_defunct(text="__CreateModel")
            # print(msghash)
            # signed_msg = Account.sign_message(msghash, "e7638fd785fdb5cf12df0b1d7b5584cc20d4e8526403f0df105aadf23728f538")
            # print(signed_msg)
            message = "__CreateModel"
            signature = service_client.generate_training_signature2(message, service_client.account.address, 1200)
            # "e7638fd785fdb5cf12df0b1d7b5584cc20d4e8526403f0df105aadf23728f538")

            # message, signature, current_block_number
            # print("current_block_number: ", current_block_number)
            print("service_client.account.address: ", service_client.account.address)
            auth_req = training_pb2.AuthorizationDetails(signature=bytes(signature), current_block=1200,
                                                         signer_address=service_client.account.address,
                                                         message=message)
            model_details = training_pb2.ModelDetails(grpc_method_name="train", grpc_service_name="service",
                                                      model_name="model_name_s")
            # print("auth_req: ", auth_req)
            response = stub.create_model(
                training_pb2.CreateModelRequest(authorization=auth_req, model_details=model_details))
            print("client received: ", response)
            return response
        except Exception as e:
            print("Exception: ", e)
            raise e
            return False
