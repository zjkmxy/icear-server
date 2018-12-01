#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time

root_path = os.path.join(os.path.dirname(sys.argv[0]), "..")
sys.path.append(root_path)

from pyndn import Name, Data, Blob, Interest, Face, InterestFilter, ContentType
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from ndn_server.messages.request_msg_pb2 import SegmentParameterMessage
from PIL import Image
import io


def main():
    face = Face()
    keychain = KeyChain()
    face.setCommandSigningInfo(keychain, keychain.getDefaultCertificateName())
    running = True
    img = None

    interest = Interest(Name("/icear-server/result/example-data/2/deeplab"))
    interest.mustBeFresh = True

    def on_data(_, data):
        # type: (Interest, Data) -> None
        nonlocal running, img
        print(data.name.toUri())
        print(data.content.toBytes())
        running = False
        if data.metaInfo.type == ContentType.NACK:
            print("NACK")
        else:
            img = data.content.toBytes()

    face.expressInterest(interest, on_data)

    while running:
        face.processEvents()
        time.sleep(0.01)

    face.shutdown()

    if img:
        image = Image.open(io.BytesIO(img))
        image.show()

if __name__ == "__main__":
    main()
