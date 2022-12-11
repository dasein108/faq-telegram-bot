import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Any


class GoogleSheets(object):
    def __init__(self, spreadsheet_id, google_docs_creds_file_name):
        self.spreadsheetId = spreadsheet_id

        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            google_docs_creds_file_name,
            ['https://www.googleapis.com/auth/spreadsheets'])

        self.spreadsheets = self._get_spreadsheets()

    def _get_spreadsheets(self):
        http_auth = self.credentials.authorize(httplib2.Http())
        return apiclient.discovery.build('sheets', 'v4', http=http_auth, cache_discovery=False).spreadsheets()

    def get_sheet_names(self):
        return [s['properties']['title'] for s in
                self.spreadsheets.get(spreadsheetId=self.spreadsheetId).execute().get('sheets', [])]

    def get_sheet_rows(self, name: str):
        rows = self.spreadsheets.values().get(spreadsheetId=self.spreadsheetId, range=name).execute().get('values', [])
        return rows

    def add_sheet_rows(self, sheet_name: str, values: List[List[Any]]):
        body = {'values': values}

        result = self.spreadsheets.values().append(spreadsheetId=self.spreadsheetId, range=sheet_name,
                                                   valueInputOption='USER_ENTERED', body=body).execute()
        return result
