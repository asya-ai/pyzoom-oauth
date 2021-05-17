########################################################################################################################
#  Author     -- Puupuls (https://puupuls.lv)
#  Repository -- https://github.com/Puupuls/pyzoom-oauth
#  License    -- GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007 (See LICENSE.md for more info)
########################################################################################################################
from __future__ import annotations
import base64
import os
import re
from datetime import datetime
from typing import List
import requests


class RecordingFile:
    """
        Class that contains recording file info
    """
    id: str
    meeting_id: str
    recording_start: datetime
    recording_end: datetime
    file_type: str
    file_extension: str
    file_size: int
    play_url: str
    download_url: str
    status: str
    zoom_instance: Zoom
    recording_type: str

    def from_json(self, js: dict, zoom_instance: Zoom) -> RecordingFile:
        """
        Fill class info from json
        :param js: js object, received from api
        :type js: dict
        :param zoom_instance: Zoom class instance that has this recording file
        :type zoom_instance: Zoom
        :return: RecordingFile class instance
        """
        self.id = js['id']
        self.meeting_id = js['meeting_id']
        self.recording_start = datetime.strptime(js['recording_start'], '%Y-%m-%dT%H:%M:%SZ')
        self.recording_end = datetime.strptime(js['recording_end'], '%Y-%m-%dT%H:%M:%SZ')
        self.file_type = js['file_type']
        self.file_extension = js['file_extension']
        self.file_size = js['file_size']
        self.play_url = js['play_url']
        self.download_url = js['download_url']
        self.status = js['status']
        self.recording_type = js['recording_type']
        self.zoom_instance = zoom_instance

        return self

    def save(self, path: str, verbose: bool = True) -> None:
        """
        Download this file
        :param path: file directory path
        :type path: str
        :param verbose: whether or not print info when download starts or ends
        :type verbose: bool
        :return: None
        """
        if not path.endswith(self.file_extension.lower()):
            path += f".{self.file_extension.lower()}"

        os.makedirs('/'.join(path.split('/')[:-1]), exist_ok=True)
        if verbose:
            print(f"Starting download of {path}")
        with requests.get(self.download_url + f"?access_token={self.zoom_instance.access_token}", stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        if verbose:
            print(f"Download of {path} finished")


class Recording:
    uuid: str
    id: int
    account_id: str
    host_id: str
    topic: str
    type: int
    start_time: datetime
    timezone: str
    duration: int
    total_size: int
    recording_count: int
    share_url: str
    zoom_instance: Zoom
    recording_files: List[RecordingFile]

    def from_json(self, js: dict, zoom_instance: Zoom) -> Recording:
        """
        Fill class info from json
        :param js: js object, received from api
        :type js: dict
        :param zoom_instance: Zoom class instance that has this recording
        :type zoom_instance: Zoom
        :return: Recording class instance
        """
        self.uuid = js['uuid']
        self.id = js['id']
        self.account_id = js['account_id']
        self.host_id = js['host_id']
        self.topic = js['topic']
        self.type = js['type']
        self.start_time = datetime.strptime(js['start_time'], '%Y-%m-%dT%H:%M:%SZ')
        self.timezone = js['timezone']
        self.duration = js['duration']
        self.total_size = js['total_size']
        self.recording_count = js['recording_count']
        self.share_url = js['share_url']
        self.recording_files = []
        self.zoom_instance = zoom_instance
        for r in js['recording_files']:
            self.recording_files.append(RecordingFile().from_json(r, zoom_instance))

        return self

    def save(self, path: str, verbose: bool = True) -> None:
        """
        Download all files in this recording
        :param path: file directory path (each file will append extension)
        :type path: str
        :param verbose: whether or not print info when downloads start and end
        :type verbose: bool
        :return: None
        """
        os.makedirs('/'.join(path.split('/')[:-1]), exist_ok=True)
        for f in self.recording_files:
            f.save(path, verbose)


class Zoom:
    access_token: str = ''
    refresh_token: str = ''
    oauth_redirect_uri: str = ''
    client_id: str = ''
    client_secret: str = ''

    def __init__(self, client_id, client_secret, oauth_redirect_uri):
        """
        :param client_id: Client id from zoom app
        :type client_id: str
        :param client_secret: Client secret from zoom app
        :type client_secret: str
        :param oauth_redirect_uri: Redirect URL from zoom app
        :type oauth_redirect_uri: str
        """
        super().__init__()
        self.oauth_redirect_uri = oauth_redirect_uri
        self.client_id = client_id
        self.client_secret = client_secret

    def get_oauth_url(self) -> str:
        """
        Get OAuth url
        :return: string with URL
        """
        state = ''
        url = f"https://zoom.us/oauth/authorize?response_type=code&redirect_uri={self.oauth_redirect_uri}&client_id={self.client_id}&state={state}"
        return url

    def oauth_receiver(self, url: str) -> None:
        """
        Wrapper for receive_oauth_code
        :param url: url that OAuth redirect
        :return: None
        """
        code = re.search("code=(?P<code>[a-zA-Z0-9_]+)&?", url).group("code")
        return self.oauth_receiver_code(code)

    def oauth_receiver_code(self, code: str) -> None:
        """
        :param code: Code that is generated and given on redirect by OAuth
        :return: None
        """
        url = f"https://zoom.us/oauth/token?grant_type=authorization_code&code={code}&redirect_uri={self.oauth_redirect_uri}"

        headers = {
            'Authorization': f'Basic {self.make_verification()}'
        }

        response = requests.request("POST", url, headers=headers, data={})
        if response.status_code == 200:
            response_json = response.json()
            self.access_token = response_json['access_token']
            self.refresh_token = response_json['refresh_token']
        else:
            raise Exception("Failed to acquire tokens, response code is not 200")

    def refresh_access_token(self) -> Bool:
        """
        Refreshes access token
        :return: is_success
        """
        try:
            url = f"https://zoom.us/oauth/token?grant_type=refresh_token&refresh_token={self.refresh_token}"

            headers = {
                'Authorization': f'Basic {self.make_verification()}'
            }

            response = requests.request("POST", url, headers=headers, data={})
            if response.status_code == 200:
                response_json = response.json()
                self.access_token = response_json['access_token']
                self.refresh_token = response_json['refresh_token']
                return True
            else:
                raise Exception("Failed to refresh tokens, response code is not 200")
        except Exception as e:
            print(e)
            return False

    def get_recordings(self,
                       start_date: str = '2021-01-01',
                       end_date: str = '2050-01-01',
                       page_size: int = 300,
                       ) -> List[Recording]:
        """
        Retrieve list of recordings
        :param start_date: date in format 'YYYY-MM-DD'
        :type start_date: str
        :param end_date:  date in format 'YYYY-MM-DD'
        :type end_date: str
        :param page_size: max number of recordings to return
        :type page_size: int
        :return: List of recordings
        """
        recording_json = self.get_recordings_raw(start_date, end_date, page_size)
        recordings: List[Recording] = []
        if 'meetings' in recording_json:
            for m in recording_json['meetings']:
                recordings.append(Recording().from_json(m, zoom_instance=self))

        return recordings

    def get_recordings_raw(self,
                           start_date: str = '2021-01-01',
                           end_date: str = '2050-01-01',
                           page_size: int = 300,
                           ) -> dict:
        """
            Retrieve recordings from zoom, returns dict object
            :param start_date: date in format 'YYYY-MM-DD'
            :type start_date: str
            :param end_date:  date in format 'YYYY-MM-DD'
            :type end_date: str
            :param page_size: max number of recordings to return
            :type page_size: int
            :return: response dict
        """
        # Request list of recordings in last month
        url = f"https://api.zoom.us/v2/users/me/recordings?"
        if start_date:
            url += f"from={start_date}&"
        if end_date:
            url += f"from={end_date}&"
        if start_date:
            url += f"page_size={page_size}"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.request("GET", url, headers=headers, data={})
        response_json = response.json()
        if 'message' in response and 'Access token is expired' in response_json['message']:
            if self.refresh_access_token():
                return self.get_recordings_raw(start_date, end_date, page_size)
        return response_json

    def make_verification(self) -> str:
        """
        Create verification string for token acquisition
        :return: string
        """
        verification = f"{self.client_id}:{self.client_secret}"
        verification = verification.encode('ascii')
        verification = base64.b64encode(verification)
        return verification.decode('ascii')
