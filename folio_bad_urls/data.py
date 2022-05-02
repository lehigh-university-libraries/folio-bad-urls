class ElectronicRecord:
    """ A record with a URL. """

    instance_hrid = None
    url = None

    def __repr__(self):
        return str(self.__dict__)

class TestResult:
    """ The result of testing a URL from a record. """ 

    def __init__(self, instance_hrid, url, status_code):
        self.instance_hrid = instance_hrid
        self.url = url
        self.status_code = status_code

    def is_bad_url(self):
        return self.status_code != 200

    def __repr__(self):
        return str(self.__dict__)

class LocalStatusCode:
    CONNECTION_FAILED               = 0
    ROBOTS_TXT_BLOCKS_URL           = -10
    ROBOTS_TXT_TIMEOUT_EXCESSIVE    = -11
