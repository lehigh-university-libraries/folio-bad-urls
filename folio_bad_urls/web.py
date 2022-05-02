import requests
import logging
import time
from urllib.parse import urlparse

from folio_bad_urls.data import ElectronicRecord, TestResult

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class WebTester:
    """ Test URLs for their response status code. """

    HEADERS = {
        "user-agent": "folio-bad-urls/0.1"
    }

    def __init__(self, config):
        self._config = config
        log.addHandler(self._config.log_file_handler)

        self._CRAWL_DELAY = float(self._config.get('WebTester', 'crawl_delay'))
        self._REQUEST_TIMEOUT = float(self._config.get('WebTester', 'request_timeout'))

        self._last_query_time = dict()

    def test_record(self, record: ElectronicRecord):
        url = record.url
        self._pause_if_needed(url)
        try :
            response = requests.get(url, timeout = self._REQUEST_TIMEOUT, headers = WebTester.HEADERS)
            status_code = int(response.status_code)
            log.debug(f"Got status code {status_code} for url {url}")
            return TestResult(record.instance_hrid, url, status_code)
        except requests.exceptions.Timeout:
            log.debug(f"Request timed out for url {url}")
            return TestResult(record.instance_hrid, url, 0)
        except requests.exceptions.RequestException as e:
            log.warn(f"Caught unexpected RequestException with url {url}: {e}")
            return TestResult(record.instance_hrid, url, 0)

    def _pause_if_needed(self, url):
        base_url = self._parse_base_url(url)
        if base_url in self._last_query_time:
            server_last_query_time = self._last_query_time[base_url]
            elapsed = time.time() - server_last_query_time
            log.debug(f"new query to {base_url} after {elapsed}")
            wait_time = self._CRAWL_DELAY - elapsed
            if wait_time > 0:
                log.debug(f"waiting {wait_time:.1f} seconds before next url")
                time.sleep(wait_time)
        self._last_query_time[base_url] = time.time()

    def _parse_base_url(self, url):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        log.debug(f"base url: {base_url}")
        return base_url
