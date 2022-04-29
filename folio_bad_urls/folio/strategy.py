from abc import ABC, abstractmethod

class Strategy(ABC):

    def __init__(self, folio):
        self.folio = folio

    @abstractmethod    
    def get_total_records(self):
        pass

    @abstractmethod
    def load_electronic_records(self, offset):
        pass
