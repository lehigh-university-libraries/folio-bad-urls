class ElectronicRecord:
    state: str
    hasExternalIds: bool
    suppressDiscovery: bool
    url: str
    control_number: str|None

    def __repr__(self):
        return str(self.__dict__)

class TestResult:
    url: str
    status_code: int

    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code

    def is_bad_url(self):
        return self.status_code != 200
