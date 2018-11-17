#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
from deeplab import DeepLab, DeepLabRequest


def main():
    root_path = os.path.dirname(sys.argv[0])

    deeplab_inst = DeepLab(range(1), root_path)
    deeplab_inst.send(DeepLabRequest("example01", "img.jpg", "deeplab.png"))
    deeplab_inst.send(DeepLabRequest("example02", "img.jpg", "deeplab.png"))
    deeplab_inst.join_all()
    deeplab_inst.shutdown()


if __name__ == "__main__":
    main()
