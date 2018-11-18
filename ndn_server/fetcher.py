from pyndn import Face, Name, Interest, Data
from pyndn.security import KeyChain
import os.path


class Fetcher:
    def __init__(self, keychain, on_payload, upload_path):
        # type: (KeyChain, function, str) -> None
        self.face = None
        self.keychain = keychain
        self.on_payload = on_payload
        self.upload_path = upload_path

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
            interest = Interest(name)
            interest.setCanBePrefix(False)
            self.face.expressInterest(interest, self.on_data)

    def on_data(self, _, data):
        # type: (Interest, Data) -> None
        # TODO: segmentation
        # Save data to file
        file_path = os.path.join(self.upload_path, data.name.toUri()[1:])
        os.makedirs(file_path, exist_ok=True)
        with open(os.path.join(file_path, "img.jpg"), "wb") as f:
            f.write(data.content.toBytes())
        self.on_payload(data)
