from config import *
import time
from pyndn import Face, Name, Interest, InterestFilter, Data, Blob, MetaInfo, ContentType
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from deeplab import DeepLab, DeepLabRequest
from fst import Fst, FstRequest
import logging
from .fetcher import Fetcher
from .messages.request_msg_pb2 import OpComponent, SegmentParameterMessage, ServerResponseMessage
from copy import copy
from storage import IStorage
from pycnl import Namespace
from pycnl.generalized_object import ContentMetaInfo
from pyndn.util.common import Common
import struct


# Request succeeded
RET_OK = 200
# Request exists, but not processed yet
RET_RETRY_AFTER = 100
# No such request for specified frame
RET_NO_REQUEST = 400
# Operation not supported
RET_NOT_SUPPORTED = 401
# Operation failed
RET_EXECUTION_FAILED = 402
# Can not fetch specified frame
RET_NO_INPUT = 403

# No flag
STATUS_NONE = 0
# No input data in the network
STATUS_NO_INPUT = 1
STATUS_FETCHING = 2
STATUS_PROCESSING = 3
STATUS_FAILED = 4
STATUS_SUCCEED = 5


class ResultStatus:
    """Status for a single frame per operation."""
    def __init__(self, prefix, operation, request_time, status=STATUS_NONE):
        self.prefix = prefix
        self.operation = operation
        self.request_time = request_time
        self.proecess_start_time = 0.0
        self.estimated_time = 0.0
        self.end_time = 0.0
        self.status = status

    def to_bytes(self):
        return struct.pack("ddddl256s64s",
                           self.request_time,
                           self.proecess_start_time,
                           self.estimated_time,
                           self.end_time,
                           self.status,
                           bytes(self.prefix, "utf-8"),
                           bytes(self.operation, "utf-8"))

    @staticmethod
    def from_bytes(buffer):
        values = struct.unpack("ddddl256s64s", buffer)
        ret = ResultStatus(values[5].decode("utf-8"), values[6].decode("utf-8"), values[0], values[4])
        ret.proecess_start_time = values[1]
        ret.estimated_time = values[2]
        ret.end_time = values[3]
        return ret


