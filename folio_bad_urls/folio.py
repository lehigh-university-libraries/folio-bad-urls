import logging
from folioclient.FolioClient import FolioClient

from data import ElectronicRecord

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Folio:
    """ Get SRS records via the FOLIO API. """

    def __init__(self, config):
        self._config = config
        log.addHandler(self._config.log_file_handler)
        self.connection = self._init_connection()

        self._query_limit = self._config.get("Folio", "query_limit")

    def _init_connection(self):
        log.debug("Connecting to FOLIO")
        self.client = FolioClient(
            okapi_url = self._config.get('Folio', 'okapi_url'),
            tenant_id = self._config.get('Folio', 'tenant_id'),
            username = self._config.get('Folio', 'username'),
            password = self._config.get('Folio', 'password')
        )

    def load_electronic_records(self, offset):
        log.debug("Getting electronic SRS records")
        srs_records = self._get_srs_records(offset)
        records = [record for record in
            [self._parse_record(srs_record) for srs_record in srs_records]
            if record is not None]
        return records
        
    def get_total_records(self):
        srs_records_empty = self._api_query_srs_records(0, 0)
        return int(srs_records_empty['totalRecords'])

    def _get_srs_records(self, offset, limit = None):
        if not limit:
            limit = self._query_limit

        result = self._api_query_srs_records(offset, limit)
        srs_records = result['records']
        return srs_records

    def _api_query_srs_records(self, offset, limit = None):
        path = "/source-storage/records"
        params = f'?state=ACTUAL&offset={offset}&limit={limit}'
        return self.client.folio_get(path, query = params)

    def _parse_record(self, srs_record):
        record = ElectronicRecord()
        record.state = srs_record['state']
        record.hasExternalIds = len(srs_record['externalIdsHolder']) > 0
        record.suppressDiscovery = srs_record['additionalInfo']['suppressDiscovery']

        fields = srs_record['parsedRecord']['content']['fields']
        found_856 = False
        for field in fields:
            # if '245' in field:
            #     log.debug(f"found 245: {field['245']}")
            if '856' in field:
                field_856 = field['856']
                found_856 = True
                # log.debug(f"found 856: {field_856}")
                record.control_number = None # default
                subfields = field_856['subfields']
                for subfield in subfields:
                    if 'u' in subfield:
                        record.url = subfield['u']
                        # log.debug(f'... found URL: {record.url}')
                    if 'w' in subfield:
                        record.control_number = subfield['w']
        if found_856:
            return record
        else:
            return None
