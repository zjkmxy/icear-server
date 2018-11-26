import time
from pyndn import Face, Name, Interest, InterestFilter, Data, Blob, MetaInfo
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from deeplab import DeepLab, DeepLabRequest
from fst import Fst, FstRequest
import logging
from .fetcher import Fetcher
from .messages.request_msg_pb2 import OpComponent, SegmentParameterMessage
from copy import copy
from storage import Storage
from pycnl import Namespace
from pycnl.generalized_object import ContentMetaInfo
from pyndn.util.common import Common

DISCONN_RETRY_TIME = 2.0
SERVER_PREFIX = "icear-server"
COMMAND_PREFIX = "calc"
RESULT_PREFIX = "result"

# No such request for specified frame
NACK_NO_REQUEST = 404
# Not processed yet
NACK_RETRY_AFTER = 300
# Operation succeeded but the name is not a file name
NACK_RETRY_WITH_FILE_NAME = 301
# Operation failed
NACK_EXECUTION_FAILED = 405
# Can not fetch specified frame
# RESERVED
# Operation not supported
NACK_NOT_SUPPORTED = 401


# No flag
FLAG_NONE = 0
# No input data in the network
# TODO: Fix this dirty way
FLAG_NO_INPUT = 1
FLAG_FETCHING = 2
FLAG_PROCESSING = 4
FLAG_FAILED = 8
FLAG_SUCCEEDED = 16


class Status:
    def __init__(self, operations, start_time, estimated_time):
        # type: (OpComponent, float, float)->None
        self.operations = operations
        self.start_time = start_time
        self.estimated_time = estimated_time
        self.end_time = 0.0


