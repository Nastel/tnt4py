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
    """Logging handler that will stream to jKool cloud service."""
        
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
        name = record.name
        time = int(record.created) * 1000000
        message = record.getMessage()
        level = record.levelname
        
        extras = record.__dict__
        tagNames = extras['allTags']
        tags = {}
        for tag in tagNames:
            jsonTag = tag.replace('_', '-')
            tags[jsonTag] = extras[tag]
            
        
        payload={'operation': name, 'type':'EVENT', 'time-usec':time, 'msg-text':message, 'severity':level}
        payload.update(tags)
        formatted = json.dumps(payload, cls = SnapshotEncoder)
        headers = {"Content-Type": "application/json"}
        
        
        try:
            self.connection.request("POST", self.path, formatted, headers)
        except (ConnectionError, HTTPException, timeout) as err:
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
        except (ConnectionError, HTTPException) as err:
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
        except (ConnectionError, HTTPException) as err:
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


            

    
    
def logEvent(logger, msg_text, source_fqn, tracking_id=str(uuid.uuid4()), time_usec=None, corr_id=None, 
            exception=None, resource=None, wait_time_used=None, source_url=None,
            severity=logging.INFO, pid=None, tid=None, comp_code=None, reason_code=None,
            location=None, operation=None, user=None, start_time_usec=None, end_time_usec=None,
            elapsed_time_usec=None, msg_size=None, encoding=None,
            charset=None, mime_type=None, msg_age=None, msg_tag=None, parent_tracking_id=None,
            properties = None, snapshots = None):
    
    arguments = locals()
    emptyKeys = [k for k, v in arguments.items() if v is None or k == 'logger']
    allTags = [k for k,v in arguments.items() if v != logger and v != None and k != 'severity']
    arguments['allTags'] = allTags
    for key in emptyKeys:
        del arguments[key]
    
    logger.log(severity, msg_text, extra=arguments)
    
        

