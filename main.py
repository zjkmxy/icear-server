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

    server.run()

    deeplab_inst.join_all()
    fst_inst.join_all()
    deeplab_inst.shutdown()
    fst_inst.shutdown()


if __name__ == "__main__":
    main()
