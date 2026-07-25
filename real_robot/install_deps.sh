#!/bin/bash
# Install Python 2.7 dependencies for the Baxter policy client.
# Run this on the remote PC once before first use.
#
# ROS Indigo ships with Python 2.7 and pip may be outdated — upgrade first.

set -e

echo "=== Upgrading pip ==="
python -m pip install --upgrade "pip<21"  # pip 21+ dropped Python 2.7 support

echo "=== Installing websocket-client ==="
# websocket-client 0.x supports Python 2.7; 1.x requires Python 3
pip install "websocket-client==0.59.0"

echo "=== Installing msgpack ==="
# msgpack 0.6.x is the last version supporting Python 2.7
pip install "msgpack==0.6.2"

echo "=== Installing msgpack-numpy ==="
# msgpack-numpy 0.4.x supports Python 2.7
pip install "msgpack-numpy==0.4.8"

echo "=== Installing numpy (if not present) ==="
pip install "numpy>=1.11,<1.17"   # 1.17 dropped Python 2.7

echo "=== Installing opencv-python ==="
# opencv-python 4.x dropped Python 2. Use 3.x
pip install "opencv-python==3.4.18.65"

echo ""
echo "=== Done. Verify with: ==="
echo "  python -c \"import websocket, msgpack, msgpack_numpy, cv2, numpy; print('OK')\""
