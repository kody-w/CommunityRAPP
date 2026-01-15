"""
Dynamics 365 Digital Twin Agent

A 1:1 Digital Twin of a Dynamics 365 CRM instance that allows working with the twin
exactly like working with the real D365 instance. All operations are mirrored to both
systems with comparison output to verify synchronization.

Architecture:
- D365Client: OAuth2 authentication and Web API operations against real D365
- DigitalTwinStore: Local JSON-based storage mirroring D365 entity structure
- SyncEngine: Synchronization between Digital Twin and real D365
- D365DigitalTwinAgent: Agent interface exposing unified operations

Every operation executes on BOTH systems and returns comparative results.
"""

import json
import logging
import os
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode, quote

try:
    import requests
    from msal import ConfidentialClientApplication
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    logging.warning("MSAL or requests not available. D365 Digital Twin will use mock mode.")

from agents.basic_agent import BasicAgent

# Try to import Azure storage for persistent twin storage
try:
    from utils.azure_file_storage import AzureFileStorageManager
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False
    logging.warning("Azure File Storage not available. Using local file storage.")


class D365Client:
    """
    Dynamics 365 Web API Client with OAuth2 authentication.

    Handles all communication with the real Dynamics 365 instance.
    Uses MSAL for OAuth2 client credentials flow.
    """

    def __init__(
        self,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        d365_url: str = None
    ):
        """
        Initialize D365 client with OAuth2 credentials.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: App registration client ID
            client_secret: App registration client secret
            d365_url: Dynamics 365 instance URL (e.g., https://org.crm.dynamics.com)
        """
        self.tenant_id = tenant_id or os.environ.get('D365_TENANT_ID')
        self.client_id = client_id or os.environ.get('D365_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('D365_CLIENT_SECRET')
        self.d365_url = (d365_url or os.environ.get('D365_URL', '')).rstrip('/')

        self.access_token = None
        self.token_expiry = None
        self.api_version = "v9.2"
        self.mock_mode = not MSAL_AVAILABLE or not all([
            self.tenant_id, self.client_id, self.client_secret, self.d365_url
        ])

        if self.mock_mode:
            logging.info("D365Client running in MOCK mode - no real D365 connection")
        else:
            self._msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            logging.info(f"D365Client initialized for: {self.d365_url}")

    def _get_access_token(self) -> str:
        """Acquire or refresh OAuth2 access token."""
        if self.mock_mode:
            return "mock_token"

        # Check if current token is still valid
        if self.access_token and self.token_expiry:
            if datetime.now(timezone.utc) < self.token_expiry:
                return self.access_token

        # Acquire new token
        scope = [f"{self.d365_url}/.default"]
        result = self._msal_app.acquire_token_for_client(scopes=scope)

        if "access_token" in result:
            self.access_token = result["access_token"]
            # Token typically valid for 1 hour, refresh 5 minutes early
            expires_in = result.get("expires_in", 3600)
            self.token_expiry = datetime.now(timezone.utc).replace(
                second=datetime.now(timezone.utc).second + expires_in - 300
            )
            return self.access_token
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Failed to acquire D365 token: {error}")

    @property
    def _headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Prefer": "odata.include-annotations=*"
        }

    @property
    def _api_base(self) -> str:
        """Get base API URL."""
        return f"{self.d365_url}/api/data/{self.api_version}"

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Tuple[Dict, int]:
        """
        Make HTTP request to D365 Web API.

        Returns:
            Tuple of (response_data, status_code)
        """
        if self.mock_mode:
            return self._mock_request(method, endpoint, data, params)

        url = f"{self._api_base}/{endpoint}"
        if params:
            url += "?" + urlencode(params)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers,
                json=data if data else None,
                timeout=30
            )

            if response.status_code == 204:
                return {"success": True}, 204
            elif response.status_code >= 400:
                return {"error": response.text, "status": response.status_code}, response.status_code
            else:
                return response.json() if response.text else {"success": True}, response.status_code

        except requests.exceptions.RequestException as e:
            logging.error(f"D365 request failed: {str(e)}")
            return {"error": str(e)}, 500

    def _mock_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Tuple[Dict, int]:
        """Generate mock responses for testing without real D365."""
        entity_set = endpoint.split('(')[0].split('?')[0]

        mock_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        if method == "GET":
            if "(" in endpoint:  # Single record
                return {
                    f"{entity_set.rstrip('s')}id": mock_id,
                    "name": f"Mock {entity_set} Record",
                    "createdon": timestamp,
                    "modifiedon": timestamp,
                    "@odata.etag": f'W/"{hash(endpoint)}"'
                }, 200
            else:  # Collection
                return {
                    "@odata.context": f"{self._api_base}/$metadata#{entity_set}",
                    "value": [
                        {
                            f"{entity_set.rstrip('s')}id": str(uuid.uuid4()),
                            "name": f"Mock {entity_set} {i+1}",
                            "createdon": timestamp,
                            "modifiedon": timestamp
                        }
                        for i in range(3)
                    ]
                }, 200
        elif method == "POST":
            return {
                f"{entity_set.rstrip('s')}id": mock_id,
                **data,
                "createdon": timestamp,
                "modifiedon": timestamp
            }, 201
        elif method == "PATCH":
            return {"success": True, "modifiedon": timestamp}, 204
        elif method == "DELETE":
            return {"success": True}, 204

        return {"success": True}, 200

    # ========== CRUD Operations ==========

    def create(self, entity_set: str, data: Dict) -> Tuple[Dict, int]:
        """Create a new record."""
        return self._request("POST", entity_set, data=data)

    def read(self, entity_set: str, record_id: str = None, params: Dict = None) -> Tuple[Dict, int]:
        """Read record(s) with optional OData query parameters."""
        endpoint = f"{entity_set}({record_id})" if record_id else entity_set
        return self._request("GET", endpoint, params=params)

    def update(self, entity_set: str, record_id: str, data: Dict) -> Tuple[Dict, int]:
        """Update an existing record."""
        endpoint = f"{entity_set}({record_id})"
        return self._request("PATCH", endpoint, data=data)

    def delete(self, entity_set: str, record_id: str) -> Tuple[Dict, int]:
        """Delete a record."""
        endpoint = f"{entity_set}({record_id})"
        return self._request("DELETE", endpoint)

    def query(
        self,
        entity_set: str,
        select: List[str] = None,
        filter_expr: str = None,
        expand: str = None,
        orderby: str = None,
        top: int = None
    ) -> Tuple[Dict, int]:
        """
        Execute OData query against entity set.

        Args:
            entity_set: Entity set name (e.g., 'accounts', 'contacts')
            select: Fields to return
            filter_expr: OData filter expression
            expand: Related entities to expand
            orderby: Sort order
            top: Limit number of records
        """
        params = {}
        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if expand:
            params["$expand"] = expand
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = str(top)

        return self._request("GET", entity_set, params=params if params else None)

    def get_metadata(self) -> Tuple[Dict, int]:
        """Get entity metadata."""
        return self._request("GET", "$metadata")


