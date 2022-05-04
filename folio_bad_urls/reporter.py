import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Reporter:
    """ Save bad URLs to a file. """

    STANDARD_HEADER_FIELDS = [ 
        "instance_hrid",
        "url", 
        "status_code", 
        "permanent_redirect",
        "insecure_url", 
    ]

    def __init__(self, config):
        self._config = config
        log.addHandler(self._config.log_file_handler)

        self._PROXY_REPORT_NO_PREFIX = bool(config.get('UrlParser', 'proxy_report_no_prefix', fallback=False))
        self._PROXY_REPORT_WRONG_PREFIX = bool(config.get('UrlParser', 'proxy_report_wrong_prefix', fallback=False))

    def write_results(self, offset, results):
        filename = f'result_{str(offset)}.csv'
        bad_urls = 0
        with open(filename, 'w') as file:
            file.write(self._format_header())
            for result in results:
                if result.is_bad_url():
                    bad_urls += 1
                    result_line = self._format_result(result)
                    file.write(result_line)
        log.info(f"Wrote file with {bad_urls} bad URLs.")
        return bad_urls

    def _format_header(self):
        header_fields = Reporter.STANDARD_HEADER_FIELDS
        if self._PROXY_REPORT_NO_PREFIX:
            header_fields.append("proxy_no_prefix")
        if self._PROXY_REPORT_WRONG_PREFIX:
            header_fields.append("proxy_wrong_prefix")
        return ", ".join(header_fields) + "\n"

    def _format_result(self, result):
        result_string = f"{result.instance_hrid}, \
            {result.url}, \
            {result.status_code}, \
            {result.permanent_redirect if result.permanent_redirect else ''}, \
            {self._format_bool(result.parser_result().is_insecure_url())} \
            "
        if self._PROXY_REPORT_NO_PREFIX:
            result_string += self._format_bool(result.parser_result().has_no_proxy_prefix())
        if self._PROXY_REPORT_WRONG_PREFIX:
            result_string += self._format_bool(result.parser_result().has_wrong_proxy_prefix())
        result_string += "\n"
        return result_string

    def _format_bool(self, value):
        return 'Y,' if value else ','
