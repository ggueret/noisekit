class Mixer(object):
    def __init__(self, control="Master", id=0, cardindex=-1, device="default"):
        self.control = control
        self.id = id
        self.cardindex = cardindex
        self.device = device

    def setvolume(self, value):
        pass
