# CustomUNO252
A multiplayer turn-based card game with a host room architecture and a set of custom house rules.

# Network Architecture & Testing

## 1. Networking Concept & Implementation
The networking layer is built using raw **TCP Sockets** (`socket`) and the **Host-Authoritative** model. To ensure the game runs smoothly without freezing the Pygame UI, the implementation relies heavily on multi-threading and thread-safe queues.

### Core Architecture
* **Host-Authoritative Model:** The player who creates the room acts as the Host. Their machine runs both the central `GameServer` (which holds the absolute truth of the game state) and a `NetworkClient` (for their own UI).
* **Server-Side (`network_server.py`):**
  * Runs a main `accept_connections` loop in the background.
  * Spawns a **dedicated daemon thread for each connected client**. This allows the server to continuously `recv()` messages from multiple players simultaneously without blocking.
* **Client-Side (`network_client.py`):**
  * Upon connecting, it immediately spawns a background listening thread.
  * **Non-Blocking UI:** Instead of processing messages directly (which would crash Pygame), the background thread parses incoming JSON strings and pushes them into a thread-safe `queue.Queue`. The Pygame main loop simply polls this queue frame-by-frame (`get_messages()`), keeping the UI perfectly responsive.
* **Message Protocol:** All data is packaged into Data Transfer Objects (DTOs) defined in `message_protocol.py` and serialized to **JSON** before being sent over TCP.

---

## 2. Testing the Connection Layer

To verify that the TCP socket communication and threading are working correctly without Pygame, we use a simple dummy client script.

### The Test Script (`test_network.py`)
```python
import time
from client.controller.network_client import NetworkClient

client = NetworkClient(host='127.0.0.1', port=5000)
print("Connected:", client.connect())
time.sleep(10)  # Keep connection alive to observe server logs

Execution & Expected Output
1. Start the Server:

Bash
python -m server.main
Server Output:

Plaintext
[GAMESERVER] Initialized at localhost:5000
[GAMESERVER] Starting server...
[SERVER] Started on localhost:5000
[GAMESERVER] Server started successfully

============================================================
  Custom UNO Online - Server Running
============================================================
  Host: localhost
  Port: 5000
  Waiting for player connections...
  Press Ctrl+C to stop
============================================================
2. Run the Client(s):
Execute the test script in a new terminal. You can run it multiple times to simulate multiple players joining.

Bash
python test_network.py
Client Output:

Plaintext
[CLIENT] Connected to 127.0.0.1:5000
Connected: True
3. Server Log Reactions:
As clients connect and the script finishes its 10-second sleep, the server will log the lifecycle:

Plaintext
[SERVER] Client 0 connected from ('127.0.0.1', 60657)
[SERVER] Client 0 forcefully disconnected
[SERVER] Client 0 removed from server
[SERVER] Client 1 connected from ('127.0.0.1', 60659)
[SERVER] Client 1 forcefully disconnected
[SERVER] Client 1 removed from server
(Note: The "forcefully disconnected" log is expected here, as the test script terminates abruptly after time.sleep() without sending a graceful exit payload).

4. Shutting Down:
Pressing Ctrl+C on the server terminal gracefully shuts down the threads:

Plaintext
[MAIN] Shutdown signal received
[GAMESERVER] Stopping server...
[SERVER] Shutting down...
[SERVER] Shutdown complete
[GAMESERVER] Server stopped
[MAIN] Server stopped