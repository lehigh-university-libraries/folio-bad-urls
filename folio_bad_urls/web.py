import requests
import logging
import time
from urllib.parse import urlparse
import urllib.robotparser

from folio_bad_urls.data import ElectronicRecord, TestResult, LocalStatusCode
from folio_bad_urls.url_parser import UrlParser

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

        self._DEFAULT_CRAWL_DELAY = float(self._config.get('WebTester', 'default_crawl_delay'))
        self._MAX_CRAWL_DELAY = float(self._config.get('WebTester', 'max_crawl_delay'))
        self._REQUEST_TIMEOUT = float(self._config.get('WebTester', 'request_timeout'))

        self._parser = UrlParser(config)
        self._crawl_rules = dict()
        self._last_query_time = dict()
        self._init_filters()

    def _init_filters(self):
        self._allow_list = self._block_list = None

        allow_list_string = self._config.get('WebTester', 'allow_list', fallback=None)
        if allow_list_string:
            self._allow_list = [val.strip() for val in allow_list_string.split(',')]
            log.info(f"Using allow list: {self._allow_list}")

        if not self._allow_list:
            block_list_string = self._config.get('WebTester', 'block_list', fallback=None)
            if block_list_string:
                self._block_list = [val.strip() for val in block_list_string.split(',')]
                log.info(f"Using block list: {self._block_list}")

    def test_record(self, record: ElectronicRecord):
        url = record.url

        # check static URL parsing results
        parser_result = self._parser.parse(url)

        # check local filters
        if not self._check_filters(url):
            log.debug(f"Skipping URL due to filters: {url}")
            return None

        # check robots.text rules
        rules = self._check_crawl_rules(url)
        if not rules.can_fetch(url):
            log.warn(f"Robots.txt blocks URL: {url}")
            return TestResult(record.instance_hrid, url, LocalStatusCode.ROBOTS_TXT_BLOCKS_URL,
                parser_result=parser_result)
        pause_ok = self._pause_if_needed(url, rules)
        if not pause_ok:
            return TestResult(record.instance_hrid, url, LocalStatusCode.ROBOTS_TXT_TIMEOUT_EXCESSIVE,
                parser_result=parser_result)

        # load URL and check response
        try:
            response = requests.get(url, timeout = self._REQUEST_TIMEOUT, headers = WebTester.HEADERS)
            status_code = int(response.status_code)
            last_permanent_redirect = self._get_last_permanent_redirect(response, url)
            log.debug(f"Got status code {status_code} for url {url}")
            return TestResult(record.instance_hrid, url, status_code, permanent_redirect=last_permanent_redirect,
                parser_result=parser_result)
        except requests.exceptions.Timeout:
            log.debug(f"Request timed out for url {url}")
            return TestResult(record.instance_hrid, url, LocalStatusCode.CONNECTION_FAILED,
                parser_result=parser_result)
        except requests.exceptions.RequestException as e:
            log.warn(f"Caught unexpected RequestException with url {url}: {e}")
            return TestResult(record.instance_hrid, url, LocalStatusCode.CONNECTION_FAILED,
                parser_result=parser_result)

    def _check_filters(self, url):
        # check allow list
        if self._allow_list:
            for pattern in self._allow_list:
                if pattern in url:
                    return True
            return False

        # check block list
        elif self._block_list:
            for pattern in self._block_list:
                if pattern in url:
                    return False

        # allow URL if it's in neither list
        return True

    def _check_crawl_rules(self, url):
        base_url = self._parse_base_url(url)
        if base_url in self._crawl_rules:
            crawl_rules = self._crawl_rules[base_url]
        else:
            crawl_rules = CrawlRules(base_url)
            self._crawl_rules[base_url] = crawl_rules
        return crawl_rules

    def _pause_if_needed(self, url, crawl_rules):
        base_url = self._parse_base_url(url)
        if base_url in self._last_query_time:
            server_last_query_time = self._last_query_time[base_url]
            elapsed = time.time() - server_last_query_time
            log.debug(f"new query to {base_url} after {elapsed}")

            if crawl_rules.crawl_delay():
                crawl_delay = crawl_rules.crawl_delay()
                log.debug(f"URL {url} using robots.txt crawl delay: {crawl_delay}")
            else:
                crawl_delay = self._DEFAULT_CRAWL_DELAY

            wait_time = crawl_delay - elapsed
            if wait_time > self._MAX_CRAWL_DELAY:
                log.warn(f"Skipping URL {url} due to excessive wait time {wait_time}.")
                return False

            if wait_time > 0:
                log.debug(f"waiting {wait_time:.1f} seconds before next url")
                time.sleep(wait_time)
        self._last_query_time[base_url] = time.time()
        return True

    def _parse_base_url(self, url):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        return base_url

    def _get_last_permanent_redirect(self, response, request_url):
        permanent_redirects = [item for item in response.history if item.is_permanent_redirect]
        if len(permanent_redirects) == 0:
            return None
        elif permanent_redirects[-1].url.strip() != request_url.strip():
            return permanent_redirects[-1].url
        else:
            return None
            
class CrawlRules:
    """ Report on robots.txt rules for a base URL. """

    def __init__(self, base_url):
        self._base_url = base_url
        self._robot_parser = urllib.robotparser.RobotFileParser()
        self._robot_parser.set_url(base_url + "robots.txt")
        try:
            self._robot_parser.read()
            self._loaded_rules = True
        except: 
            log.warn(f"Could not retrieve robots.txt rules for url {base_url}")
            self._loaded_rules = False

    def can_fetch(self, url):
        if self._loaded_rules:
            return self._robot_parser.can_fetch("*", url)
        else:
            return True

    def crawl_delay(self):
        if self._loaded_rules:
            return self._robot_parser.crawl_delay("*")
        else:
            return None
