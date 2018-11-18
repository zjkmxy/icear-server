#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
from deeplab import DeepLab, DeepLabRequest
from fst import Fst, FstRequest


def main():
    root_path = os.path.dirname(sys.argv[0])

    deeplab_inst = DeepLab(range(1), root_path)
    img_shape = (236, 420, 3)
    fst_inst = Fst(range(1), root_path, img_shape)

    deeplab_inst.send(DeepLabRequest("example01", "img.jpg", "deeplab.png"))
    assert(fst_inst.send(FstRequest("example01", "la_muse", "img.jpg", "la_muse.png")))
    assert(fst_inst.send(FstRequest("example02", "rain_princess", "img.jpg", "rain_princess.png")))
    deeplab_inst.send(DeepLabRequest("example02", "img.jpg", "deeplab.png"))

    deeplab_inst.join_all()
    fst_inst.join_all()
    deeplab_inst.shutdown()
    fst_inst.shutdown()


if __name__ == "__main__":
    main()
