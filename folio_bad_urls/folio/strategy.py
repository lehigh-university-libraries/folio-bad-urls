from abc import ABC, abstractmethod

class Strategy(ABC):
    """ A method of seraching folio for records linking to electronic resources. """

    def __init__(self, folio):
        self.folio = folio

    @abstractmethod    
    def get_total_records(self):
        pass

    @abstractmethod
    def load_electronic_records(self, offset):
        pass
