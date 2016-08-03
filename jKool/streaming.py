# 
#  Copyright 2015 JKOOL, LLC.
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import urllib.request
from urllib.parse import urlparse
import json
import http.client
import jKool.metrics
import uuid



class SnapshotEncoder(json.JSONEncoder):
    """Allows for Snapshot and Property to be serializable with json.dumps.
    Must add this class to the optional cls param of json.dumps method"""
    def default(self, obj):
        if isinstance(obj, jKool.metrics.Property) or isinstance(obj, jKool.metrics.Snapshot):
            return obj.getDict()

        return json.JSONEncoder.default(self, obj)
    
    
    
class AuthorizationError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)

    
class jKoolHandler(logging.Handler):
    """Logging handler to stream to jKool cloud service using specified protocol."""
    
    def logRecordToJsonString(record):
        name = record.name
        time = int(record.created) * 1000000
        message = record.getMessage()
        level = record.levelname
        payload={'operation': name, 'type':'EVENT', 'time-usec':time, 'msg-text':message, 'severity':level}


        extras = record.__dict__
        try:
            tagNames = extras['allTags']
            tags = {}
            for tag in tagNames:
                jsonTag = tag.replace('_', '-')
                tags[jsonTag] = extras[tag]
            payload.update(tags)
        except KeyError:
            pass

        return json.dumps(payload, cls = SnapshotEncoder)
    
        
    class HttpHandler():
        """Logging handler that will stream to jKool cloud service using http/s."""

        def __init__(self, accessToken, urlStr="https://data.jkoolcloud.com", level=logging.INFO):
                        
            self.level = level
            self.token = accessToken

            self.url = urlStr
            uri = urlparse(self.url)

            scheme = uri.scheme
            self.secure = ("https" == scheme)

            self.host = uri.hostname
            self.path = uri.path
            self.port = uri.port

            if self.host == None:
                self.host = "localhost"

            self.connect()


        def emit(self, record):
            
            message = jKoolHandler.logRecordToJsonString(record)
            headers = {"Content-Type": "application/json"}

            try:
                self.connection.request("POST", self.path, message, headers)
            except (ConnectionError, timeout) as err:
                conn.close()
                raise err
            else:
                response = self.connection.getresponse()
                data = response.read()
                print(response.status, response.reason)


        def connect(self):
            
            if self.secure:
                if self.port != None:
                    conn = http.client.HTTPSConnection(self.host, port=self.port, timeout=10)
                else:
                    conn = http.client.HTTPSConnection(self.host, timeout=10)
            else:
                if self.port != None:
                    conn = http.client.HTTPConnection(self.host, port=self.port, timeout=10)
                else:
                    conn = http.client.HTTPConnection(self.host, timeout=10)

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
                conn.request("POST", self.path, msg, headers)
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
                raise AuthorizationError("Error authorizing token")

    
    class MqttHandler:
        """Logging handler that streams to jKool using mqtt"""
        
        def __init__(self, accessToken, urlStr, level=logging.INFO, keepalive=60):
            import paho.mqtt.client as mqtt

            self.url = urlStr
            self.port = urlparse(urlStr).port
            
            self.keepalive = keepalive
            
            self.client = mqtt.Client()
            
            self.connect()
            
            
        def connect(self):
            """Connect client to broker and start network loop"""
            if self.port == None:
                self.client.connect(self.url, keepalive=self.keepalive)
            else:
                self.client.connect(self.url, self.port, self.keepalive)
                
            self.start()
            
            
        def emit(self, record):
            topic = record.name
            message = jKoolHandler.logRecordToJsonString(record)
            print(message)
            
            result, mid = self.client.publish(topic, message)
            print(result, mid)
            
        def stop(self):
            self.client.loop_stop()
            
        def start(self):
            self.client.loop_start()
    
    
    def __init__(self, accessToken, urlStr="https://data.jkoolcloud.com", level=logging.INFO, protocol="http"):
        logging.Handler.__init__(self, level)
        
        protocol = protocol.lower()

        if protocol == "http" or protocol == "https":
            self.handler = self.HttpHandler(accessToken, urlStr, level)
        elif protocol == "mqtt":
            self.handler = self.MqttHandler(accessToken, urlStr, level)
        else:
            raise ValueError("Invalid protocol")
            
    
    def emit(self, record):
        self.handler.emit(record)


    
def logEvent(logger, msg_text, source_fqn, tracking_id=str(uuid.uuid4()), time_usec=None, corr_id=None, 
            exception=None, resource=None, wait_time_used=None, source_url=None,
            severity=logging.INFO, pid=None, tid=None, comp_code=None, reason_code=None,
            location=None, operation=None, user=None, start_time_usec=None, end_time_usec=None,
            elapsed_time_usec=None, msg_size=None, encoding=None,
            charset=None, mime_type=None, msg_age=None, msg_tag=None, parent_tracking_id=None,
            properties = None, snapshots = None):
    """Helper method to enrich event streaming"""
    
    arguments = locals()
    emptyKeys = [k for k, v in arguments.items() if v is None or k == 'logger']
    allTags = [k for k,v in arguments.items() if v != logger and v != None and k != 'severity']
    arguments['allTags'] = allTags
    for key in emptyKeys:
        del arguments[key]
    
    logger.log(severity, msg_text, extra=arguments)
    
        