class Server:
    def __init__(self, deeplab_manager, fst_manager, root_path, storage):
        # type: (DeepLab, Fst, str, Storage) -> None
        self.face = None
        self.keychain = KeyChain()
        # self.namespace = Namespace(Name(SERVER_PREFIX).append(RESULT_PREFIX), self.keychain)
        # self.namespace.addOnObjectNeeded(self.on_result_interest)
        self.segment_size = Face.getMaxNdnPacketSize() // 2

        self.running = False
        self._restart = False

        self.deeplab_manager = deeplab_manager
        self.fst_manager = fst_manager
        self.storage = storage
        deeplab_manager.on_finished = self.on_process_finished
        fst_manager.on_finished = self.on_process_finished

        self.fetcher = Fetcher(self.keychain, self.on_payload, self.storage)

        self.command_filter_id = 0
        self.result_filter_id = 0

        # Status set, one item per frame
        # TODO: Put status into storage
        self.status_set = {}

    def run(self):
        self.running = True
        while self.running:
            self.face = Face()
            self._restart = False
            try:
                self._network_start()
                print("Starting...")
                while self.running and not self._restart:
                    self.face.processEvents()
                    time.sleep(0.01)
            except ConnectionRefusedError:
                pass
            finally:
                self.face.shutdown()
                self._network_stop()
            if self.running:
                time.sleep(DISCONN_RETRY_TIME)

    def stop(self):
        self.running = False

    def _network_start(self):
        self.face.setCommandSigningInfo(self.keychain, self.keychain.getDefaultCertificateName())
        # self.namespace.setFace(self.face, lambda prefix: print("Register failed for"))

        self.face.registerPrefix(Name(SERVER_PREFIX), None, self.on_register_failed)
        self.command_filter_id = self.face.setInterestFilter(
            Name(SERVER_PREFIX).append(COMMAND_PREFIX), self.on_command)
        self.result_filter_id = self.face.setInterestFilter(
            Name(SERVER_PREFIX).append(RESULT_PREFIX), self.on_result_interest)
        self.fetcher.network_start(self.face)

    def _network_stop(self):
        self.fetcher.network_stop()
        self.face.unsetInterestFilter(self.result_filter_id)
        self.face.unsetInterestFilter(self.command_filter_id)

    def on_register_failed(self, prefix):
        # type: (Name) -> None
        logging.warning("Register failed for prefix", prefix.toUri())
        self._restart = True

    def on_command(self, _prefix, interest, _face, _interest_filter_id, _filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> None
        parameter_msg = SegmentParameterMessage()
        ProtobufTlv.decode(parameter_msg, interest.name[-1].getValue())
        parameter = parameter_msg.segment_parameter
        prefix = Name()
        for compo in parameter.name.component:
            prefix.append(compo.decode("utf-8"))
        # TODO: Check operations
        for frame_id in range(parameter.start_frame, parameter.end_frame + 1):
            frame_name = Name(prefix).append(str(frame_id))
            self.status_set[frame_name] = Status(copy(parameter.operations), 0, 0)
        # TODO: Server should check whether data is here, not fetcher
        self.fetcher.fetch_data(prefix, parameter.start_frame, parameter.end_frame)
        # TODO: Response with succeed code

    # def on_result_interest(self, _namespace, needed_obj, _id):
    #     # type: (Namespace, Namespace, int) -> bool
    def on_result_interest(self, _prefix, interest, face, _interest_filter_id, _filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> bool
        prefix = Name(SERVER_PREFIX).append(RESULT_PREFIX)
        if not prefix.isPrefixOf(interest.name):
            return False
        data_name = interest.name[prefix.size():]
        print("On result", data_name.toUri())
        key, stat = self._result_set_prefix_match(data_name)
        if key is None:
            self.negative_reply(NACK_NO_REQUEST)
            return True

        if data_name[-1].isSegment():
            seg_no = data_name[-1].toSegment()
            result = self.storage.get(data_name.getPrefix(-1))
        elif data_name[-1] == Name("_meta")[0]:
            seg_no = -1
            result = self.storage.get(data_name.getPrefix(-1))
        else:
            seg_no = None
            result = self.storage.get(data_name)

        if result is not None:
            segment_cnt = (len(result) + self.segment_size - 1) // self.segment_size
            # TODO: I don't understand why namespace keep all data in memory
            metainfo = MetaInfo()
            # metainfo.setFinalBlockId(segment_cnt - 1) # WHY this doesn't work?
            metainfo.setFinalBlockId(Name().appendSegment(segment_cnt - 1)[0])
            if segment_cnt > 1 and seg_no is None:
                seg_no = 0
                data_name.appendSequenceNumber(seg_no)

            data = Data(Name(prefix).append(data_name))
            data.setMetaInfo(metainfo)
            if seg_no == -1:
                # _meta
                # TODO: Shouldn't produce meta here.
                contentMetaInfo = ContentMetaInfo()
                contentMetaInfo.setContentType("png")
                contentMetaInfo.setTimestamp(Common.getNowMilliseconds())
                contentMetaInfo.setHasSegments(True)
                data.content = contentMetaInfo.wireEncode()
            else:
                # data
                if seg_no < segment_cnt:
                    if segment_cnt > 1:
                        start_offset = seg_no * self.segment_size
                        end_offset = start_offset + self.segment_size
                        data.content = Blob(bytearray(result[start_offset:end_offset]))
                    else:
                        data.content = Blob(bytearray(result))
                else:
                    data.content = None
            self.keychain.sign(data)
            face.putData(data)
            return True
        # TODO: Check the status
        print("Not exists", data_name)
        self.negative_reply(NACK_RETRY_AFTER, stat.estimated_time)


    def negative_reply(self, code, retry_after=0):
        # TODO: Reply with Application NACK
        print("Negative reply", code)

    def _result_set_prefix_match(self, data_name):
        for key, value in self.status_set.items():
            if key.isPrefixOf(data_name):
                return key, value
        return None, None

    def on_payload(self, data_name):
        # type: (Name) -> None
        for op in self.status_set[data_name].operations.components:
            model_name = op.model.decode("utf-8")
            result_name = Name(data_name).append(model_name)
            if self.storage.exists(result_name):
                print("Result exists:" + result_name.toUri())
                continue
            print("Ready to produce:" + result_name.toUri())
            if model_name == "deeplab":
                ret = self.deeplab_manager.send(DeepLabRequest(data_name.toUri()[1:],
                                                               data_name.toUri(),
                                                               result_name))
            else:
                ret = self.fst_manager.send(FstRequest(data_name.toUri()[1:],
                                                       model_name,
                                                       data_name.toUri(),
                                                       result_name))
            op.flags = FLAG_PROCESSING if ret else FLAG_FAILED

    def on_process_finished(self, name_str, model_name):
        name = Name(name_str)
        print("Process finished:", name_str)
        for op in self.status_set[name].operations.components:
            if model_name != op.model.decode("utf-8"):
                continue
            # TODO: Currently cannot rely on this flag in onInterest();
            # We need to put states into storage
            op.flags = FLAG_SUCCEEDED
            break
