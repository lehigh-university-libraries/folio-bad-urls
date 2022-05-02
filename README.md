# Folio Bad URLs

Report on Bad URLs in FOLIO records with electronic access links.  The application utilizes the FOLIO APIs to load a set of records and test their URLs for any [HTTP response status code](#status-codes) other than 200 OK.  It generates a .csv file report.

## Dependencies

The tool requires Python 3.x+.

### Install from PIP
  - requests

### Additional Dependencies
- [FOLIO-FSE/FolioClient (python wrapper for FOLIO API)](https://github.com/FOLIO-FSE/FolioClient)

## Configuration

Copy/rename `example.properties` and configure its parameters.

### Folio Section

For connecting to and using the FOLIO APIs.  All properties are **required**.

| Property | Description | Required |
|----------|-------------|---------|
| okapi_url | OKAPI URL of the FOLIO server | Y |
| tenant_id | FOLIO Tenant ID | Y |
| username | FOLIO username | Y | 
| password | FOLIO password | Y |
| strategy | Name of the strategy to use.  See [Folio Stratgy](#folio-strategy) below. | Y |
| query_limit | Number of records requested in each FOLIO API call.  Note: for SrsInstanceIdsStrategy, this must be approximately 30 or lower so that the maximum query string length is not exceeded. | Y |
| batch_limit | Number of records tested for each output file.  Must be equal to or a multiple of query_limit.  The actual file will contain only those records which had bad URLs. | Y |

### WebTester Section

For testing each URL.

| Property | Description | Required |
|----------|-------------|---------|
| default_crawl_delay | In seconds.  Requests to the same host will be spaced to be at least this far apart, to avoid triggering rate limits.  A higher crawl delay specified in robots.txt is respected. | Y |
| max_crawl_delay | In seconds, must be greater or equal to default_crawl_delay.  If robots.txt specifies a crawl delay higher than this value, the request will be skipped and reported as a failure with an [identifying status code](#status-codes).  | Y |
| request_timeout | In seconds.  Maximum timeout used for connecting to URLs. | Y |
| allow_list | Comma-separated list of strings.  If present, only URLs including one of these strings will be tested. | N |
| block_list | Comma-separated list of strings.  If present, URLs that include one of these strings will be skipped.  `block_list` is ignored if `allow_list` is present. | N |

### Logging Section

| Property | Description | Required |
|----------|-------------|---------|
| log_file | Log filename | Y |

## How to Run

### Basic Operation

python3 ./folio_bad_urls/main.py --config=CONFIG_FILE

### Command Line Arguments

    usage: main.py [-h] -c, CONFIG_FILE [-s START_OFFSET] [-e END_OFFSET]

    Report on URLs in 856 fields.

    optional arguments:
      -h, --help            show this help message and exit
      -c, CONFIG_FILE, --config CONFIG_FILE
                            Path to the properties file
      -s START_OFFSET, --start-offset START_OFFSET
                            Starting offset (inclusive) for the FOLIO query.
                            Default is 0.
      -e END_OFFSET, --end-offset END_OFFSET
                            Ending offset (exclusive) for the FOLIO query. Default
                            is no ending, retrieve all records.

## Reporter File Format

The .csv file output by the application has the following columns:
- FOLIO Instance HRID
- URL
- [Status Code](#status-codes)
- [Permanent Redirect](#permanent-redirect)

### Status Codes

For successful server connections, this value is the [HTTP response status code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) returned by the server.

Note that successful requests (with status code 200) are not be reported to the CSV.

The following codes are reported for special circumstances:

| Status Code | Description |
| ----------- | ----------- |
| 0 | Could not connect to the server within the configured `request_timeout` period. |
| -10 | Robots.txt blocks fetching this URL. |
| -11 | Robots.txt specifies a crawl delay greater than the configured `max_crawl_delay` period. |

### Permanent Redirect

If a request includes one or more permanent (301) redirects, this field reports the destination URL of the final permanent redirect.
A permanent redirect generally indicates that the URL should generally be changed in the source (FOLIO) data.

## Folio Strategy

Two algorithms are available to load the records with URLs to test.  The configuration file must specify the name of a strategy to use.

Neither strategy works great, so suggestions are welcome.

### SrsStrategy

Strategy "SrsStrategy" uses the `/source-storage/records` API with limit and offset, filtered only on `state=ACTUAL`.  After retrieval, results are tested for the following and passed to WebTester only if *all* are true:
- contains an 856$u
- does not contain a 856$x
- is not marked `suppressDiscovery` = true
- contains a linked `instanceHrid`

#### Considerations

This strategy requires only a single API call for each batch of records.  However it must iterate through every (`ACTUAL`) SRS record, most of which may not have electronic access links at all. 

### SrsInstanceIdsStrategy

Strategy "SrsInstanceIdsStrategy" first uses the `/source-storage/stream/marc-record-identifiers` API twice: first to query for instance IDS with an 856$u, and then for those with an 856$w.  The difference of those two sets (instance IDs found in the first list, not found in the second) is saved.  This list can be reused on multiple executions of the application if the record sets have not changed (much) in between.  

Iterating in batches over this list, the `/inventory/instance` API is queried on `state=ACTUAL` and a batch of those instance IDs to return FOLIO instance records.  Any record that is not marked `discoverySuppress` is tested by WebTester.

#### Considerations

This strategy requires multiple FOLIO APIs, and the instances query must be repeated constantly due to the limit on how many UUIDs can fit into an HTTP GET query.  However the net result tests out 20% faster than SrsStrategy in initial profiling.
