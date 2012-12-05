from twisted.internet import reactor

from madcap.utilities import join_flags

class MadcapServices(object):
    """
    Services.

    This services client runs as part of a factory's processing, rather than
    standalone.
    """

    inf = {
        "CT": 17,
        "ID": "THISCIDISBOGUSANDSHOULDNOTBEUSEDBYYOUOK",
        "NI": "Services",
    }

    state = "NORMAL"

    def __init__(self, factory):
        self.factory = factory

    def sendLine(self, line):
        pass

    def build_inf(self):
        return "SERV %s" % join_flags(self.inf)

    def send_chat(self, message):
        def cb():
            for client in self.factory.clients.values():
                if client is not self:
                    client.chat("SERV", message)
        reactor.callLater(0, cb)

    def chat(self, sender, message):
        if sender == "SERV":
            # Don't go into loops. Ever.
            return

        if message == "!hi":
            self.send_chat("Hey!")
        elif message == "!clients":
            self.send_chat("Client listing:")
            for (sid, client) in self.factory.clients.items():
                if client is not self:
                    info = "* %s: %s" % (sid, client.inf["NI"])
                    self.send_chat(info)
