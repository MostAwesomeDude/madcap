import random

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python import log

def new_sid():
    """
    Generate a new SID.
    """

    xs = "ABCDEFHIJKLMNOPQRSTUVWXYZ23456789"
    return "".join(random.choice(xs) for chaff in range(4))

def split_line(line):
    """
    Break a line into its components.
    """

    where = line[0]
    what = line[1:4]
    return where, what, line[5:]


class MadcapProtocol(LineOnlyReceiver):
    """
    A protocol that can communicate to ADC clients.
    """

    delimiter = "\n"

    state = "PROTOCOL"

    def send_sid(self):
        # Loop, making sure that we only assign unique SIDs.
        sid = new_sid()
        while sid in self.factory.clients:
            sid = new_sid()

        self.sid = sid

        msg = "FSID %s" % sid
        self.sendLine(msg)

    def lineReceived(self, line):
        log.msg("%% %r" % line)
        where, what, rest = split_line(line)

        if where == "B":
            # Rebroadcast to everybody.
            for client in self.factory.clients.values():
                client.sendLine(line)
        elif where == "D":
            # Send to just one specific SID.
            target = line.split()[-1]
            if target in self.factory.clients:
                self.factory.clients[target].sendLine(line)
            self.sendLine(line)
        elif where == "E":
            self.sendLine(line)

        attr = getattr(self, "handle_%s" % what, None)
        if attr is None:
            log.msg("! Can't handle %s" % what)
        else:
            attr(rest)

    def handle_STA(self, data):
        code, description = data.split(" ", 1)
        log.msg("%% STA %% %r" % (code, description))

    def handle_SUP(self, data):
        if self.state not in ("PROTOCOL", "NORMAL"):
            # XXX kick?
            pass

        # XXX handle dynamic feature updates
        features = data.split(" ")
        self.features = features

        # If in PROTOCOL, reply with SUP, assign and send a SID, and switch to
        # the IDENTIFY state.
        if self.state == "PROTOCOL":
            # XXX reply with SUP
            self.send_sid()
            # XXX maybe send INF
            self.state = "IDENTIFY"

    def handle_INF(self, data):
        if self.state not in ("IDENTIFY", "NORMAL"):
            # XXX kick?
            pass

        # XXX should record all of these

    def handle_MSG(self, data):
        log.msg("%% <> %r" % data)

    def handle_SCH(self, data):
        # XXX
        pass

    def handle_PAS(self, data):
        # XXX
        pass


class MadcapFactory(Factory):
    """
    A factory that manages ADC clients.
    """

    protocol = MadcapProtocol

    def __init__(self):
        self.clients = {}

    def buildProtocol(self, addr):
        log.msg("Accepting connection from %r" % addr)
        p = Factory.buildProtocol(self, addr)
        p.factory = self
        return p
