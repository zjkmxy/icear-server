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
    face = Face()
    keychain = KeyChain()
    face.setCommandSigningInfo(keychain, keychain.getDefaultCertificateName())
    running = True

    interest = Interest("/icear-server/calc")
    param_msg = SegmentParameterMessage()
    param_msg.segment_parameter.name.component.append(bytes("example-data", "utf-8"))
    param_msg.segment_parameter.start_frame = 2
    param_msg.segment_parameter.end_frame = 3
    op = param_msg.segment_parameter.operations.components.add()
    op.model = bytes("deeplab", "utf-8")
    op.flags = 0
    op = param_msg.segment_parameter.operations.components.add()
    op.model = bytes("la_muse", "utf-8")
    op.flags = 0
    interest.name.append(ProtobufTlv.encode(param_msg))

    def on_data(_, data):
        # type: (Interest, Data) -> None
        # This won't hit
        print(data.name.toUri())
        print(data.content.toBytes())

    face.expressInterest(interest, on_data)

    while running:
        face.processEvents()
        time.sleep(0.01)

    face.shutdown()

if __name__ == "__main__":
    main()