class Server:
    def __init__(self, deeplab_manager, fst_manager, root_path, storage):
        # type: (DeepLab, Fst, str, IStorage) -> None
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

        self.operations_set = self.fst_manager.get_models() | {"deeplab"}
        # Status set, one item per frame
        # TODO: Start with unfinished tasks
        # self.status_set = {}

    def save_status(self, name, status):
        # type: (Name, ResultStatus) -> None
        """Save status to database"""
        self.storage.put(Name(STATUS_PREFIX).append(name), status.to_bytes())

    def load_status(self, name):
        """Load status from database"""
        # Get exact prefix to data
        if name[-1] == Name.Component("_meta") or name[-1].isSegment():
            name = name[:-1]
        ret = self.storage.get(Name(STATUS_PREFIX).append(name))
        if ret is not None:
            return ResultStatus.from_bytes(ret)
        else:
            return None

    def run(self):
        self.running = True
        while self.running:
            self.face = Face()
            self._restart = False
            try:
                self._network_start()
                logging.info("Starting...")
                while self.running and not self._restart:
                    self.face.processEvents()
                    time.sleep(0.01)
            except ConnectionRefusedError:
                logging.warning("Connection refused. Retry in %ss.", DISCONN_RETRY_TIME)
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
        logging.error("Register failed for prefix: %s", prefix.toUri())
        self._restart = True

    def on_command(self, _prefix, interest, _face, _interest_filter_id, _filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> None
        parameter_msg = SegmentParameterMessage()
        ProtobufTlv.decode(parameter_msg, interest.name[-1].getValue())
        parameter = parameter_msg.segment_parameter
        prefix = Name()
        for compo in parameter.name.component:
            prefix.append(compo.decode("utf-8"))

        # Check operations
        for op in parameter.operations.components:
            model_name = op.model.decode("utf-8")
            if model_name not in self.operations_set:
                self.nodata_reply(interest.name, RET_NOT_SUPPORTED)
                return

        # Fetch frames
        for frame_id in range(parameter.start_frame, parameter.end_frame + 1):
            frame_name = Name(prefix).append(str(frame_id))
            for op in parameter.operations.components:
                model_name = op.model.decode("utf-8")
                data_name = Name(frame_name).append(model_name)
                logging.info("Request processed: %s", data_name)
                status = ResultStatus(prefix.toUri(), model_name, Common.getNowMilliseconds())
                status.status = STATUS_FETCHING
                status.estimated_time = status.proecess_start_time + 10.0
                self.save_status(data_name, status)
        # TODO: Server should check whether data is here, not fetcher
        self.fetcher.fetch_data(prefix, parameter.start_frame, parameter.end_frame)

        self.nodata_reply(interest.name, RET_OK, 10.0)

    # def on_result_interest(self, _namespace, needed_obj, _id):
    #     # type: (Namespace, Namespace, int) -> bool
    def on_result_interest(self, _prefix, interest, face, _interest_filter_id, _filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> bool
        prefix = Name(SERVER_PREFIX).append(RESULT_PREFIX)
        if not prefix.isPrefixOf(interest.name):
            # Wrong prefix
            return False

        data_name = interest.name[prefix.size():]
        logging.info("On result interest: %s", data_name.toUri())
        # key, stat = self._result_set_prefix_match(data_name)
        status = self.load_status(data_name)
        if status is None:
            # No such request
            self.nodata_reply(interest.name, RET_NO_REQUEST)
            return True

        if data_name[-1].isSegment():
            # Segment no suffix
            seg_no = data_name[-1].toSegment()
            result = self.storage.get(data_name.getPrefix(-1))
        elif data_name[-1] == Name("_meta")[0]:
            # MetaInfo suffix
            seg_no = -1
            result = self.storage.get(data_name.getPrefix(-1))
        else:
            # No suffix
            seg_no = None
            result = self.storage.get(data_name)

        if result is not None:
            # There are data
            segment_cnt = (len(result) + self.segment_size - 1) // self.segment_size
            # Note: I don't understand why namespace keep all data in memory
            metainfo = MetaInfo()
            # metainfo.setFinalBlockId(segment_cnt - 1) # WHY this doesn't work?
            metainfo.setFinalBlockId(Name().appendSegment(segment_cnt - 1)[0])
            if segment_cnt > 1 and seg_no is None:
                # Fetch segmented data with no suffix will get only first segment
                seg_no = 0
                data_name.appendSequenceNumber(seg_no)

            data = Data(Name(prefix).append(data_name))
            data.setMetaInfo(metainfo)
            if seg_no == -1:
                # _meta
                # TODO: I think we shouldn't produce meta here?
                content_metainfo = ContentMetaInfo()
                content_metainfo.setContentType("png")
                content_metainfo.setTimestamp(status.end_time)
                content_metainfo.setHasSegments(True)
                data.content = content_metainfo.wireEncode()
            else:
                # data
                if segment_cnt > 1:
                    # Segmented
                    if seg_no < segment_cnt:
                        start_offset = seg_no * self.segment_size
                        end_offset = start_offset + self.segment_size
                        data.content = Blob(bytearray(result[start_offset:end_offset]))
                    else:
                        data.content = None
                else:
                    # No segmentation
                    data.content = Blob(bytearray(result))

            self.keychain.sign(data)
            face.putData(data)
            return True
        else:
            # Data are not ready
            if status.status == STATUS_NO_INPUT:
                self.nodata_reply(interest.name, RET_NO_INPUT)
            if status.status == STATUS_FAILED:
                self.nodata_reply(interest.name, RET_EXECUTION_FAILED)
            else:
                self.nodata_reply(interest.name, RET_RETRY_AFTER, status.estimated_time - Common.getNowMilliseconds())
            return True

    def nodata_reply(self, name, code, retry_after=0.0):
        # type: (Name, int, float) -> None
        logging.info("Reply with code: %s", code)
        data = Data(name)
        metainfo = MetaInfo()
        msg = ServerResponseMessage()
        msg.server_response.ret_code = code

        if code != RET_OK:
            metainfo.type = ContentType.NACK
        else:
            metainfo.type = ContentType.BLOB
        if retry_after > 0.1:
            metainfo.freshnessPeriod = int(retry_after / 10)
            msg.server_response.retry_after = int(retry_after)
        else:
            metainfo.freshnessPeriod = 600

        data.setMetaInfo(metainfo)
        data.setContent(ProtobufTlv.encode(msg))

        self.keychain.sign(data)
        self.face.putData(data)

    def on_payload(self, frame_name):
        # type: (Name) -> None
        for model in self.operations_set:
            data_name = Name(frame_name).append(model)
            status = self.load_status(data_name)
            if status is None:
                continue
            if self.storage.exists(data_name):
                logging.info("Result exists: %s", data_name.toUri())
                continue
            logging.info("Ready to produce: %s", data_name.toUri())
            status.proecess_start_time = Common.getNowMilliseconds()

            if model == "deeplab":
                ret = self.deeplab_manager.send(DeepLabRequest(frame_name.toUri()[1:],
                                                               frame_name.toUri(),
                                                               data_name))
            else:
                ret = self.fst_manager.send(FstRequest(frame_name.toUri()[1:],
                                                       model,
                                                       frame_name.toUri(),
                                                       data_name))
            status.status = STATUS_PROCESSING if ret else STATUS_FAILED
            self.save_status(data_name, status)

    def on_process_finished(self, name_str, model_name):
        # type: (str, str) -> None
        data_name = Name(name_str).append(model_name)
        logging.info("Process finished: %s", data_name.toUri())
        status = self.load_status(data_name)
        if status is not None:
            status.end_time = Common.getNowMilliseconds()
            status.status = STATUS_SUCCEED

