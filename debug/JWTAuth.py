#
# utility to handle the authenticion while using the Vantage6 api
# shamelessly copied from https://deepintodjango.com/jwt-authentication-class-for-python-requests
#
import time
from json import JSONDecodeError
from typing import Dict

import requests
from requests import PreparedRequest, RequestException
from requests.auth import AuthBase

REQUEST_TIMEOUT = 30  # Seconds


class JWTAuthFailedAuthentication(Exception):
    """Raised when could not authenticate: not allowed or, credentials could be wrong."""
    pass


class JWTAuth(AuthBase):
    """A simple JWT Authentication mechanism to add `access_token` to a request.

    Raises:
        JWTAuthFailedAuthentication: at request-time when authentication failed.

    Usage:
        ```
        jwt_auth = JWTAuth(
            auth_url='https://endpoint.example/api/v1/auth',
            api_payload={
                'api_key': '<API_KEY>',
                'api_secret': '<API_SECRET>',
            }
        )
        requests.get(url, auth=jwt_auth)
        ```
    """
    def __init__(self, auth_url: str, api_payload: Dict):
        self.auth_url = auth_url
        self.api_payload = api_payload

        self.access_token = None
        self.access_token_expires = 0
        self.refresh_token = None
        self.refresh_token_expires = 0

    def __call__(self, request: PreparedRequest):
        """Called by requests when a request is made, authenticates if no token or expired.
        Sets the access token as Authorization Bearer.
        """
        self.authenticate()
        assert self.access_token, 'empty access_token detected'
        request.headers['Authorization'] = f'Bearer {self.access_token}'
        return request

    def authenticate(self):
        """Do authentication request if needed, returns False if not needed.

        Raises:
            JWTAuthFailedAuthentication: credentials incorrect or response was malformed.
        """
        current_timestamp = int(time.time())
        if self.access_token and self.access_token_expires > current_timestamp:
            # Still valid access token, do nothing
            return False
        if self.access_token and self.access_token_expires < current_timestamp < self.refresh_token_expires:
            # Access token expired but refresh token still valid, use refresh token
            response = requests.post(self.auth_url, timeout=REQUEST_TIMEOUT, json={'refresh_token': self.refresh_token})
        else:
            # No tokens or expired, need an api key authentication
            response = requests.post(self.auth_url, timeout=REQUEST_TIMEOUT, json=self.api_payload)

        try:
            json_data = response.json()
            response.raise_for_status()
            self.access_token = json_data['access_token']
            #self.access_token_expires = int(json_data['access_token_expires_at'])
            self.refresh_token = json_data['refresh_token']
            #self.refresh_token_expires = int(json_data['refresh_token_expires_at'])
        except RequestException as e:
            raise JWTAuthFailedAuthentication(f'{e}: {json_data}') from e
        except JSONDecodeError as e:
            raise JWTAuthFailedAuthentication(
                f'JWT authentication endpoint did not return valid json: {response.text}') from e
        except KeyError as e:
            raise JWTAuthFailedAuthentication(f'JWT authentication endpoint did not return all tokens: {e}') from e

        return True  # Required by pylint

