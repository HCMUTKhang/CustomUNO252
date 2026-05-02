from server.main import GameServer

localhost="localhost"
LAN_accept="0.0.0.0"

host=localhost

server = GameServer(host=host, port=5000)
server.start()

input("Server running. Press Enter to stop...\n")
server.stop()

"""
python -c "from client.controller.network_client import NetworkClient; c=NetworkClient(host='127.0.0.1', port=5000); print('connected', c.connect())"
"""