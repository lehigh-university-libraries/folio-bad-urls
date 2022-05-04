import logging

from folio_bad_urls.data import ParserResult

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)

class UrlParser:
    """ Parse URLs for lexical result information. """

    def __init__(self, config):
        self._PROXY_PREFIX = config.get('UrlParser', 'proxy_prefix', fallback=None)
        self._PROXY_PREFIX_COMMON_PART = config.get('UrlParser', 'proxy_prefix_common_part', fallback="?url=")
        self._PROXY_REPORT_NO_PREFIX = bool(config.get('UrlParser', 'proxy_report_no_prefix', fallback=False))
        self._PROXY_REPORT_WRONG_PREFIX = bool(config.get('UrlParser', 'proxy_report_wrong_prefix', fallback=False))
 
        # validate config
        if self._PROXY_REPORT_NO_PREFIX and not self._PROXY_PREFIX:
            raise Exception("Parameter proxy_prefix required for proxy_report_no_prefix")
        if self._PROXY_REPORT_WRONG_PREFIX and not self._PROXY_PREFIX:
            raise Exception("Parameter proxy_prefix required for proxy_report_wrong_prefix")

    def parse(self, url):
        parser_result = ParserResult(
            insecure_url=self._test_insecure_url(url),
            no_proxy_prefix=self._test_no_proxy_prefix(url),
            wrong_proxy_prefix=self._test_wrong_proxy_prefix(url)
            )
        return parser_result

    def _test_insecure_url(self, url):
        return not url.startswith("https:")

    def _test_no_proxy_prefix(self, url):
        if not self._PROXY_REPORT_NO_PREFIX:
            return None
        return not url.startswith(self._PROXY_PREFIX)

    def _test_wrong_proxy_prefix(self, url):
        if not self._PROXY_REPORT_WRONG_PREFIX:
            return None
        return self._PROXY_PREFIX_COMMON_PART in url \
            and not url.startswith(self._PROXY_PREFIX)
