import argparse
import configparser
import logging
from os.path import exists

from folio import Folio
from web import WebTester

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class FolioBadUrls:
    """ Report on Bad URLs in 856 fields. """

    def __init__(self, config_file):
        if not exists(config_file):
            raise FileNotFoundError(f"Cannot find config file: {config_file}")

        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self._init_log()
        log.info(f"Initialized with config file {config_file}")
        # Note: Config contains the FOLIO credentials.  Consider logging destinations.
        # print("Config: ", {section: dict(self.config[section]) for section in self.config.sections()})
        self.folio = Folio(self.config)
        self.web = WebTester(self.config)

    def _init_log(self):
        log_file = self.config.get("Logging", "log_file", fallback=None)
        if log_file:
            self.config.log_file_handler = logging.FileHandler(filename=log_file)  # type: ignore
            self.config.log_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))  # type: ignore
            log.addHandler(self.config.log_file_handler)  # type: ignore
        else:
            self.config.log_file_handler = logging.NullHandler()  # type: ignore

    def run(self):
        # TODO use some limit intelligently to allow restart after a point
        records = self.folio.load_electronic_records()
        print(f"Found {len(records)} electronic records.")
        for record in records:
            if self.within_scope(record):
                result = self.web.test_record(record)
                # log.debug(f"Result {result} for record: {record}")
        
    def within_scope(self, record):
        return True

def main():
    parser = argparse.ArgumentParser(description="Report on URLs in 856 fields.")
    parser.add_argument('-c,', '--config', dest='config_file', required=True, help='Path to the properties file')
    args = parser.parse_args()

    folio_bad_urls = FolioBadUrls(args.config_file)
    folio_bad_urls.run()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        log.exception("Caught exception.")
