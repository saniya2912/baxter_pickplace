# Baxter Policy Client — Two-PC Setup & Troubleshooting

## 1. System setup

We are running a Baxter policy client across two PCs.

### PC 1 — Baxter / client PC

Hostname:

```text
deniro-mobile-pc
```

Relevant network interfaces:

```text
eth0   192.168.0.103/24
wlan0  192.168.0.118/24
```

This PC runs:

- ROS/Baxter-side code
- `baxter_policy_client.py`
- `test_connection.py`

ROS master:

```text
192.168.0.99:11311
```

### PC 2 — Policy server PC

Ethernet interface:

```text
enp5s0
192.168.0.104/24
```

The policy server is a Python 3 process listening on:

```text
0.0.0.0:8000
```

The server was confirmed with:

```bash
sudo ss -lntp | grep :8000
```

which showed a `python3` process in `LISTEN` state on port 8000.

The server PC is connected to the same LAN as the laptop through Ethernet. The laptop is connected to the same LAN through Wi-Fi.

---

## 2. Project files

On the Baxter/client PC:

```text
~/Saniya/ros_ws/real_robot/
├── baxter_policy_client.py
├── install_deps.sh
├── test_connection.py
├── open_cameras.py
└── move_to_home.py
```

There is also a local package directory:

```text
~/Saniya/ros_ws/real_robot/py2_packages/
```

---

## 3. Python environment

The Baxter/client PC uses:

```text
Python 2.7.6
pip 9.0.1
OpenSSL 1.0.1f
```

The original dependency installation script attempted to install Python 2.7-compatible versions:

```text
websocket-client==0.59.0
msgpack==0.6.2
msgpack-numpy==0.4.8
numpy>=1.11,<1.17
opencv-python==3.4.18.65
```

Direct `pip` downloads from PyPI failed because the old Python/OpenSSL environment has TLS/certificate problems.

Errors included:

```text
Certificate did not match expected hostname: pypi.org
```

and:

```text
No matching distribution found for websocket-client==0.59.0
```

The PC has an old Ubuntu/ROS Indigo environment, so the dependency installation was handled by transferring compatible wheels from another machine.

---

## 4. Offline Python package installation

Compatible wheels were copied into:

```text
py2_packages/
```

The relevant files were:

```text
msgpack-0.6.2-cp27-cp27mu-manylinux1_x86_64.whl
msgpack_numpy-0.4.8-py2.py3-none-any.whl
numpy-1.16.6-cp27-cp27mu-manylinux1_x86_64.whl
six-1.17.0-py2.py3-none-any.whl
websocket_client-0.59.0-py2.py3-none-any.whl
```

Installation was performed locally with:

```bash
sudo pip install --no-index \
six-1.17.0-py2.py3-none-any.whl \
websocket_client-0.59.0-py2.py3-none-any.whl \
msgpack-0.6.2-cp27-cp27mu-manylinux1_x86_64.whl \
msgpack_numpy-0.4.8-py2.py3-none-any.whl
```

The installation succeeded.

The installed runtime versions were verified as:

```text
websocket       OK
msgpack         OK
msgpack_numpy   OK
numpy            1.13.1
opencv          3.3.0
```

The locally installed NumPy/OpenCV versions are older than the downloaded wheels, but imports work successfully.

---

## 5. Original networking issue

Initially the client attempted to connect to:

```text
192.168.0.103:8000
```

This was incorrect because `192.168.0.103` is the client PC itself.

The correct policy-server destination is:

```text
192.168.0.104:8000
```

The ROS master remains:

```text
192.168.0.99:11311
```

These are separate services.

### Network layout

```text
                         LAN / Wi-Fi
                              │
                ┌─────────────┴─────────────┐
                │                           │
       deniro-mobile-pc                Server PC
       Baxter/client                  Policy server
       Wi-Fi: 192.168.0.118           Ethernet:
       Ethernet: 192.168.0.103        192.168.0.104
                │                           │
                └──── WebSocket :8000 ─────┘
```

ROS:

```text
Baxter / ROS
     │
     ▼
192.168.0.99:11311
```

---

## 6. Diagnosing the network problem

The client initially reported:

```text
No route to host
```

and:

```text
Host Unreachable
```

ARP/neighbour state showed the Ethernet path to `192.168.0.104` as:

```text
FAILED
```

The cause was that the laptop and server were using different physical network interfaces while both had addresses in the same `192.168.0.0/24` subnet.

The laptop has:

```text
eth0   192.168.0.103/24
wlan0  192.168.0.118/24
```

while the server uses:

```text
enp5s0  192.168.0.104/24
```

The actual working connection is through the shared LAN/Wi-Fi network.

After resolving the network/interface issue, connectivity was confirmed.

---

## 7. Network connectivity is now working

From the client PC:

```bash
ping -c 4 192.168.0.104
```

succeeded:

```text
4 packets transmitted
4 received
0% packet loss
```

Then:

```bash
nc -zv 192.168.0.104 8000
```

succeeded:

```text
Connection to 192.168.0.104 8000 port [tcp/*] succeeded!
```

Therefore:

- Client can reach server.
- TCP port 8000 is reachable.
- Server is listening.
- The remaining problem is at the WebSocket/message-protocol level, not basic networking.

---

## 8. Current `test_connection.py` behaviour

The test client connects to the policy server using:

```python
url = "ws://{}:{}".format(args.host, args.port)
```

The default configuration shown in the file was:

```python
parser.add_argument("--host", type=str, default="192.168.0.103")
parser.add_argument("--port", type=int, default=8000)
```

Because the server is actually `192.168.0.104`, the test should be run explicitly with:

```bash
python test_connection.py --host 192.168.0.104 --port 8000
```

The test successfully establishes the TCP/WebSocket connection and receives data from the server.

However, it then fails while decoding the first received message.

The traceback points to:

```python
msgpack.unpackb(raw, raw=False)
```

with:

```text
msgpack.exceptions.ExtraData: unpack(b) received extra data
```

The client currently assumes that the first WebSocket message is a single msgpack object.

The current evidence does **not** yet establish exactly what the server is sending. It could be a different serialization/protocol format, multiple msgpack objects, or an additional header/payload structure.

---

# Setup Instructions

## A. On the server PC

Make sure the policy server is running and listening on port 8000:

```bash
sudo ss -lntp | grep :8000
```

Expected:

```text
0.0.0.0:8000
```

or equivalent listening output.

## B. On the Baxter/client PC

Check basic connectivity:

```bash
ping -c 4 192.168.0.104
```

Check port 8000:

```bash
nc -zv 192.168.0.104 8000
```

Then run:

```bash
cd ~/Saniya/ros_ws/real_robot
python test_connection.py --host 192.168.0.104 --port 8000
```

Do not replace the ROS master address:

```text
192.168.0.99:11311
```

with the policy-server address.

---

# Next Steps

The network and port connectivity are now confirmed.

The next task is to inspect the **raw first WebSocket message** received by the client, before calling `msgpack.unpackb()`.

Run on the client PC:

```bash
python - <<'EOF'
import websocket

ws = websocket.WebSocket()
ws.connect("ws://192.168.0.104:8000")

raw = ws.recv()

print("TYPE:", type(raw))
print("LENGTH:", len(raw))

if isinstance(raw, bytes):
    print("FIRST 100 BYTES:", repr(raw[:100]))
else:
    print("FIRST 500 CHARS:", repr(raw[:500]))

ws.close()
EOF
```

Use the output to determine the actual server-to-client message format.

Do **not** reinstall the Python dependencies or change the ROS configuration yet. The current evidence shows that the dependencies import correctly and the network connection to the policy server is working.
