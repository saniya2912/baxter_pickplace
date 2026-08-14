#!/bin/bash
# Install Python 2.7 dependencies for the Baxter policy client, from the
# offline wheels in py2_packages/.
#
# Run this on the remote PC once before first use. Installs from local
# wheels rather than PyPI directly -- this laptop's old Python 2.7 /
# OpenSSL environment has TLS/certificate problems that break direct
# `pip install <pkg>` downloads (see baxter_policy_setup_troubleshooting.md),
# so all dependencies are pre-downloaded as cp27 (or universal) wheels here.

set -e

echo "=== Upgrading pip ==="
python -m pip install --upgrade "pip<21"  # pip 21+ dropped Python 2.7 support

echo "=== Installing from offline wheels (py2_packages/) ==="
cd "$(dirname "$0")/py2_packages"
sudo pip install --no-index \
    six-1.17.0-py2.py3-none-any.whl \
    websocket_client-0.59.0-py2.py3-none-any.whl \
    msgpack-0.6.2-cp27-cp27mu-manylinux1_x86_64.whl \
    numpy-1.16.6-cp27-cp27mu-manylinux1_x86_64.whl \
    h5py-2.10.0-cp27-cp27mu-manylinux1_x86_64.whl

echo "=== Installing opencv-python (via PyPI if reachable, else see note below) ==="
# opencv-python 4.x dropped Python 2, use 3.x. Not bundled as an offline
# wheel here (large); if PyPI is unreachable from this machine, download
# opencv_python==3.4.18.65 (cp27, manylinux1, x86_64) on another machine and
# add it to py2_packages/ following the same pattern as the others.
pip install "opencv-python==3.4.18.65" || echo "  (failed -- see comment above, install manually)"

echo ""
echo "=== Done. Verify with: ==="
echo "  python -c \"import websocket, msgpack, cv2, numpy, h5py; print('OK')\""
echo ""
echo "Note: msgpack_numpy is intentionally NOT installed/used by this"
echo "project's own scripts (baxter_policy_client.py, test_connection.py,"
echo "collect_push_demos.py) -- its wire format is incompatible with the"
echo "server's encoding. Those scripts implement their own compatible"
echo "pack/unpack helpers instead. See 13aug_physical.md for why."