class DigitalTwinStore:
    """
    Local storage for the Digital Twin of Dynamics 365.

    Mirrors the D365 entity structure using JSON storage.
    Supports full CRUD operations and OData-like queries.
    """

    def __init__(self, twin_id: str = "default"):
        """
        Initialize Digital Twin storage.

        Args:
            twin_id: Unique identifier for this twin instance
        """
        self.twin_id = twin_id
        self.storage_dir = f"d365_twins/{twin_id}"
        self._data: Dict[str, Dict[str, Dict]] = {}  # entity_set -> {record_id -> record}
        self._metadata: Dict[str, Any] = {
            "twin_id": twin_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_sync": None,
            "sync_status": "not_synced",
            "record_counts": {}
        }

        # Try Azure File Storage first, fall back to local
        self._azure_storage = None
        if AZURE_STORAGE_AVAILABLE:
            try:
                self._azure_storage = AzureFileStorageManager()
                logging.info(f"Digital Twin using Azure File Storage: {self.storage_dir}")
            except Exception as e:
                logging.warning(f"Azure Storage unavailable, using local: {e}")

        self._load_twin()

    def _load_twin(self):
        """Load twin data from storage."""
        try:
            if self._azure_storage:
                # Load from Azure
                data_content = self._azure_storage.read_file(self.storage_dir, "twin_data.json")
                if data_content:
                    self._data = json.loads(data_content)

                meta_content = self._azure_storage.read_file(self.storage_dir, "twin_metadata.json")
                if meta_content:
                    self._metadata = json.loads(meta_content)
            else:
                # Load from local file
                local_path = f"/tmp/{self.storage_dir}"
                if os.path.exists(f"{local_path}/twin_data.json"):
                    with open(f"{local_path}/twin_data.json", "r") as f:
                        self._data = json.load(f)
                    with open(f"{local_path}/twin_metadata.json", "r") as f:
                        self._metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load twin data: {e}")
            self._data = {}

    def _save_twin(self):
        """Save twin data to storage."""
        try:
            # Update record counts
            self._metadata["record_counts"] = {
                entity: len(records) for entity, records in self._data.items()
            }

            if self._azure_storage:
                self._azure_storage.write_file(
                    self.storage_dir,
                    "twin_data.json",
                    json.dumps(self._data, indent=2)
                )
                self._azure_storage.write_file(
                    self.storage_dir,
                    "twin_metadata.json",
                    json.dumps(self._metadata, indent=2)
                )
            else:
                local_path = f"/tmp/{self.storage_dir}"
                os.makedirs(local_path, exist_ok=True)
                with open(f"{local_path}/twin_data.json", "w") as f:
                    json.dump(self._data, f, indent=2)
                with open(f"{local_path}/twin_metadata.json", "w") as f:
                    json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save twin data: {e}")

    def _get_entity_key_field(self, entity_set: str) -> str:
        """Get the primary key field name for an entity set."""
        # D365 standard naming convention
        singular = entity_set.rstrip('s')
        return f"{singular}id"

    def create(self, entity_set: str, data: Dict) -> Tuple[Dict, int]:
        """Create a record in the twin."""
        if entity_set not in self._data:
            self._data[entity_set] = {}

        key_field = self._get_entity_key_field(entity_set)
        record_id = data.get(key_field) or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            key_field: record_id,
            **data,
            "createdon": timestamp,
            "modifiedon": timestamp,
            "_twin_synced": False,
            "_twin_checksum": None
        }
        record["_twin_checksum"] = self._compute_checksum(record)

        self._data[entity_set][record_id] = record
        self._save_twin()

        return record, 201

    def read(self, entity_set: str, record_id: str = None, params: Dict = None) -> Tuple[Dict, int]:
        """Read record(s) from the twin."""
        if entity_set not in self._data:
            return {"value": []}, 200

        if record_id:
            record = self._data[entity_set].get(record_id)
            if record:
                return self._clean_record(record), 200
            return {"error": "Record not found"}, 404

        # Return all records (filtered/sorted if params provided)
        records = list(self._data[entity_set].values())

        if params:
            records = self._apply_odata_params(records, params)

        return {
            "@odata.context": f"$metadata#{entity_set}",
            "value": [self._clean_record(r) for r in records]
        }, 200

    def update(self, entity_set: str, record_id: str, data: Dict) -> Tuple[Dict, int]:
        """Update a record in the twin."""
        if entity_set not in self._data or record_id not in self._data[entity_set]:
            return {"error": "Record not found"}, 404

        record = self._data[entity_set][record_id]
        record.update(data)
        record["modifiedon"] = datetime.now(timezone.utc).isoformat()
        record["_twin_synced"] = False
        record["_twin_checksum"] = self._compute_checksum(record)

        self._save_twin()
        return {"success": True, "modifiedon": record["modifiedon"]}, 204

    def delete(self, entity_set: str, record_id: str) -> Tuple[Dict, int]:
        """Delete a record from the twin."""
        if entity_set not in self._data or record_id not in self._data[entity_set]:
            return {"error": "Record not found"}, 404

        del self._data[entity_set][record_id]
        self._save_twin()
        return {"success": True}, 204

    def query(
        self,
        entity_set: str,
        select: List[str] = None,
        filter_expr: str = None,
        expand: str = None,
        orderby: str = None,
        top: int = None
    ) -> Tuple[Dict, int]:
        """Execute OData-like query on twin data."""
        params = {}
        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = str(top)

        return self.read(entity_set, params=params if params else None)

    def _apply_odata_params(self, records: List[Dict], params: Dict) -> List[Dict]:
        """Apply OData query parameters to records."""
        result = records.copy()

        # Apply $filter (simplified - supports basic equality)
        if "$filter" in params:
            filter_expr = params["$filter"]
            # Parse simple eq expressions: "name eq 'Value'"
            if " eq " in filter_expr:
                parts = filter_expr.split(" eq ")
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip().strip("'\"")
                    result = [r for r in result if str(r.get(field, "")).lower() == value.lower()]
            # Parse contains expressions: "contains(name,'Value')"
            elif "contains(" in filter_expr.lower():
                import re
                match = re.match(r"contains\((\w+),\s*'([^']+)'\)", filter_expr, re.IGNORECASE)
                if match:
                    field, value = match.groups()
                    result = [r for r in result if value.lower() in str(r.get(field, "")).lower()]

        # Apply $orderby
        if "$orderby" in params:
            orderby = params["$orderby"]
            desc = " desc" in orderby.lower()
            field = orderby.replace(" desc", "").replace(" asc", "").strip()
            result = sorted(result, key=lambda x: x.get(field, ""), reverse=desc)

        # Apply $top
        if "$top" in params:
            top = int(params["$top"])
            result = result[:top]

        # Apply $select
        if "$select" in params:
            fields = [f.strip() for f in params["$select"].split(",")]
            key_field = self._get_entity_key_field("records")
            fields.append(key_field)  # Always include primary key
            result = [{k: v for k, v in r.items() if k in fields} for r in result]

        return result

    def _clean_record(self, record: Dict) -> Dict:
        """Remove internal twin fields from record."""
        return {k: v for k, v in record.items() if not k.startswith("_twin_")}

    def _compute_checksum(self, record: Dict) -> str:
        """Compute checksum for record comparison."""
        clean = self._clean_record(record)
        return hashlib.md5(json.dumps(clean, sort_keys=True).encode()).hexdigest()

    def get_metadata(self) -> Dict:
        """Get twin metadata."""
        return self._metadata

    def get_all_entities(self) -> Dict[str, int]:
        """Get counts of all entities in the twin."""
        return {entity: len(records) for entity, records in self._data.items()}

    def bulk_load(self, entity_set: str, records: List[Dict]):
        """Bulk load records into the twin (for initial sync)."""
        if entity_set not in self._data:
            self._data[entity_set] = {}

        key_field = self._get_entity_key_field(entity_set)
        for record in records:
            record_id = record.get(key_field)
            if record_id:
                record["_twin_synced"] = True
                record["_twin_checksum"] = self._compute_checksum(record)
                self._data[entity_set][record_id] = record

        self._save_twin()


