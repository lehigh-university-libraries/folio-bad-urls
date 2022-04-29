import requests
import json

from folioclient.FolioClient import FolioClient as OriginalFolioClient

class FolioClient(OriginalFolioClient):
    """ Extending original library to add POST support. """

    def folio_post(self, path, key=None, data=""):
        """Fetches data from FOLIO and turns it into a json object"""
        url = self.okapi_url + path
        print("POSTing to FOLIO: " + url)
        req = requests.post(url, headers=self.okapi_headers, data=json.dumps(data))
        if req.status_code == 200:
            return json.loads(req.text)[key] if key else json.loads(req.text)
        elif req.status_code == 422:
            raise Exception(f"HTTP {req.status_code}\n{req.text}")
        elif req.status_code in [500, 413]:
            raise Exception(f"HTTP {req.status_code}\n{req.text} ")
        else:
            raise Exception(f"HTTP {req.status_code}\n{req.text}")

