import asyncio
from pyndn import Face, Interest, Data, NetworkNack


class WaitForResponse:
    def __init__(self, face: Face, interest: Interest):
        self.done = asyncio.Event()
        self.face = face
        self.interest = interest
        self.data = None
        self.nack = None
        self.timeout = False

    def on_data(self, _interest, data: Data):
        self.data = data
        self.done.set()

    def on_timeout(self, _interest):
        self.timeout = True
        self.done.set()

    def on_network_nack(self, _interest, network_nack: NetworkNack):
        self.nack = network_nack
        self.done.set()

    async def run(self):
        self.face.expressInterest(self.interest, self.on_data, self.on_timeout, self.on_network_nack)
        await self.done.wait()
        return self
