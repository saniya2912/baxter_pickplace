#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Connection test — sends a dummy observation to the policy server and prints
the returned action chunk. NO robot motion. Run this before baxter_policy_client.py
to verify the network, serialisation, and image format are all correct.

Usage:
    python test_connection.py --host 192.168.0.103 --task 0
"""

from __future__ import print_function

import argparse
import time

import numpy as np
import websocket
import msgpack
import msgpack_numpy

msgpack_numpy.patch()

IMG_SIZE = 224

TASKS = {
    0: "move the red block to the far side",
    1: "move the red block to the near side",
    2: "move the blue block to the far side",
    3: "move the blue block to the near side",
    4: "move the green block to the far side",
    5: "move the green block to the near side",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="192.168.0.103")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--task", "-t", type=int, default=0)
    args = parser.parse_args()

    prompt = TASKS[args.task]
    url = "ws://{}:{}".format(args.host, args.port)

    print("Connecting to {} ...".format(url))
    ws = websocket.WebSocket()
    ws.connect(url)

    meta_raw = ws.recv()
    meta = msgpack.unpackb(meta_raw, raw=False)
    print("Server metadata: {}".format(meta))

    # Build a dummy observation (random images, zero state)
    dummy_img   = np.zeros((3, IMG_SIZE, IMG_SIZE), dtype=np.uint8)
    dummy_state = np.zeros(11, dtype=np.float32)

    obs = {
        "observation/image":       dummy_img,
        "observation/wrist_image": dummy_img,
        "observation/state":       dummy_state,
        "prompt":                  prompt,
    }

    print("Sending dummy observation (task {}: '{}') ...".format(args.task, prompt))
    t0 = time.time()
    packed = msgpack.packb(obs)
    ws.send_binary(packed)
    raw = ws.recv()
    elapsed_ms = (time.time() - t0) * 1000.0

    response = msgpack.unpackb(raw, raw=False)
    chunk = np.array(response["actions"])

    print("")
    print("Round-trip latency : {:.1f} ms".format(elapsed_ms))
    print("Action chunk shape : {}".format(chunk.shape))
    print("First action (q_target)  : {}".format(np.round(chunk[0, :7], 4)))
    if chunk.shape[1] > 7:
        print("First action (gripper)   : {:.4f}".format(float(chunk[0, 7])))
    if "server_timing" in response:
        print("Server inference time    : {:.1f} ms".format(
            response["server_timing"].get("infer_ms", -1)))
    print("")
    print("Connection test PASSED.")
    ws.close()


if __name__ == "__main__":
    main()
