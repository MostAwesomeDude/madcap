from base64 import b32decode, b32encode
import random
import time

import tiger

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python import log

from madcap.services import MadcapServices

def b32d(s):
    """
    Decode a base32 string, repairing padding if necessary.
    """

    if len(s) % 8:
        s = s.ljust((len(s) // 8 + 1) * 8, "=")
    return b32decode(s)

def b32e(s):
    """
    Encode a base32 string, stripping padding.
    """

    return b32encode(s).rstrip("=")

def rand32(length):
    """
    Return a random base32 string of a given length.
    """

    xs = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return "".join(random.choice(xs) for chaff in range(length))

def new_sid():
    """
    Generate a new SID.
    """

    return rand32(4)

def hash_password(password, nonce):
    return b32e(tiger.new(password + b32d(nonce)).digest())

def split_line(line):
    """
    Break a line into its components.
    """

    where = line[0]
    what = line[1:4]
    return where, what, line[5:]

def join_features(fs):
    return " ".join("AD%s" % f for f in fs)

def inf_dict(data):
    d = {}
    for field in data.split()[1:]:
        k = field[:2]
        v = field[2:]
        d[k] = v
    return d

def escape(s):
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace(" ", "\\s")

def unescape(s):
    return s.replace("\\s", " ").replace("\\n", "\n").replace("\\\\", "\\")


class MadcapProtocol(LineOnlyReceiver):
    """
    A protocol that can communicate to ADC clients.
    """

    delimiter = "\n"

    state = "PROTOCOL"

    # List of features which we support.
    _our_features = (
        # TIGR must be first because it indicates not only that TTHs are
        # allowed on this hub, but also that Tiger is the preferred hashing
        # algorithm. While most clients default to Tiger anyway, making this
        # explicit is a good thing.
        "TIGR",
        # Base protocol support.
        "BASE",
        # File lists may be compressed with bzip2.
        "BZIP",
        # We send INFs to clients when they join.
        "PING",
    )

    def __init__(self, factory, addr):
        self.factory = factory
        self.addr = addr

        self.features = set()
        self.inf = {}

        # Pick a SID. Loop to make sure that we only assign unique SIDs.
        sid = new_sid()
        while sid in self.factory.clients:
            sid = new_sid()

        self.sid = sid

    def connectionMade(self):
        self.factory.clients[self.sid] = self

    def connectionLost(self, reason):
        del self.factory.clients[self.sid]

    def sendLine(self, line):
        """
        Log sent lines.
        """

        log.msg("%s < %r" % (self.sid, line))
        LineOnlyReceiver.sendLine(self, line)

    def lineReceived(self, line):
        # Some clients occasionally send bare newlines as a form of keepalive.
        # Discard them immediately without logging; this is not a problem but
        # there is nothing that needs to be done.
        if not line:
            return

        log.msg("%s > %r" % (self.sid, line))

        try:
            where, what, rest = split_line(line)
        except IndexError:
            log.msg("! Bad line %r" % line)
            return

        # Dispatch and update our internal state first.
        attr = getattr(self, "handle_%s" % what, None)
        if attr is None:
            log.msg("! Can't handle %s" % what)
        else:
            attr(rest)

        if where == "B":
            # Rebroadcast to everybody, as long as this client's acutally
            # authenticated.
            if self.state != "NORMAL":
                return

            if what == "INF":
                # INF needs to be rebuilt.
                inf = self.build_inf()
                self.factory.broadcast("INF", inf)
            elif what == "MSG":
                # It's chat; broadcast it using the chat interface.
                sender, message = rest.split(" ", 1)
                self.factory.chat(sender, unescape(message))
            else:
                self.factory.broadcast(what, rest)
        elif where == "D":
            # Send to just one specific SID.
            sender, receiver, chaff = rest.split(" ", 2)
            self.factory.direct(receiver, what, rest)
        elif where == "E":
            # Send it to a specific SID, and also echo it back to the sender.
            sender, receiver, chaff = rest.split(" ", 2)
            self.factory.direct(receiver, what, rest)
            self.sendLine(line)

    def status(self, code, reason, *flags):
        """
        Set the status code.
        """

        log.msg("%% Status: %s (%d) %r" % (reason, code, flags))
        if flags:
            status = "ISTA %d %s %s" % (code, " ".join(flags), escape(reason))
        else:
            status = "ISTA %d %s" % (code, escape(reason))
        self.sendLine(status)

    def kick(self, reason):
        """
        Disconnect this client.
        """

        log.msg("Kicking %s: %s" % (self.sid, reason))

        message = "%s MS%s" % (self.sid, escape(reason))
        self.factory.broadcast("QUI", message)
        self.transport.loseConnection()

    def chat(self, sender, message):
        """
        Send a message.
        """

        msg = "BMSG %s %s" % (sender, escape(message))
        self.sendLine(msg)

    def send_sid(self):
        msg = "ISID %s" % self.sid
        self.sendLine(msg)

    def build_inf(self):
        """
        Build an INF for us.
        """

        d = self.inf.copy()

        # Hubs should never leak PIDs.
        if "PD" in d:
            del d["PD"]

        data = " ".join("%s%s" % t for t in d.items())

        return "%s %s" % (self.sid, data)

    def handle_STA(self, data):
        code, description = data.split(" ", 1)
        log.msg("%% STA %% %r" % (code, unescape(description)))

    def handle_SUP(self, data):
        if self.state not in ("PROTOCOL", "NORMAL"):
            self.status(44, "Invalid state", "FCHSUP")
            return

        for flag in data.split(" "):
            feature = flag[2:]
            if flag.startswith("RM"):
                self.features.discard(feature)
            elif flag.startswith("AD"):
                self.features.add(feature)

        if "BASE" not in self.features:
            self.status(45, "Missing required feature", "FCBASE")
            return

        if "TIGR" not in self.features:
            self.status(45, "Missing required feature", "FCTIGR")
            return

        # If in PROTOCOL, reply with SUP, assign and send a SID, and switch to
        # the IDENTIFY state.
        if self.state == "PROTOCOL":
            sup = "ISUP %s" % join_features(self._our_features)
            self.sendLine(sup)
            self.send_sid()
            uptime = int(time.time() - self.factory.started)
            inf = "IINF CT32 UP%d" % uptime
            self.sendLine(inf)

            self.state = "IDENTIFY"

    def handle_INF(self, data):
        if self.state not in ("IDENTIFY", "NORMAL"):
            self.status(44, "Invalid state", "FCBINF")
            return

        self.inf = inf_dict(data)

        # Verify that tiger(PID) == CID.
        if "ID" in self.inf and "PD" in self.inf:
            hashed = b32d(self.inf["ID"])
            unhashed = b32d(self.inf["PD"])
            if tiger.new(unhashed).digest() != hashed:
                self.status(27, "PID does not match CID")
                return

        # If the IP address was not provided, or if it was blank, write down
        # their actual connecting IP.
        if "I4" not in self.inf or self.inf["I4"] == "0.0.0.0":
            self.inf["I4"] = self.addr.host

        # If we weren't identified before, transition to VERIFY and ask for a
        # password.
        if self.state == "IDENTIFY":
            self.state = "VERIFY"

            self.nonce = rand32(16)
            gpa = "IGPA %s" % self.nonce
            self.sendLine(gpa)

    def handle_MSG(self, data):
        sid, msg = data.split(" ", 1)

        if "NI" in self.inf:
            sid = self.inf["NI"]

        log.msg("%% <%s> %r" % (sid, unescape(msg)))

    def handle_SCH(self, data):
        # XXX
        pass

    def handle_CTM(self, data):
        pass

    def handle_RCM(self, data):
        pass

    def handle_PAS(self, data):
        if self.state != "VERIFY":
            self.status(44, "Invalid state", "FCIPAS")
            return

        # XXX go look up an actual password
        password = "madcap"

        if hash_password(password, self.nonce) != data:
            self.status(23, "Incorrect password")
            return

        # Okay, you're in.
        self.state = "NORMAL"

        # Send this client's info to everybody else.
        self.factory.broadcast("INF", self.build_inf())

        # Send out our current client list.
        for client in self.factory.clients.values():
            if client.state == "NORMAL" and client is not self:
                self.sendLine("BINF %s" % client.build_inf())

    def handle_QUI(self, data):
        log.msg("%% %s quit: %r" % (self.sid, unescape(data)))
        self.transport.loseConnection()


class MadcapFactory(Factory):
    """
    A factory that manages ADC clients.
    """

    protocol = MadcapProtocol

    def __init__(self):
        self.clients = {
            "SERV": MadcapServices(self),
        }

    def startFactory(self):
        self.started = time.time()

    def buildProtocol(self, addr):
        log.msg("Accepting connection from %r" % addr)
        p = MadcapProtocol(self, addr)
        return p

    def broadcast(self, what, message):
        """
        Send a message to all connected clients.
        """

        line = "B%s %s" % (what, message)

        for client in self.clients.values():
            if client.state == "NORMAL":
                client.sendLine(line)

    def direct(self, sid, what, message):
        """
        Send a message directly to a single client.
        """

        line = "D%s %s" % (what, message)

        if sid in self.clients:
            self.clients[sid].sendLine(line)
        else:
            log.msg("! No SID %s for direct message" % sid)

    def chat(self, sender, message):
        """
        Broadcast a chat message to all connected clients.
        """

        for client in self.clients.values():
            if client.state == "NORMAL":
                client.chat(sender, message)
