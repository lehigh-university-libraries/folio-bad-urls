import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

HEADER = "instance_hrid, url, status_code\n"

class Reporter:
    """ Save bad URLs to a file. """

    def __init__(self, config):
        self._config = config
        log.addHandler(self._config.log_file_handler)

    def write_results(self, offset, results):
        filename = f'result_{str(offset)}.csv'
        bad_urls = 0
        with open(filename, 'w') as file:
            file.write(HEADER)
            for result in results:
                if result.is_bad_url():
                    bad_urls += 1
                    result_line = self._format_result(result)
                    file.write(result_line)
        log.info(f"Wrote file with {bad_urls} bad URLs.")
        return bad_urls

    def _format_result(self, result):
        return f"{result.instance_hrid}, {result.url}, {result.status_code}\n"
