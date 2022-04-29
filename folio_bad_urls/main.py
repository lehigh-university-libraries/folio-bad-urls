import argparse
import configparser
import logging
from os.path import exists

from folio_bad_urls.folio.main import Folio
from folio_bad_urls.data import ElectronicRecord
from folio_bad_urls.web import WebTester
from folio_bad_urls.reporter import Reporter

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class FolioBadUrls:
    """ Report on Bad URLs in 856 fields. """

    def __init__(self, config_file):
        if not exists(config_file):
            raise FileNotFoundError(f"Cannot find config file: {config_file}")

        self._config = configparser.ConfigParser()
        self._config.read(config_file)
        self._init_log()
        log.info(f"Initialized with config file {config_file}")
        # Note: Config contains the FOLIO credentials.  Consider logging destinations.
        # print("Config: ", {section: dict(self.config[section]) for section in self.config.sections()})
        self.folio = Folio(self._config)
        self.web = WebTester(self._config)
        self.reporter = Reporter(self._config)

    def _init_log(self):
        log_file = self._config.get("Logging", "log_file", fallback=None)
        if log_file:
            self._config.log_file_handler = logging.FileHandler(filename=log_file)  # type: ignore
            self._config.log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))  # type: ignore
            log.addHandler(self._config.log_file_handler)  # type: ignore
        else:
            self._config.log_file_handler = logging.NullHandler()  # type: ignore

    def run(self, start_offset, end_offset):
        BATCH_LIMIT = int(self._config.get('Folio', 'batch_limit'))
        offset = start_offset
        total_records = self.folio.get_total_records()
        log.info(f"Total records to check: {total_records}")
        while offset < total_records and offset < end_offset:
            results = self.run_batch(offset)
            self.reporter.write_results(offset, results)
            offset += BATCH_LIMIT

    def run_batch(self, offset):
        # TODO use some limit intelligently to allow restart after a point
        records = self.folio.load_electronic_records(offset)
        log.info(f"Batch {offset}: found {len(records)} electronic records matching criteria.")
        results = []
        for index, record in enumerate(records):
            if index % 10 == 0:
                log.debug(f"... at index {index} within query")
            result = self.web.test_record(record)
            log.debug(f"Result {result} for record: {record}")
            results.append(result)
        return results
        
def main():
    parser = argparse.ArgumentParser(description="Report on URLs in 856 fields.")
    parser.add_argument('-c,', '--config', dest='config_file', required=True, help='Path to the properties file')
    parser.add_argument('-s', '--start-offset', dest='start_offset', type=int, default=0, 
        help='Starting offset (inclusive) for the FOLIO query.  Default is 0.')
    parser.add_argument('-e', '--end-offset', dest='end_offset', type=int, default=None, 
        help='Ending offset (exclusive) for the FOLIO query.  Default is no ending, retrieve all records.')
    args = parser.parse_args()

    folio_bad_urls = FolioBadUrls(args.config_file)
    folio_bad_urls.run(args.start_offset, args.end_offset)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        log.exception("Caught exception.")
