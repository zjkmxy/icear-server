#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
from deeplab import DeepLab, DeepLabRequest
from fst import Fst, FstRequest
from ndn_server.server import Server, Status
from pyndn import Name, Data, Blob
from ndn_server.messages.request_msg_pb2 import OpComponent, Operations


IMG_MEAN = (104.00698793, 116.66876762, 122.67891434)
IMG_SHAPE = (236, 420, 3)


def main():
    root_path = os.path.dirname(sys.argv[0])

    deeplab_inst = DeepLab(range(1), root_path, IMG_MEAN)
    fst_inst = Fst(range(1), root_path, IMG_SHAPE)
    server = Server(deeplab_inst, fst_inst, root_path)

    ops = Operations()
    op = ops.components.add()
    op.model = bytes("deeplab", "utf-8")
    op.flags = 0
    op = ops.components.add()
    op.model = bytes("la_muse", "utf-8")
    op.flags = 0
    op = ops.components.add()
    op.model = bytes("rain_princess", "utf-8")
    op.flags = 0

    server.status_set[Name("/example01")] = Status(ops, 0.0, 0.0)

    data = Data(Name("/example01"))
    with open(os.path.join(root_path, "upload/example02/img.jpg"), "rb") as f:
        data.content = Blob(bytearray(f.read()))
    server.fetcher.on_data(None, data)

    deeplab_inst.join_all()
    fst_inst.join_all()
    deeplab_inst.shutdown()
    fst_inst.shutdown()

    for k, v in server.status_set.items():
        for op in v.operations.components:
            print(op.model.decode("utf-8"), op.flags)


if __name__ == "__main__":
    main()
