import time
from client.controller.network_client import NetworkClient

client = NetworkClient(host='172.20.10.2', port=5000)
print("Connected:", client.connect())
time.sleep(10)  # Keep connection alive

"""
python -c "from client.controller.network_client import NetworkClient; c=NetworkClient(host='127.0.0.1', port=5000); print('connected', c.connect())"
"""