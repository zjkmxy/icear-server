from config import *
from pyndn.util.common import Common
from pyndn import Face, Name, Interest, Data, Blob
from pycnl.generalized_object import ContentMetaInfo


class AwaitReason:
    def run(self, generator):
        return next(generator)


Running = AwaitReason


class Finished(AwaitReason):
    def run(self, _generator):
        return self


class WaitForResponse(AwaitReason):
    def __init__(self, face, interest):
        self.stalled = True
        face.expressInterest(interest, self.on_data, self.on_timeout, self.on_network_nack)
        self.data = None
        self.nack = None
        self.timeout = False

    def on_data(self, _interest, data):
        self.stalled = False
        self.data = data

    def on_timeout(self, _interest):
        self.stalled = False
        self.timeout = True

    def on_network_nack(self, _interest, network_nack):
        self.stalled = False
        self.nack = network_nack

    def run(self, generator):
        if self.stalled:
            return self
        else:
            return generator.send(self)


class Delay(AwaitReason):
    def __init__(self, interval):
        self.interval = interval
        self.start_time = Common.getNowMilliseconds()

    def run(self, generator):
        now = Common.getNowMilliseconds()
        real_delay = now - self.start_time
        if real_delay <= self.interval:
            return self
        else:
            return generator.send(real_delay)


class Semaphore:
    class WaitForSemaphore(AwaitReason):
        def __init__(self, semaphore):
            self.semaphore = semaphore

        def run(self, generator):
            if self.semaphore.cur_cnt <= 0:
                return self
            else:
                self.semaphore.cur_cnt -= 1
                return generator.send(self.semaphore)

    def __init__(self, max_cnt=1, init_cnt=None):
        self.max_cnt = max_cnt
        self.cur_cnt = init_cnt
        if not isinstance(self.cur_cnt, int):
            self.cur_cnt = max_cnt

    def release(self):
        if self.cur_cnt < self.max_cnt:
            self.cur_cnt += 1

    def require(self):
        return Semaphore.WaitForSemaphore(self)

    def reset(self):
        self.cur_cnt = self.max_cnt

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class Task:
    def __init__(self, generator, reason):
        self.generator = generator
        self.reason = reason

    @staticmethod
    def run_one_round(task_list):
        for task in task_list:
            try:
                task.reason = task.reason.run(task.generator)
            except StopIteration:
                task.reason = Finished()
        return [task for task in task_list if not isinstance(task.reason, Finished)]

    @staticmethod
    def insert(task_list, generator):
        reason = next(generator)
        task_list.append(Task(generator, reason))


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
