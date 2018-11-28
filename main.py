#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, logging
from deeplab import DeepLab
from fst import Fst
from ndn_server.server import Server
from storage import RocksdbStorage


DATABASE_NAME = "server_cache.db"
IMG_MEAN = (104.00698793, 116.66876762, 122.67891434)
IMG_SHAPE = (236, 420, 3)


def main():
    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    root_path = os.path.dirname(sys.argv[0])

    storage = RocksdbStorage(os.path.join(root_path, DATABASE_NAME))
    deeplab_inst = DeepLab(range(1), root_path, IMG_MEAN, storage)
    fst_inst = Fst(range(1), root_path, IMG_SHAPE, storage)
    server = Server(deeplab_inst, fst_inst, root_path, storage)

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
