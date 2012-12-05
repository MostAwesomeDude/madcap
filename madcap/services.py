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
        if sender == "SERV":
            # Don't go into loops. Ever.
            return

        if message == "!hi":
            self.factory.chat("SERV", "Hey!")
        elif message == "!clients":
            self.factory.chat("SERV", "Client listing:")
            for (sid, client) in self.factory.clients.items():
                if client is not self:
                    info = "* %s: %s" % (sid, client.inf["NI"])
                    self.factory.chat("SERV", info)
