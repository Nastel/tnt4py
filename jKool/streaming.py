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

HAVE_SSL = True
try:
    import ssl
except:
    HAVE_SSL = False

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("There was a problem importing paho.mqtt.client. Make sure it is installed before using MqttHandler")
    





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


def on_connect(client, userdata, rc):
    print("Connection returned result: "+mqtt.connack_string(rc))
    
def on_publish(client, userdata, mid):
    print("Message " + str(mid) + " has been received")
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
        client.loop_stop()
    


class HttpHandler(logging.Handler):
    """Logging handler that will stream to jKool cloud service using http/s."""

    def __init__(self, accessToken, urlStr="https://data.jkoolcloud.com", level=logging.INFO):
        logging.Handler.__init__(self, level)
        
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

        message = logRecordToJsonString(record)
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

            
    

class MqttHandler(logging.Handler):
    """Logging handler that streams to jKool using mqtt"""

    def __init__(self, urlStr, topic=None, level=logging.INFO, keepalive=60, username=None, password=None, **ssl_properties):
        
        logging.Handler.__init__(self, level)
        
        self.url = urlStr
        self.port = urlparse(urlStr).port
        self.topic = topic
        self.keepalive = keepalive

        self.client = mqtt.Client()
        
        self.client.on_connect = on_connect
        self.client.on_publish = on_publish
        self.client.on_disconnect = on_disconnect
        
        if username is not None:
            self.client.username_pw_set(username, password)
        
        for key in ("ca_certs", "certfile", "keyfile", "ciphers"):
            if key in ssl_properties:
                setattr(self, key, ssl_properties[key])
            else:
                setattr(self, key, None)
                
        if self.ca_certs is not None:
            if HAVE_SSL == False:
                raise ValueError("This platform has no SSL/TLS.")
            self.port = 8883
            self.cert_reqs = ssl_properties.get("cert_reqs", ssl.CERT_REQUIRED)
            self.tls_version = ssl_properties.get("tls_version", ssl.PROTOCOL_TLSv1)
            
            self.client.tls_set(self.ca_certs, self.certfile, self.keyfile, self.cert_reqs, self.tls_version, self.ciphers)
        
        self.connect()


    def connect(self):
        """Connect client to broker and start network loop"""
        if self.port == None:
            self.client.connect(self.url, keepalive=self.keepalive)
        else:
            self.client.connect(self.url, self.port, self.keepalive)

        self.start()


    def emit(self, record):
        if self.topic == None:
            self.topic = record.name
        message = logRecordToJsonString(record)

        result, mid = self.client.publish(self.topic, message)

    def stop(self):
        self.client.loop_stop()

    def start(self):
        self.client.loop_start()


    
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
    
        

