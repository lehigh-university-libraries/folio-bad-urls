import logging

from folio_bad_urls.folio.strategy import Strategy
from folio_bad_urls.data import ElectronicRecord

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class SrsStrategy(Strategy):
    """ Discover records with electronic resource links via broadly querying SRS and then filtering locally. """ 

    def __init__(self, folio):
        super().__init__(folio)
        log.addHandler(folio._config.log_file_handler)

    def load_electronic_records(self, offset):
        log.debug("Getting electronic records via SRS records")
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
            limit = self.folio._query_limit

        result = self._api_query_srs_records(offset, limit)
        srs_records = result['records']
        return srs_records

    def _api_query_srs_records(self, offset, limit = None):
        path = "/source-storage/records"
        params = f'?state=ACTUAL&offset={offset}&limit={limit}'
        return self.folio.client.folio_get(path, query = params)

    def _parse_record(self, srs_record):
        if len(srs_record['externalIdsHolder']) == 0:
            return None
        elif srs_record['additionalInfo']['suppressDiscovery']:
            return None

        record = ElectronicRecord()
        record.instance_hrid = srs_record['externalIdsHolder']['instanceHrid']

        fields = srs_record['parsedRecord']['content']['fields']
        found_856 = False
        for field in fields:
            if '856' in field:
                field_856 = field['856']
                found_856 = True
                # log.debug(f"found 856: {field_856}")
                subfields = field_856['subfields']
                for subfield in subfields:
                    if 'u' in subfield:
                        record.url = subfield['u']
                        # log.debug(f'... found URL: {record.url}')
                    if 'w' in subfield:
                        return None

        if not found_856:
            return None
        else:
            return record
