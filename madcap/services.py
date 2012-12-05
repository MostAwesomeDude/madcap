from twisted.python import log

class MadcapServices(object):
    """
    Services.

    This services client runs as part of a factory's processing, rather than
    standalone.
    """

    state = "NORMAL"

    def __init__(self, factory):
        self.factory = factory

    def sendLine(self, line):
        pass

    def build_inf(self):
        return "SERV NIServices"

    def chat(self, sender, message):
        log.msg("SERV %s" % message)