class SyncEngine:
    """
    Synchronization engine between Digital Twin and real Dynamics 365.

    Handles initial sync, delta sync, and conflict detection.
    """

    def __init__(self, d365_client: D365Client, twin_store: DigitalTwinStore):
        self.d365 = d365_client
        self.twin = twin_store
        self.sync_log: List[Dict] = []

    def initial_sync(self, entity_sets: List[str], max_records: int = 100) -> Dict:
        """
        Perform initial sync of specified entities from D365 to twin.

        Args:
            entity_sets: List of entity set names to sync
            max_records: Maximum records per entity to sync

        Returns:
            Sync result summary
        """
        results = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entities_synced": {},
            "errors": []
        }

        for entity_set in entity_sets:
            try:
                response, status = self.d365.query(entity_set, top=max_records)

                if status == 200 and "value" in response:
                    records = response["value"]
                    self.twin.bulk_load(entity_set, records)
                    results["entities_synced"][entity_set] = len(records)

                    self.sync_log.append({
                        "action": "initial_sync",
                        "entity": entity_set,
                        "records": len(records),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    results["errors"].append({
                        "entity": entity_set,
                        "error": response.get("error", "Unknown error")
                    })
            except Exception as e:
                results["errors"].append({
                    "entity": entity_set,
                    "error": str(e)
                })

        # Update twin metadata
        self.twin._metadata["last_sync"] = results["timestamp"]
        self.twin._metadata["sync_status"] = "synced" if not results["errors"] else "partial"
        self.twin._save_twin()

        return results

    def compare_records(self, entity_set: str, record_id: str) -> Dict:
        """
        Compare a record between twin and D365.

        Returns detailed comparison with field-level differences.
        """
        twin_result, twin_status = self.twin.read(entity_set, record_id)
        d365_result, d365_status = self.d365.read(entity_set, record_id)

        comparison = {
            "entity_set": entity_set,
            "record_id": record_id,
            "twin_exists": twin_status == 200,
            "d365_exists": d365_status == 200,
            "in_sync": False,
            "differences": []
        }

        if twin_status == 200 and d365_status == 200:
            # Compare field by field
            twin_record = twin_result
            d365_record = d365_result

            all_keys = set(twin_record.keys()) | set(d365_record.keys())
            all_keys = {k for k in all_keys if not k.startswith("@") and not k.startswith("_")}

            for key in all_keys:
                twin_val = twin_record.get(key)
                d365_val = d365_record.get(key)
                if twin_val != d365_val:
                    comparison["differences"].append({
                        "field": key,
                        "twin_value": twin_val,
                        "d365_value": d365_val
                    })

            comparison["in_sync"] = len(comparison["differences"]) == 0

        return comparison


class D365DigitalTwinAgent(BasicAgent):
    """
    Dynamics 365 Digital Twin Agent - Full 1:1 CRM Mirror

    This agent maintains a Digital Twin of a Dynamics 365 CRM instance.
    All operations are executed on BOTH the twin AND the real D365 system,
    with comparative output to verify synchronization.

    Key Capabilities:
    - Full CRUD operations mirrored to both systems
    - OData query support ($filter, $select, $expand, $orderby, $top)
    - Initial and delta synchronization
    - Record comparison and conflict detection
    - Verification output showing both systems side-by-side
    """

    def __init__(self, twin_id: str = "default"):
        self.name = "D365DigitalTwin"
        self.metadata = {
            "name": self.name,
            "description": """Dynamics 365 Digital Twin - Work with a 1:1 mirror of your D365 CRM.
            All operations execute on BOTH the Digital Twin and real D365, showing comparative results.
            Supports: create, read, update, delete, query, sync, compare operations on accounts, contacts,
            leads, opportunities and other D365 entities.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "create", "read", "update", "delete", "query",
                            "sync", "compare", "status", "list_entities"
                        ],
                        "description": "Operation to perform on the Digital Twin (and real D365)"
                    },
                    "entity_set": {
                        "type": "string",
                        "description": "D365 entity set name (e.g., 'accounts', 'contacts', 'leads', 'opportunities')"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "Record GUID for read/update/delete/compare operations"
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data for create/update operations"
                    },
                    "select": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to select (OData $select)"
                    },
                    "filter": {
                        "type": "string",
                        "description": "OData filter expression (e.g., \"name eq 'Contoso'\")"
                    },
                    "orderby": {
                        "type": "string",
                        "description": "Sort order (e.g., 'createdon desc')"
                    },
                    "top": {
                        "type": "integer",
                        "description": "Maximum records to return"
                    },
                    "twin_only": {
                        "type": "boolean",
                        "description": "If true, only operate on Digital Twin without mirroring to D365"
                    }
                },
                "required": ["operation"]
            }
        }

        # Initialize D365 client and Digital Twin store
        self.d365 = D365Client()
        self.twin = DigitalTwinStore(twin_id)
        self.sync_engine = SyncEngine(self.d365, self.twin)

        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute the requested operation with mirrored output."""
        operation = kwargs.get("operation", "status")
        entity_set = kwargs.get("entity_set", "")
        record_id = kwargs.get("record_id")
        data = kwargs.get("data", {})
        twin_only = kwargs.get("twin_only", False)

        # OData params
        select = kwargs.get("select", [])
        filter_expr = kwargs.get("filter")
        orderby = kwargs.get("orderby")
        top = kwargs.get("top")

        # Route to operation handler
        handlers = {
            "create": self._create,
            "read": self._read,
            "update": self._update,
            "delete": self._delete,
            "query": self._query,
            "sync": self._sync,
            "compare": self._compare,
            "status": self._status,
            "list_entities": self._list_entities
        }

        handler = handlers.get(operation, self._status)

        try:
            result = handler(
                entity_set=entity_set,
                record_id=record_id,
                data=data,
                select=select,
                filter_expr=filter_expr,
                orderby=orderby,
                top=top,
                twin_only=twin_only
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            logging.error(f"D365DigitalTwin error: {str(e)}")
            return json.dumps({
                "status": "error",
                "operation": operation,
                "error": str(e)
            }, indent=2)

    def _create(self, entity_set: str, data: Dict, twin_only: bool = False, **kwargs) -> Dict:
        """Create record in both twin and D365."""
        result = {
            "operation": "CREATE",
            "entity_set": entity_set,
            "mirrored": not twin_only,
            "twin_result": None,
            "d365_result": None,
            "in_sync": False
        }

        # Create in twin
        twin_response, twin_status = self.twin.create(entity_set, data)
        result["twin_result"] = {
            "status": twin_status,
            "data": twin_response
        }

        if not twin_only:
            # Mirror to D365
            d365_response, d365_status = self.d365.create(entity_set, data)
            result["d365_result"] = {
                "status": d365_status,
                "data": d365_response
            }
            result["in_sync"] = (twin_status == 201 and d365_status == 201)

        result["status"] = "success" if result["twin_result"]["status"] == 201 else "failed"
        return result

    def _read(self, entity_set: str, record_id: str = None, select: List[str] = None,
              twin_only: bool = False, **kwargs) -> Dict:
        """Read record(s) from both twin and D365."""
        result = {
            "operation": "READ",
            "entity_set": entity_set,
            "record_id": record_id,
            "mirrored": not twin_only,
            "twin_result": None,
            "d365_result": None,
            "in_sync": False
        }

        params = {}
        if select:
            params["$select"] = ",".join(select)

        # Read from twin
        twin_response, twin_status = self.twin.read(entity_set, record_id, params if params else None)
        result["twin_result"] = {
            "status": twin_status,
            "data": twin_response
        }

        if not twin_only:
            # Mirror read from D365
            d365_response, d365_status = self.d365.read(entity_set, record_id, params if params else None)
            result["d365_result"] = {
                "status": d365_status,
                "data": d365_response
            }

            # Check if results match
            if twin_status == d365_status:
                if twin_status == 200:
                    # Compare record counts or single record
                    if "value" in twin_response and "value" in d365_response:
                        result["in_sync"] = len(twin_response["value"]) == len(d365_response["value"])
                    else:
                        result["in_sync"] = True  # Single records present in both

        result["status"] = "success" if result["twin_result"]["status"] == 200 else "not_found"
        return result

    def _update(self, entity_set: str, record_id: str, data: Dict,
                twin_only: bool = False, **kwargs) -> Dict:
        """Update record in both twin and D365."""
        result = {
            "operation": "UPDATE",
            "entity_set": entity_set,
            "record_id": record_id,
            "mirrored": not twin_only,
            "twin_result": None,
            "d365_result": None,
            "in_sync": False
        }

        # Update in twin
        twin_response, twin_status = self.twin.update(entity_set, record_id, data)
        result["twin_result"] = {
            "status": twin_status,
            "data": twin_response
        }

        if not twin_only:
            # Mirror to D365
            d365_response, d365_status = self.d365.update(entity_set, record_id, data)
            result["d365_result"] = {
                "status": d365_status,
                "data": d365_response
            }
            result["in_sync"] = (twin_status == 204 and d365_status == 204)

        result["status"] = "success" if result["twin_result"]["status"] == 204 else "failed"
        return result

    def _delete(self, entity_set: str, record_id: str, twin_only: bool = False, **kwargs) -> Dict:
        """Delete record from both twin and D365."""
        result = {
            "operation": "DELETE",
            "entity_set": entity_set,
            "record_id": record_id,
            "mirrored": not twin_only,
            "twin_result": None,
            "d365_result": None,
            "in_sync": False
        }

        # Delete from twin
        twin_response, twin_status = self.twin.delete(entity_set, record_id)
        result["twin_result"] = {
            "status": twin_status,
            "data": twin_response
        }

        if not twin_only:
            # Mirror to D365
            d365_response, d365_status = self.d365.delete(entity_set, record_id)
            result["d365_result"] = {
                "status": d365_status,
                "data": d365_response
            }
            result["in_sync"] = (twin_status == 204 and d365_status == 204)

        result["status"] = "success" if result["twin_result"]["status"] == 204 else "failed"
        return result

    def _query(self, entity_set: str, select: List[str] = None, filter_expr: str = None,
               orderby: str = None, top: int = None, twin_only: bool = False, **kwargs) -> Dict:
        """Execute OData query on both twin and D365."""
        result = {
            "operation": "QUERY",
            "entity_set": entity_set,
            "query_params": {
                "select": select,
                "filter": filter_expr,
                "orderby": orderby,
                "top": top
            },
            "mirrored": not twin_only,
            "twin_result": None,
            "d365_result": None,
            "in_sync": False
        }

        # Query twin
        twin_response, twin_status = self.twin.query(
            entity_set, select=select, filter_expr=filter_expr,
            orderby=orderby, top=top
        )
        result["twin_result"] = {
            "status": twin_status,
            "record_count": len(twin_response.get("value", [])),
            "data": twin_response
        }

        if not twin_only:
            # Mirror query to D365
            d365_response, d365_status = self.d365.query(
                entity_set, select=select, filter_expr=filter_expr,
                orderby=orderby, top=top
            )
            result["d365_result"] = {
                "status": d365_status,
                "record_count": len(d365_response.get("value", [])),
                "data": d365_response
            }

            # Compare results
            if twin_status == d365_status == 200:
                twin_count = len(twin_response.get("value", []))
                d365_count = len(d365_response.get("value", []))
                result["in_sync"] = twin_count == d365_count
                result["comparison"] = {
                    "twin_count": twin_count,
                    "d365_count": d365_count,
                    "difference": abs(twin_count - d365_count)
                }

        result["status"] = "success"
        return result

    def _sync(self, entity_set: str = None, **kwargs) -> Dict:
        """Synchronize twin with D365."""
        entities_to_sync = [entity_set] if entity_set else [
            "accounts", "contacts", "leads", "opportunities"
        ]

        result = self.sync_engine.initial_sync(entities_to_sync)
        result["operation"] = "SYNC"
        return result

    def _compare(self, entity_set: str, record_id: str, **kwargs) -> Dict:
        """Compare specific record between twin and D365."""
        comparison = self.sync_engine.compare_records(entity_set, record_id)
        comparison["operation"] = "COMPARE"
        return comparison

    def _status(self, **kwargs) -> Dict:
        """Get Digital Twin status."""
        twin_meta = self.twin.get_metadata()
        entities = self.twin.get_all_entities()

        return {
            "operation": "STATUS",
            "twin_id": twin_meta.get("twin_id"),
            "created_at": twin_meta.get("created_at"),
            "last_sync": twin_meta.get("last_sync"),
            "sync_status": twin_meta.get("sync_status"),
            "d365_connected": not self.d365.mock_mode,
            "d365_url": self.d365.d365_url if not self.d365.mock_mode else "Mock Mode",
            "entities": entities,
            "total_records": sum(entities.values())
        }

    def _list_entities(self, **kwargs) -> Dict:
        """List all entities in the Digital Twin."""
        entities = self.twin.get_all_entities()

        return {
            "operation": "LIST_ENTITIES",
            "entities": [
                {"name": name, "record_count": count}
                for name, count in entities.items()
            ],
            "total_entities": len(entities),
            "total_records": sum(entities.values())
        }


# Export the agent class for dynamic loading
__all__ = ['D365DigitalTwinAgent']
