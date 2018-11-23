#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time

root_path = os.path.join(os.path.dirname(sys.argv[0]), "..")
sys.path.append(root_path)

from pyndn import Name, Data, Blob, Interest, Face, InterestFilter
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from ndn_server.messages.request_msg_pb2 import SegmentParameterMessage

def main():
    img_path = os.path.join(root_path, "sample420x236-down.jpg")

    face = Face()
    keychain = KeyChain()
    face.setCommandSigningInfo(keychain, keychain.getDefaultCertificateName())
    running = True

    print(face.getMaxNdnPacketSize())

    def on_interest(_prefix, interest, _face, _interest_filter_id, _filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> None
        print("On interest", interest.name.toUri())
        data = Data(Name(interest.name))
        with open(img_path, "rb") as f:
            data.content = Blob(bytearray(f.read()))
        face.putData(data)

    def on_failed(*_):
        print("Register failed")

    face.registerPrefix(Name("example-data"), on_interest, on_failed)
    # interest_filter = InterestFilter(Name("example-data"), "<[2-3]>")
    # face.setInterestFilter(interest_filter, on_interest)

    while running:
        face.processEvents()
        time.sleep(0.01)

    face.shutdown()


if __name__ == "__main__":
    main()
