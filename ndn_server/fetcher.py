from config import *
from .ndnasync import *
from pyndn import Face, Name, Interest, Data, Blob
from pyndn.security import KeyChain
from storage import IStorage
from pycnl.generalized_object import ContentMetaInfo
from pyndn.util.common import Common
import logging


def fetch_gobject(face, prefix, on_success, on_failure, semaphore):
    def retry_or_fail(interest):
        # use a nonlocal var for "return in generator"
        data_packet = None
        # retry for up to FETCHER_MAX_ATTEMPT_NUMBER times
        for _ in range(FETCHER_MAX_ATTEMPT_NUMBER):
            # express interest
            with (yield semaphore.require()):
                response = yield WaitForResponse(face, interest)
            if response.data is not None:
                # if succeeded, jump out
                data_packet = response.data
                break
            else:
                # if failed, wait for next time
                # This will lead to an additional delay but okay
                yield Delay(FETCHER_RETRY_INTERVAL)
        if data_packet is None:
            # if we used up all attempts, fail
            on_failure(prefix)
            yield Finished()
        return data_packet

    # fetch and decode meta info
    interest = Interest(Name(prefix).append("_meta"))
    data_packet = yield from retry_or_fail(interest)
    meta_info = ContentMetaInfo()
    try:
        meta_info.wireDecode(data_packet.content)
    except ValueError:
        on_failure(prefix)
        yield Finished()
    # fetch and attach data
    data = bytes("", "utf-8")
    final_id = FETCHER_FINAL_BLOCK_ID
    cur_id = 0
    while cur_id <= final_id:
        interest = Interest(Name(prefix).appendSegment(cur_id))
        data_packet = yield from retry_or_fail(interest)
        data += data_packet.content.toBytes()
        final_id_component = data_packet.metaInfo.getFinalBlockId()
        if final_id_component.isSegment():
            final_id = final_id_component.toSegment()
        cur_id += 1
    on_success(prefix, meta_info, Blob(data))


class Fetcher:
    """
    Fetch frames and store them into database.

    New design uses coroutines to simplify the implementation.
    """
    def __init__(self, keychain, on_payload, storage, on_failure):
        # type: (KeyChain, function, IStorage, function) -> None
        self.face = None
        self.keychain = keychain
        self.on_payload = on_payload
        self.on_failure_callback = on_failure
        self.storage = storage
        self.semaphore = Semaphore(FETCHER_MAX_INTEREST_IN_FLIGHT)
        self.task_list = []

    def process_tasks(self):
        self.task_list = Task.run_one_round(self.task_list)

    def network_start(self, face):
        # type: (Face) -> None
        # Due to network's change, we have a different face
        self.face = face
        self.semaphore.reset()
        self.task_list = []

    def network_stop(self):
        # Maybe we can remove pending interests here.
        self.task_list = []

    def fetch_data(self, name):
        Task.insert(self.task_list,
                    fetch_gobject(self.face, name, self.on_generalized_obj, self.on_failure, self.semaphore))

    def on_generalized_obj(self, name, meta_info, obj):
        # type: (Name, ContentMetaInfo, Blob) -> None
        self.storage.put(Name(name).append("_meta"), meta_info.wireEncode().toBytes())
        self.storage.put(name, obj.toBytes())
        self.on_payload(name)

    def on_failure(self, name):
        if self.on_failure_callback:
            self.on_failure_callback(name)
