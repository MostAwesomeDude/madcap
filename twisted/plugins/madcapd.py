from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.usage import Options
from twisted.application.strports import service

from madcap.protocol import MadcapFactory

class MadcapOptions(Options):
    optParameters = [["port", "p", "tcp:420", "Endpoint to listen on"]]

class MadcapServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "madcap"
    description = "An ADC server"
    options = MadcapOptions

    def makeService(self, options):
        endpoint = options["port"]
        return service(endpoint, MadcapFactory())

msm = MadcapServiceMaker()
