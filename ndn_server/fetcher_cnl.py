from pyndn import Face, Name, Interest, Data, Blob
from pyndn.security import KeyChain
from storage import IStorage
from pycnl import Namespace
from pycnl.generalized_object import GeneralizedObjectHandler, ContentMetaInfo
from functools import partial
import logging


class Fetcher:
    """
    Fetch frames and store them into database.

    TO-DO:
    At least we need: congestion control, retransmission, on_nack, on_timeout
    Some are controlled by Namespace currently.
    But obviously pour all requests out is WRONG.

    NOTE:
    PyCNL is unstable now. I want to abandon this.
    """
    def __init__(self, keychain, on_payload, storage):
        # type: (KeyChain, function, IStorage) -> None
        self.face = None
        self.keychain = keychain
        self.on_payload = on_payload
        self.storage = storage

    def network_start(self, face):
        # type: (Face) -> None
        # Due to network's change, we have a different face
        self.face = face

    def network_stop(self):
        # Maybe we can remove pending interests here.
        pass

    def fetch_data(self, prefix, start_frame, end_frame):
        # type: (Name, int, int) -> None
        for frame_id in range(start_frame, end_frame + 1):
            name = Name(prefix).append(str(frame_id))

            # Feed server with existing data
            if self.storage.exists(name):
                self.on_payload(name)

            # Fetching new data
            logging.info("Fetching: %s", name.toUri())
            # TODO: Namespace will put everything into memory
            frame_namespace = Namespace(name)
            frame_namespace.setFace(self.face)
            frame_namespace.setHandler(GeneralizedObjectHandler(partial(self.on_generalized_obj, name))).objectNeeded()

    def on_data(self, _, data):
        # type: (Interest, Data) -> None
        # Currently not used
        logging.info("On frame data: %s", data.name)
        self.storage.put(data.name, data.content.toBytes())
        self.on_payload(data.name)

    def on_generalized_obj(self, name, _meta_info, obj):
        # type: (Name, ContentMetaInfo, Blob) -> None
        self.storage.put(name, obj.toBytes())
        self.on_payload(name)

    def process_tasks(self):
        pass
