#
# Rules file for Research Activity data
#
import time

class IndexData:
    def __init__(self):
        pass

    def __activate__(self, context):
        # Prepare variables
        self.index = context["fields"]
        self.indexer = context["indexer"]
        self.object = context["object"]
        self.payload = context["payload"]
        self.params = context["params"]
        self.utils = context["pyUtils"]
        self.config = context["jsonConfig"]

        # Common data
        self.__newDoc()

        # Real metadata
        if self.itemType == "object":
            self.__basicData()
            self.__metadata()

        # Make sure security comes after workflows
        self.__security(self.oid, self.index)

    def __newDoc(self):
        self.oid = self.object.getId()
        self.pid = self.payload.getId()
        metadataPid = self.params.getProperty("metaPid", "DC")

        self.utils.add(self.index, "storage_id", self.oid)
        if self.pid == metadataPid:
            self.itemType = "object"
        else:
            self.oid += "/" + self.pid
            self.itemType = "datastream"
            self.utils.add(self.index, "identifier", self.pid)

        self.utils.add(self.index, "id", self.oid)
        self.utils.add(self.index, "item_type", self.itemType)
        self.utils.add(self.index, "last_modified", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        self.utils.add(self.index, "harvest_config", self.params.getProperty("jsonConfigOid"))
        self.utils.add(self.index, "harvest_rules", self.params.getProperty("rulesOid"))
        self.utils.add(self.index, "display_type", "research_activities")

        self.item_security = []

    def __basicData(self):
        self.utils.add(self.index, "repository_name", self.params["repository.name"])
        self.utils.add(self.index, "repository_type", self.params["repository.type"])
        # Persistent Identifiers
        pidProperty = self.config.getString(None, ["curation", "pidProperty"])
        if pidProperty is None:
            self.log.error("No configuration found for persistent IDs!")
        else:
            pid = self.params[pidProperty]
            if pid is not None:
                self.utils.add(self.index, "known_ids", pid)
                self.utils.add(self.index, "pidProperty", pid)
                self.utils.add(self.index, "oai_identifier", pid)
        self.utils.add(self.index, "oai_set", "Activities")

    def __metadata(self):
        self.utils.registerNamespace("dc", "http://purl.org/dc/terms/")
        self.utils.registerNamespace("foaf", "http://xmlns.com/foaf/0.1/")

        jsonPayload = self.object.getPayload("metadata.json")
        json = self.utils.getJsonObject(jsonPayload.open())
        jsonPayload.close()

        metadata = json.getObject("metadata")
        self.utils.add(self.index, "dc_identifier", metadata.get("dc.identifier"))

        data = json.getObject("data")
        self.utils.add(self.index, "grant_number", data.get("ID"))
        self.utils.add(self.index, "dc_date_submitted", data.get("Submit Year"))
        self.utils.add(self.index, "dc_date", data.get("Start Year"))
        self.utils.add(self.index, "dc_title", data.get("Title"))
        self.utils.add(self.index, "dc_description", data.get("Description"))
        self.utils.add(self.index, "foaf_name", data.get("Institution"))
        self.utils.add(self.index, "dc_subject", data.get("Discipline"))
        self.utils.add(self.index, "dc_format", "application/x-mint-research-activity")
        self.__indexList("dc_contributor", data.get("Investigators").split(";"))

        # Known IDs
        identifier = json.getString(None, ["metadata", "dc.identifier"])
        if identifier is not None:
            self.utils.add(self.index, "known_ids", identifier)

    def __security(self, oid, index):
        roles = self.utils.getRolesWithAccess(oid)
        if roles is not None:
            for role in roles:
                self.utils.add(index, "security_filter", role)
        else:
            # Default to guest access if Null object returned
            schema = self.utils.getAccessSchema("derby");
            schema.setRecordId(oid)
            schema.set("role", "guest")
            self.utils.setAccessSchema(schema, "derby")
            self.utils.add(index, "security_filter", "guest")

    def __indexList(self, name, values):
        for value in values:
            self.utils.add(self.index, name, value)
