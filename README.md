# TNT4PY - Python Streaming
Stream your logs, metrics, custom KPIs using `jKool.streaming`. Search, create dashboards & analyze your data using jKool @ https://www.jkoolcloud.com.

# License
Apache V2.0

## How to Start Streaming
* Obtain `jkool-api-access-token` by registering with jKool https://data.jkoolcloud.com. (FREE)

### Easily stream simple messages from command line
* Get started streaming quickly by calling jKool/streaming.py from the command line.
* Specify which protocol to use for streaming with `--https` or `--mqtt`
* See full usage with -h option.

Example stream over https:
~~~sh
python streaming.py "Your message to stream" --https your-access-token
~~~~

Example stream over mqtt:
~~~sh
python streaming.py "Your message to stream" --mqtt broker-address your-username your-password --topic python/streams
~~~

### Incorporate with your python applications
* Create a HttpHandler using your `jkool-api-access-token` and optional url and logging level
    * Default streaming url is `https://data.jkoolcloud.com`
    * Default log level is `logging.INFO`
* Add this handler to your python loggers
* Logs, metrics are automatically streamed when logging calls are made.

~~~~python
from jKool import streaming
import logging

logger = logging.getLogger("jKool logger")
hdlr = streaming.HttpHandler("jkool-api-access-token")
logger.addHandler(hdlr)

logger.error("Test log")
~~~~

### Streaming over MQTT
* `MqttHandler` implements an MQTT client using the Eclipse Paho Python Client API. See the [documentation](https://eclipse.org/paho/clients/python/) for installation instructions.
* Create an MqttHandler with the url of the mqtt broker to publish to.
   * Default logging `level` is logging.INFO
   * Default message topic is the name of the logger but can be specified with `topic` parameter.
   * Specify a unique client id string with `client_id`. If not specified, one will be generated. In this case the clean_session parameter must be True.
   * If `clean_session` set to True the broker will remove all information about this client when it disconnects. If False, the client is a durable client and subscription information and queued messages will be retained when the client disconnects. Defaults to True
   * Use `username` and `password` to set a username/password for broker authentication.
   * Configure network encryption and authentication options by passing a dictionary or keyword arguements for ssl options. See Paho Python Client [documentation](https://eclipse.org/paho/clients/python/docs/#option-functions) for tls_set() for valid options.
* Add this handler to your python loggers

~~~python
# dictionary with ssl options
options = {"ca_certs":"certificates/ca_certs.crt", "certfile":"path-to-certfile", "keyfile":"path-to-keyfile",
"cert_reqs":"ssl.CERT_REQUIRED", "tls_version":"ssl.PROTOCOL_TLSv1", "ciphers":"a-cipher"}

# options passed as dict
MqttHandler("broker-url", topic="tnt4py example", client_id = str(uuid.uuid4()), clean_session=False, **options)

# or specify each
MqttHandler("broker-url", ca_certs="path-to-ca-file", cert_reqs=ssl.CERT_REQUIRED)
~~~

## Event Stream Decoration
Events can be decorated/enriched before streaming to jKool. Use `logEvent` helper method with user defined decorations.
Required parameters are the logger instance, logging message, and the sourcefqn. Source fully qualified name (fqn) is a cannonical event source name with the following convention `TYPE=name#TYPE=name..#TYPE=name` which is read from left to right and defines enclosure relationship. 

Example: `APPL=PythonStreaming#SERVER=PythonServer100#NETADDR=11.0.0.2#DATACENTER=DC1#GEOADDR=52.52437,13.41053` interpreted as application `PythonStreaming` running on server `PythonServer100` at network address `11.0.0.2` in datacenter `DC1` located in geo-location `52.52437,13.41053`. 

Supported types: `USER, APPL, PROCESS, APPSERVER, SERVER, RUNTIME, VIRTUAL, NETWORK, DEVICE, NETADDR, GEOADDR, DATACENTER, DATASTORE, CACHE, SERVICE, QUEUE` 

~~~~python
streaming.logEvent(logger, "This is an example",
       "APPL=PythonStreaming#SERVER=PythonServer100#NETADDR=11.0.0.2#DATACENTER=DC1#GEOADDR=52.52437,13.41053")
~~~~

Use optional parameters to decorate event streams.

~~~~python
sourcefqn = "APPL=PythonStreaming#SERVER=PythonServer100#NETADDR=11.0.0.2#DATACENTER=DC1#GEOADDR=52.52437,13.41053"
streaming.logEvent(logger, "This is an example", sourcefqn,
       time_usec=int(time.time() * 1000000), corr_id="your-correlator-id", location="Atlanta, Ga")
~~~~
Correlators are used to connect/stitch multiple events into a single related activity. Any number of events are related when they share one ore more correlators.

## User Defined Metrics
You can also report user defined metrics (e.g. CPU, memory, Order Amount).
This is done via `Snapshots` and `Properties` in the metrics module. A `Snapshot` holds a collection of user define `Properties`, each property is `name, value, type` pairing.

### Streaming Events with Snapshots and Custom Properties
Snapshots can be attached to an `Event` by adding a list of snapshots to the `snapshots` argument.

~~~~python
mySnapshot = Snapshot("Payment", category="Order")
mySnapshot.addProperty("order-no", orderNo, "string")
mySnapshot.addProperty("order-amount", orderAmount, "integer")

# snapshots argument must be a list containing one or more Snapshots
logEvent(logger, "Order Processed Succesfully", sourcefqn, snapshots=[mySnapshot])
~~~~

Snapshots and Properties are automatically serialized into JSON format.
