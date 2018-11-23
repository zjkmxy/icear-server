import time
from pyndn import Face, Name, Interest, InterestFilter, Data, Blob
from pyndn.security import KeyChain
from pyndn.encoding import ProtobufTlv
from deeplab import DeepLab, DeepLabRequest
from fst import Fst, FstRequest
import logging
from .fetcher import Fetcher
from .messages.request_msg_pb2 import OpComponent, SegmentParameterMessage
import os
from copy import copy

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
    def __init__(self, deeplab_manager, fst_manager, root_path):
        # type: (DeepLab, Fst, str) -> None
        self.face = None
        self.keychain = KeyChain()
        self.running = False
        self._restart = False

        self.deeplab_manager = deeplab_manager
        self.fst_manager = fst_manager
        deeplab_manager.on_finished = self.on_process_finished
        fst_manager.on_finished = self.on_process_finished

        self.upload_path = os.path.join(root_path, "upload")
        self.fetcher = Fetcher(self.keychain, self.on_payload, self.upload_path)
        self.results_path = os.path.join(root_path, "results")

        self.command_filter_id = 0
        self.result_filter_id = 0

        # Status set, one item per frame
        self.status_set = {}

    def run(self):
        self.running = True
        while self.running:
            self.face = Face()
            self.face.setCommandSigningInfo(self.keychain, self.keychain.getDefaultCertificateName())
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
        # TODO: On Command
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

    def on_result_interest(self, prefix, interest, face, interest_filter_id, filter_obj):
        # type: (Name, Interest, Face, int, InterestFilter) -> None
        prefix_len = Name(SERVER_PREFIX).append(RESULT_PREFIX).size()
        data_name = interest.name[prefix_len:]
        print("On result", data_name.toUri())
        key, stat = self._result_set_prefix_match(data_name)
        if key is None:
            self.negative_reply(NACK_NO_REQUEST)
            return
        # Note: as no knowledge about the namespace, use files' name.
        result_file = os.path.join(self.results_path, data_name.toUri()[1:])
        if os.path.exists(result_file):
            # TODO: segmentation
            with open(result_file, "rb") as f:
                data = Data(interest.name)
                data.content = Blob(bytearray(f.read()))
                self.face.putData(data)
            return
        # TODO: Check the status
        self.negative_reply(NACK_RETRY_AFTER, stat.estimated_time)


    def negative_reply(self, code, retry_after=0):
        # TODO: Reply with Application NACK
        print("Negative reply", code)

    def _result_set_prefix_match(self, data_name):
        for key, value in self.status_set.items():
            if key.isPrefixOf(data_name):
                return key, value
        return None, None

    def on_payload(self, data):
        # type: (Data) -> None
        for op in self.status_set[data.name].operations.components:
            model_name = op.model.decode("utf-8")
            # TODO: Use an on-server database, but not to repeat calculation
            if model_name == "deeplab":
                ret = self.deeplab_manager.send(DeepLabRequest(data.name.toUri()[1:],
                                                               "img.jpg",
                                                               "deeplab.png"))
            else:
                ret = self.fst_manager.send(FstRequest(data.name.toUri()[1:],
                                                       model_name,
                                                       "img.jpg",
                                                       model_name + ".png"))
            op.flags = FLAG_PROCESSING if ret else FLAG_FAILED

    def on_process_finished(self, name_str, model_name):
        name = Name(name_str)
        for op in self.status_set[name].operations.components:
            if model_name != op.model.decode("utf-8"):
                continue
            op.flags = FLAG_SUCCEEDED
            break
