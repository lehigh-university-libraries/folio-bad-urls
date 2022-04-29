import logging
import json
from os.path import exists

from folio_bad_urls.folio.strategy import Strategy
from folio_bad_urls.data import ElectronicRecord

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class SrsInstanceIdsStrategy(Strategy):

    def __init__(self, folio):
        super().__init__(folio)
        log.addHandler(folio._config.log_file_handler)
        self._load_instance_ids()

    def _load_instance_ids(self):
        # check file storage
        filename = f'instance_ids.json'
        if exists(filename):
            with open(filename) as file:
                ids = json.load(file)
                log.debug(f"loaded {len(ids)} ids")

        # else generate
        else:
            ids_with_856_u = self._get_ids_with_field('856', 'u')
            log.debug(f"{len(ids_with_856_u)} IDs with 856$u")
            ids_with_856_w = self._get_ids_with_field('856', 'w')
            log.debug(f"{len(ids_with_856_w)} IDs with 856$w")
            ids = set(ids_with_856_u) - set(ids_with_856_w)
            log.debug(f"filtered ids: {len(ids)}")

            with open(filename, 'w') as file:
                json.dump(list(ids), file)

        self._instance_ids = list(ids)

    def load_electronic_records(self, offset):
        log.debug("Getting electronic records via instance IDs")
        end_offset = offset + self.folio._batch_limit
        query_offset = offset
        batch_records = []
        while query_offset < end_offset:
            log.debug(f"... querying from offset {query_offset}")
            query_end_offset = query_offset + self.folio._query_limit
            instance_ids_query = self._instance_ids[query_offset : query_end_offset]
            instance_records = self._get_instance_records(instance_ids_query)
            records = [record for record in
                [self._parse_record(instance_record) for instance_record in instance_records]
                if record is not None]
            batch_records.extend(records)
            query_offset = query_end_offset
        return batch_records
        
    def _get_ids_with_field(self, field, subfield):
        response = self._api_query_ids_with_field(field, subfield)
        return response['records']

    def _api_query_ids_with_field(self, field, subfield):
        path = "/source-storage/stream/marc-record-identifiers"
        data = {"fieldsSearchExpression" : f"{field}.{subfield} is 'present'"}
        return self.folio.client.folio_post(path, data=data)

    def get_total_records(self):
        return len(self._instance_ids)

    def _get_instance_records(self, instance_ids):
        result = self._api_query_instance_records(instance_ids)
        instance_records = result['instances']
        return instance_records

    def _api_query_instance_records(self, instance_ids):
        path = "/inventory/instances"
        instance_ids = [f"\"{id}\"" for id in instance_ids]
        query_param = "id=" + "or id=".join(instance_ids)
        params = f'?state=ACTUAL&query=({query_param})'
        return self.folio.client.folio_get(path, query = params)

    def _parse_record(self, instance_record):
        if instance_record['discoverySuppress']:
            return None        

        record = ElectronicRecord()
        record.instance_hrid = instance_record['hrid']
        record.url = instance_record['electronicAccess'][0]['uri']
        return record
