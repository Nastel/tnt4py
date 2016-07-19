# TNT4PY - Python Streaming
Stream your logs, metrics, custom KPIs using `jKool.streaming`. Search, create dashboards & analyze your data using jKool @ https://data.jkoolcloud.com.

## How to Start Streaming
* Create a jKoolHandler using your access token and optional url and logging level
    * Default url is https://data.jkoolcloud.com
    * Default level is logging.INFO
* Add this handler to your python loggers.
* Logs, metrics are automatically streamed when logging calls are made.

~~~~python
from jKool import streaming
import logging

logger = logging.getLogger("jKool logger")
hdlr = streaming.jKoolHandler("jkool-api-access-token")
logger.addHandler(hdlr)

logger.error("Test log")
~~~~

## More Detailed Event Streaming
To stream more detailed Events to jKool use the logEvent helper method.
Required parameters are the logger instance, logging message, and the source fqn

~~~~python
streaming.logEvent(logger, "This is an example",
       "APPL=PythonStreaming#SERVER=PythonServer100#NETADDR=11.0.0.2#DATACENTER=DC1#GEOADDR=52.52437,13.41053")
~~~~

Use optional parameters to add more information to your logs.

~~~~python
sourcefqn = "APPL=PythonStreaming#SERVER=PythonServer100#NETADDR=11.0.0.2#DATACENTER=DC1#GEOADDR=52.52437,13.41053"
streaming.logEvent(logger, "This is an example", sourcefqn,
       time_usec=1457524800000000, corr_id="your-correlator-id", location="Atlanta, Ga")
~~~~

## Measurements and Metrics
You can also report measurements and metrics like CPU and memory as well as other user defined metrics.
This is done via Snapshots and Properties in the metrics module. A Snapshot holds a collection of Properties that are user defined.

### Streaming Events with Snapshots and Custom Properties
Snapshots can be attached to an Event by adding a list of Snapshots to the snapshots arguement.

~~~~python
# generate unique id
tracking = str(uuid4())

mySnapshot = Snapshot("Payment", 1466662761000000, parent_id=tracking, category="Order")
mySnapshot.addProperty("order-no", orderNo, "string")
mySnapshot.addProperty("order-amount", orderAmount, "integer")

# snapshots argument must be a list containing one or more Snapshots
logEvent(logger, "Order Processed Succesfully", sourcefqn, corr_id=tracking, snapshots=[mySnapshot])
~~~~

Snapshots and Properties are automatically serialized into JSON format.
