class ElectronicRecord:
    """ A record with a URL. """

    instance_hrid = None
    url = None

    def __repr__(self):
        return str(self.__dict__)

class TestResult:
    """ The result of testing a URL from a record. """ 

    def __init__(self, instance_hrid, url, status_code, permanent_redirect=None,
        parser_result=None):

        self.instance_hrid = instance_hrid
        self.url = url
        self.status_code = status_code
        self.permanent_redirect = permanent_redirect
        self._parser_result = parser_result

    def is_bad_url(self):
        return self.status_code != 200

    def parser_result(self):
        return self._parser_result

    def __repr__(self):
        return str(self.__dict__)

class LocalStatusCode:
    CONNECTION_FAILED               = 0
    ROBOTS_TXT_BLOCKS_URL           = -10
    ROBOTS_TXT_TIMEOUT_EXCESSIVE    = -11

class ParserResult:
    """ The result of string scanning of a URL from a record. """

    def __init__(self, *, insecure_url, no_proxy_prefix, wrong_proxy_prefix):
        self._insecure_url = insecure_url
        self._no_proxy_prefix = no_proxy_prefix
        self._wrong_proxy_prefix = wrong_proxy_prefix

    def is_insecure_url(self):
        return self._insecure_url

    def has_no_proxy_prefix(self):
        return self._no_proxy_prefix

    def has_wrong_proxy_prefix(self):
        return self._wrong_proxy_prefix
