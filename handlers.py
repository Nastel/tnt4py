
# coding: utf-8

# In[1]:

import logging
import urllib.request
from urllib.parse import urlparse
import json
import http.client


# In[2]:

class AuthorizationError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)

class jKoolHandler(logging.Handler):
    """Logging handler that will stream to jKool cloud service"""
        
    def __init__(self, accessToken, urlStr="https://data.jkoolcloud.com", level=logging.INFO):
        logging.Handler.__init__(self)
        
        self.level = level
        self.token = accessToken
            
        self.url = urlStr
        uri = urlparse(self.url)
        
        scheme = uri.scheme
        self.secure = ("https" == scheme)
        
        self.host = uri.hostname
        self.path = uri.path
        
        if self.host == None:
            self.host = "localhost"
            
        self.connect()
        
            
    def emit(self, record):
        name = record.name
        time = int(record.created) * 1000000
        message = record.getMessage()
        level = record.levelname
        
        payload={'operation': name, 'type':'EVENT', 'time-usec':time, 'msg-text':message, 'severity':level}
        payload.update(record.__dict__)
        formatted = json.dumps(payload).encode('utf8')
        headers = {'token': self.token, "Content-Type": "application/json"}
        
        try:
            self.connection.request("POST", self.path, formatted, headers)
        except ConnectionError as err:
            conn.close()
            raise err
        else:
            response = self.connection.getresponse()
            data = response.read()
            print(response.status, response.reason)
        
        
    def connect(self):
        if self.secure:
            conn = http.client.HTTPSConnection(self.host, timeout = 10)
        else:
            conn = http.client.HTTPConnection(self.host, timeout = 10)
        
        try:
            conn.connect()
        except ConnectionError as err:
            conn.close()
            raise err
        else:
            print("Connected")
            self.connection = conn
            
        self.sendAuthRequest(self.connection)
        
    def sendAuthRequest(self, conn):
        """Attempts to authorize the token with jKool"""
        
        msg = "<access-request><token>" + self.token + "</token></access-request>"
        headers = {"Content-Type": "text/plain"}
        
        try:
            conn.request("POST", "", msg, headers)
        except ConnectionError as err:
            conn.close()
            raise err
        else:
            response = conn.getresponse()
            data = response.read()
        
        if response.status >= 200 and response.status < 300:
            print("Authorized")
        else:
            conn.close()
            print("response.status, response.reason")
            raise AuthorizationError("Error authorizing token")

