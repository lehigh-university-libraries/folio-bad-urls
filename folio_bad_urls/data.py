class ElectronicRecord:
    state: str
    hasExternalIds: bool
    suppressDiscovery: bool
    url: str
    control_number: str|None

    def __repr__(self):
        return str(self.__dict__)
