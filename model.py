class Snapshot:
    """Simple model for Snapshots. Add the tracking id of the event this Snapshot belongs to 
    with the parent_id argument."""
    def __init__(self, name, time_usec, parent_id=None, category=None, properties=None):
        self.name = name
        self.time_usec = time_usec
        self.parent_id = parent_id
        self.category = category
        self.properties = properties
        
    def getDict(self):
        values = {"name":self.name, "time-usec":self.time_usec, "type":"SNAPSHOT"}
        if self.parent_id != None:
            values["parent-id"] = self.parent_id
        if self.category != None:
            values["category"] = self.category 
        if self.properties != None:
            values["properties"] = self.properties
                
        return values



class Property:
    """Simple model for user defined properties. Holds a name, value, and type of the property."""
    def __init__(self, name, value, property_type):
        self.name = name
        self.value = value
        self.property_type = property_type
    
    def getDict(self):
        values = {"name":self.name, "value":self.value, "type":self.property_type}
        return values
