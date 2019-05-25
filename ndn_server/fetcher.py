from typing import Callable
from config import *
from .ndnasync import *
from pyndn import Face, Name, Interest, Blob
from pyndn.security import KeyChain
from storage import IStorage
from pycnl.generalized_object import ContentMetaInfo
import logging


async def fetch_gobject(face: Face,
                        prefix: Name,
                        on_success: Callable[[Name, ContentMetaInfo, Blob], None],
                        on_failure: Callable[[Name], None],
                        semaphore: asyncio.Semaphore):
    async def retry_or_fail():
        nonlocal interest
        result = None
        # retry for up to FETCHER_MAX_ATTEMPT_NUMBER times
        for _ in range(FETCHER_MAX_ATTEMPT_NUMBER):
            # express interest
            async with semaphore:
                response = await WaitForResponse(face, interest).run()
            if response.data is not None:
                # if succeeded, jump out
                result = response.data
                break
            else:
                # if failed, wait for next time
                # This will lead to an additional delay but okay
                await asyncio.sleep(FETCHER_RETRY_INTERVAL / 1000.0)
        return result

    # fetch and decode meta info
    interest = Interest(Name(prefix).append("_meta"))
    data_packet = await retry_or_fail()
    if data_packet is None:
        on_failure(prefix)
        return
    meta_info = ContentMetaInfo()
    try:
        meta_info.wireDecode(data_packet.content)
    except ValueError:
        on_failure(prefix)
        return
    # fetch and attach data
    data = bytes("", "utf-8")
    final_id = FETCHER_FINAL_BLOCK_ID
    cur_id = 0
    while cur_id <= final_id:
        interest = Interest(Name(prefix).appendSegment(cur_id))
        data_packet = await retry_or_fail()
        if data_packet is None:
            on_failure(prefix)
            return
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
    def __init__(self,
                 keychain: KeyChain,
                 on_payload: Callable[[Name], None],
                 storage: IStorage,
                 on_failure: Callable[[Name], None]):
        self.face = None
        self.keychain = keychain
        self.on_payload = on_payload
        self.on_failure_callback = on_failure
        self.storage = storage
        self.semaphore = asyncio.Semaphore(FETCHER_MAX_INTEREST_IN_FLIGHT)
        self.task_list = []

    def network_start(self, face: Face) -> None:
        # Due to network's change, we have a different face
        self.face = face
        self.semaphore = asyncio.Semaphore(FETCHER_MAX_INTEREST_IN_FLIGHT)
        self.task_list = []

    def network_stop(self):
        # Maybe we can remove pending interests here.
        for task in self.task_list:
            task.cancel()
        self.task_list = []

    def fetch_data(self, name: Name) -> None:
        event_loop = asyncio.get_event_loop()
        task = event_loop.create_task(fetch_gobject(self.face, name,
                                                    self.on_generalized_obj, self.on_failure, self.semaphore))

        logging.info("Fetching task created: %s", task.__repr__())

        self.task_list.append(task)

    def on_generalized_obj(self, name: Name, meta_info: ContentMetaInfo, obj: Blob) -> None:
        self.storage.put(Name(name).append("_meta"), meta_info.wireEncode().toBytes())
        self.storage.put(name, obj.toBytes())
        self.on_payload(name)

    def on_failure(self, name: Name) -> None:
        if self.on_failure_callback:
            self.on_failure_callback(name)
