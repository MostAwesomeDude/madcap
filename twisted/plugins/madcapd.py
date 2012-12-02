from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.usage import Options
from twisted.application.strports import service

from madcap import MadcapFactory

class MadcapOptions(Options):
    pass

class MadcapServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "madcap"
    description = "An ADC server"
    options = MadcapOptions

    def makeService(self, options):
        return service("tcp:3231", MadcapFactory())

msm = MadcapServiceMaker()
