from pyndn import Face, Name, Interest, Data, Blob
from pyndn.security import KeyChain
from storage import Storage
from pycnl import Namespace
from pycnl.generalized_object import GeneralizedObjectHandler, ContentMetaInfo
from functools import partial


class Fetcher:
    def __init__(self, keychain, on_payload, storage):
        # type: (KeyChain, function, Storage) -> None
        self.face = None
        self.keychain = keychain
        self.on_payload = on_payload
        self.storage = storage

    def network_start(self, face):
        # type: (Face) -> None
        # Due to network's change, we have a different face
        self.face = face

    def network_stop(self):
        # TODO: remove pending interests
        pass

    def fetch_data(self, prefix, start_frame, end_frame):
        # TODO: window, retransmission, on_nack, on_timeout, segmentation
        for frame_id in range(start_frame, end_frame + 1):
            name = Name(prefix).append(str(frame_id))
            print("Fetching", name.toUri())
            frame_namespace = Namespace(name)
            frame_namespace.setFace(self.face)
            frame_namespace.setHandler(GeneralizedObjectHandler(partial(self.on_generalized_obj, name))).objectNeeded()

    def on_data(self, _, data):
        # type: (Interest, Data) -> None
        # TODO: segmentation
        # Save data to file
        print("On data", data.name)
        # file_path = os.path.join(self.upload_path, data.name.toUri()[1:])
        # os.makedirs(file_path, exist_ok=True)
        # with open(os.path.join(file_path, "img.jpg"), "wb") as f:
        #     f.write(data.content.toBytes())
        self.storage.put(data.name, data.content.toBytes())
        self.on_payload(data.name)

    def on_generalized_obj(self, name, _meta_info, obj):
        # type: (Name, ContentMetaInfo, Blob) -> None
        self.storage.put(name, obj.toBytes())
        self.on_payload(name)
        pass
