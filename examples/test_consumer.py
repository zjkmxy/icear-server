#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time

root_path = os.path.join(os.path.dirname(sys.argv[0]), "..")
sys.path.append(root_path)

from pyndn import Name, Data, Blob, Face, MetaInfo
from pyndn.security import KeyChain, SafeBag
from pyndn.encoding import ProtobufTlv
from pyndn.util.common import Common
from pycnl import Namespace
from pycnl.generalized_object import GeneralizedObjectHandler
from PIL import Image
import io

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

def main():
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    prefix = Name("/icear-server/result/example-data/2/deeplab")
    prefixNamespace = Namespace(prefix)
    prefixNamespace.setFace(face)

    enabled = [True]
    img = [None]
    def onGeneralizedObject(contentMetaInfo, obj):
        data = obj.toBytes()
        dump("Got generalized object, content-type",
             contentMetaInfo.getContentType(), ":", repr(data))
        print(len(data))
        enabled[0] = False
        img[0] = data

    goh = GeneralizedObjectHandler(onGeneralizedObject)
    prefixNamespace.setHandler(goh).objectNeeded()

    # Loop calling processEvents until a callback sets enabled[0] = False.
    while enabled[0]:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    image = Image.open(io.BytesIO(img[0]))
    image.show()
main()
