#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time

root_path = os.path.join(os.path.dirname(sys.argv[0]), "..")
sys.path.append(root_path)

from pyndn import Name, Data, Blob, Face, MetaInfo
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from pyndn.util.common import Common
from pycnl import Namespace
from pycnl.generalized_object import ContentMetaInfo


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else str(element)) + " "
    print(result)

def main():
    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Create an in-memory key chain with default keys.
    keyChain = KeyChain()
    face.setCommandSigningInfo(keyChain, keyChain.getDefaultCertificateName())

    streamNamespace = Namespace(Name("/example-data"), keyChain)

    dump("Register prefix", streamNamespace.name)
    # Set the face and register to receive Interests.
    streamNamespace.setFace(face,
      lambda prefixName: dump("Register failed for prefix", prefixName))

    # /example-data/2~3
    for sequenceNumber in range(2, 4):
        sequenceNamespace = streamNamespace[str(sequenceNumber)]
        dump("Preparing data for", sequenceNamespace.name)

        # Prepare the _meta packet.
        contentMetaInfo = ContentMetaInfo()
        contentMetaInfo.setContentType("jpeg")
        contentMetaInfo.setTimestamp(Common.getNowMilliseconds())
        contentMetaInfo.setHasSegments(True)
        sequenceNamespace["_meta"].serializeObject(contentMetaInfo.wireEncode())

        # Read jpeg file
        img_path = os.path.join(root_path, "sample420x236.jpg")
        with open(img_path, "rb") as f:
            data = f.read()
        segment_size = face.getMaxNdnPacketSize() // 2
        segment_cnt = (len(data) + segment_size - 1) // segment_size

        # We know the content has two segments.
        metaInfo = MetaInfo()
        metaInfo.setFinalBlockId(Name().appendSegment(segment_cnt - 1)[0])
        sequenceNamespace.setNewDataMetaInfo(metaInfo)
        for i in range(segment_cnt):
            start_offset = i * segment_size
            end_offset = start_offset + segment_size
            sequenceNamespace[Name.Component.fromSegment(i)].serializeObject(
                Blob(bytearray(data[start_offset:end_offset])))

    while True:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

main()
