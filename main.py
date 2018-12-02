#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, logging

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "PyCNL", "python"))

from config import *
from deeplab import DeepLab
from fst import Fst
from ndn_server.server import Server
from storage import RocksdbStorage


def main():
    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    root_path = os.path.dirname(sys.argv[0])
    if len(sys.argv) >= 2:
        node_address = sys.argv[1]
    else:
        node_address = "localhost"

    if len(sys.argv) >= 3:
        node_port = int(sys.argv[2])
    else:
        node_port = 6363

    storage = RocksdbStorage(os.path.join(root_path, DATABASE_NAME))
    deeplab_inst = DeepLab(range(1), root_path, IMG_MEAN, storage)
    fst_inst = Fst(range(1), root_path, IMG_SHAPE, storage)
    server = Server(deeplab_inst, fst_inst, root_path, storage, node_address, node_port)

    try:
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        deeplab_inst.join_all()
        fst_inst.join_all()
        deeplab_inst.shutdown()
        fst_inst.shutdown()

if __name__ == "__main__":
    main()
