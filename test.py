from snet.sdk import SnetSDK

from snet.snet_cli.utils.utils import get_address_from_private, get_contract_object, normalize_private_key

import test_pb2_grpc
from snet.sdk.training import training

org_id = "test-ilya-goerli-id"
service_id = "ilya_test_service"
group_name = "default_groups"

config = {
    "private_key": "e7638fd785fdb5cf12df0b1d7b5584cc20d4e8526403f0df105aadf23728f538",
    "eth_rpc_endpoint": "https://goerli.infura.io/v3/92a117f286914f259e30d3338aad054d",
}

snet_sdk = SnetSDK(config)

service_client = snet_sdk.create_service_client(org_id, service_id, test_pb2_grpc.CalculatorStub, group_name)

print("service_client init")
account = snet_sdk.account
# tx = snet_sdk.mpe_contract.channel_extend(account=account, channel_id=17, expiration=1)
# snet_sdk.mpe_contract.open_channel()
# print(tx)
balance = snet_sdk.mpe_contract.balance(address=account.address)
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
# print(eth_utils.to_normalized_address())
print("get_address_from_private: ", get_address_from_private(config["private_key"]))
tr = training.TrainingModel()
resp = tr.create_model(service_client, grpc_method_name="/example_service.Calculator/train_add",
                       model_name="semyon_model", is_publicly_accessible=True,
                       training_data_link="https://goerli.infura.io", description="my model")
print("create_model: ", resp)
model_id = resp.model_details.model_id
print("new model: ", model_id)

resp = tr.get_model_status(service_client, grpc_method_name="/example_service.Calculator/train_add",
                           model_id=model_id)
print("get_model_status: ", resp)

print("get_all_models: ", tr.get_all_models(service_client, grpc_service_name='service_name',
                                            grpc_method_name="/example_service.Calculator/train_add"))

print('------------')
exit(0)


resp = tr.update_model_access(service_client, grpc_method_name="/example_service.Calculator/train_add",
                              model_name="model_name", model_id='0', is_public=True,
                              description='new desc')
print("delete model: ", resp)

resp = tr.get_model_status(service_client, grpc_method_name="/example_service.Calculator/train_add",
                           model_id=model_id)
print("model status: ", resp)
print("from model status: ", resp.model_details.model_id)

resp = tr.delete_model(service_client, grpc_method_name="/example_service.Calculator/train_add",
                       model_id=resp.model_details.model_id)
print("delete model: ", resp)

resp = tr.get_model_status(service_client, grpc_method_name="/example_service.Calculator/train_add",
                           model_id=resp.model_details.model_id)
print("model status: ", resp)
print("from model status: ", resp.model_details.model_id)
