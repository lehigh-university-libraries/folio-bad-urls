import logging

from folio_bad_urls.folio.client import FolioClient

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class Folio:
    """ Get ElectronicRecords via the FOLIO API. """

    def __init__(self, config, reuse_instance_ids):
        self._config = config
        log.addHandler(self._config.log_file_handler)
        self.connection = self._init_connection()

        strategy = self._config.get('Folio', 'strategy')
        if strategy == "SrsStrategy":
            from folio_bad_urls.folio.srs_strategy import SrsStrategy
            self._strategy = SrsStrategy(self)
        elif strategy == "SrsInstanceIdsStrategy":
            from folio_bad_urls.folio.srs_instance_ids_strategy import SrsInstanceIdsStrategy
            self._strategy = SrsInstanceIdsStrategy(self, reuse_instance_ids)
        else:
            raise Exception(f"Unknown strategy: {strategy}")

        self._query_limit = int(self._config.get("Folio", "query_limit"))
        self._batch_limit = int(self._config.get("Folio", "batch_limit"))

    def _init_connection(self):
        log.debug("Connecting to FOLIO")
        self.client = FolioClient(
            okapi_url = self._config.get('Folio', 'okapi_url'),
            tenant_id = self._config.get('Folio', 'tenant_id'),
            username = self._config.get('Folio', 'username'),
            password = self._config.get('Folio', 'password')
        )

    def get_total_records(self):
        return self._strategy.get_total_records()

    def load_electronic_records(self, offset):
        return self._strategy.load_electronic_records(offset)
