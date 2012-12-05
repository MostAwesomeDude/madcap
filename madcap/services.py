class MadcapServices(object):
    """
    Services.

    This services client runs as part of a factory's processing, rather than
    standalone.
    """

    cid = "THISCIDISBOGUSANDSHOULDNOTBEUSEDBYYOUOK"
    state = "NORMAL"

    def __init__(self, factory):
        self.factory = factory

    def sendLine(self, line):
        pass

    def build_inf(self):
        return "SERV CT17 NIServices ID%s" % self.cid

    def chat(self, sender, message):
        if message == "!hi":
            self.factory.chat("SERV", "Hey!")
