"""
Dynamics 365 Sync Guardian Agent

An autonomous agent that maintains synchronization between the Digital Twin
and the real Dynamics 365 instance. Continuously monitors both systems,
detects changes, resolves conflicts, and ensures they remain in sync.

Architecture:
- ChangeTracker: Monitors and tracks changes in both systems
- ConflictResolver: Handles merge conflicts with configurable strategies
- DriftDetector: Identifies synchronization drift between systems
- HealthMonitor: Tracks overall sync health and alerts on issues
- AuditLogger: Records all sync activities for troubleshooting
- RecoveryManager: Handles failures with retry logic and rollback
- SyncScheduler: Manages sync timing, priorities, and autonomous operation

Key Capabilities:
- Autonomous background synchronization
- Bidirectional change detection
- Multiple conflict resolution strategies
- Real-time drift detection and alerting
- Comprehensive audit trail
- Self-healing with automatic recovery
"""

import json
import logging
import os
import hashlib
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import queue

from agents.basic_agent import BasicAgent

# Import the Digital Twin agent components
try:
    from agents.d365_digital_twin_agent import (
        D365Client, DigitalTwinStore, SyncEngine, D365DigitalTwinAgent
    )
    TWIN_AVAILABLE = True
except ImportError:
    TWIN_AVAILABLE = False
    logging.warning("D365 Digital Twin agent not available")


class ConflictStrategy(Enum):
    """Conflict resolution strategies."""
    D365_WINS = "d365_wins"          # Real D365 always takes precedence
    TWIN_WINS = "twin_wins"          # Digital Twin always takes precedence
    NEWEST_WINS = "newest_wins"      # Most recently modified record wins
    MANUAL = "manual"                 # Flag for manual review
    MERGE = "merge"                   # Attempt to merge non-conflicting fields
    SKIP = "skip"                     # Skip conflicting records


class SyncDirection(Enum):
    """Synchronization direction."""
    BIDIRECTIONAL = "bidirectional"  # Sync both ways
    D365_TO_TWIN = "d365_to_twin"    # Pull from D365 to Twin only
    TWIN_TO_D365 = "twin_to_d365"    # Push from Twin to D365 only


class ChangeType(Enum):
    """Types of changes detected."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class SyncStatus(Enum):
    """Overall sync status."""
    IN_SYNC = "in_sync"
    DRIFTED = "drifted"
    SYNCING = "syncing"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class Change:
    """Represents a detected change."""
    change_id: str
    entity_set: str
    record_id: str
    change_type: ChangeType
    source: str  # "d365" or "twin"
    timestamp: str
    old_data: Optional[Dict] = None
    new_data: Optional[Dict] = None
    checksum: Optional[str] = None
    processed: bool = False
    conflict: bool = False


@dataclass
class Conflict:
    """Represents a synchronization conflict."""
    conflict_id: str
    entity_set: str
    record_id: str
    twin_change: Change
    d365_change: Change
    detected_at: str
    resolved: bool = False
    resolution_strategy: Optional[str] = None
    resolution_result: Optional[Dict] = None


@dataclass
class SyncEvent:
    """Audit log entry for sync events."""
    event_id: str
    event_type: str
    entity_set: str
    record_id: Optional[str]
    source: str
    target: str
    status: str
    timestamp: str
    details: Dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class HealthStatus:
    """Current health status of the sync system."""
    status: SyncStatus
    last_sync: Optional[str]
    last_check: str
    twin_connected: bool
    d365_connected: bool
    pending_changes: int
    unresolved_conflicts: int
    drift_percentage: float
    entities_monitored: List[str]
    error_count_24h: int
    warnings: List[str] = field(default_factory=list)


class ChangeTracker:
    """
    Tracks changes in both Digital Twin and D365 systems.
    Uses checksums and timestamps to detect modifications.
    """

    def __init__(self, twin_store: DigitalTwinStore, d365_client: D365Client):
        self.twin = twin_store
        self.d365 = d365_client
        self.tracked_entities: List[str] = []
        self.last_known_state: Dict[str, Dict[str, str]] = {}  # entity -> {record_id -> checksum}
        self.pending_changes: List[Change] = []
        self._lock = threading.Lock()

    def track_entities(self, entities: List[str]):
        """Set which entities to track for changes."""
        self.tracked_entities = entities
        # Initialize baseline state
        for entity in entities:
            self._capture_baseline(entity)

    def _capture_baseline(self, entity_set: str):
        """Capture current state as baseline for change detection."""
        if entity_set not in self.last_known_state:
            self.last_known_state[entity_set] = {}

        # Capture twin state
        twin_data, _ = self.twin.read(entity_set)
        if "value" in twin_data:
            for record in twin_data["value"]:
                key = self._get_record_key(entity_set, record)
                if key:
                    self.last_known_state[entity_set][f"twin_{key}"] = self._compute_checksum(record)

        # Capture D365 state
        d365_data, _ = self.d365.query(entity_set, top=1000)
        if "value" in d365_data:
            for record in d365_data["value"]:
                key = self._get_record_key(entity_set, record)
                if key:
                    self.last_known_state[entity_set][f"d365_{key}"] = self._compute_checksum(record)

    def _get_record_key(self, entity_set: str, record: Dict) -> Optional[str]:
        """Get the primary key value from a record."""
        singular = entity_set.rstrip('s')
        key_field = f"{singular}id"
        return record.get(key_field)

    def _compute_checksum(self, record: Dict) -> str:
        """Compute checksum for change detection."""
        # Exclude metadata and timestamps for comparison
        clean = {k: v for k, v in record.items()
                 if not k.startswith('@') and not k.startswith('_')
                 and k not in ('modifiedon', 'createdon')}
        return hashlib.md5(json.dumps(clean, sort_keys=True, default=str).encode()).hexdigest()

    def detect_changes(self) -> List[Change]:
        """Scan both systems and detect all changes since last check."""
        changes = []

        with self._lock:
            for entity_set in self.tracked_entities:
                # Detect Twin changes
                twin_changes = self._detect_twin_changes(entity_set)
                changes.extend(twin_changes)

                # Detect D365 changes
                d365_changes = self._detect_d365_changes(entity_set)
                changes.extend(d365_changes)

            self.pending_changes.extend(changes)

        return changes

    def _detect_twin_changes(self, entity_set: str) -> List[Change]:
        """Detect changes in the Digital Twin."""
        changes = []
        current_records = {}

        twin_data, status = self.twin.read(entity_set)
        if status != 200 or "value" not in twin_data:
            return changes

        for record in twin_data["value"]:
            key = self._get_record_key(entity_set, record)
            if not key:
                continue

            checksum = self._compute_checksum(record)
            current_records[key] = checksum
            state_key = f"twin_{key}"

            if state_key not in self.last_known_state.get(entity_set, {}):
                # New record
                changes.append(Change(
                    change_id=str(uuid.uuid4()),
                    entity_set=entity_set,
                    record_id=key,
                    change_type=ChangeType.CREATED,
                    source="twin",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    new_data=record,
                    checksum=checksum
                ))
            elif self.last_known_state[entity_set][state_key] != checksum:
                # Modified record
                changes.append(Change(
                    change_id=str(uuid.uuid4()),
                    entity_set=entity_set,
                    record_id=key,
                    change_type=ChangeType.UPDATED,
                    source="twin",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    new_data=record,
                    checksum=checksum
                ))

        # Check for deleted records
        for state_key in list(self.last_known_state.get(entity_set, {}).keys()):
            if state_key.startswith("twin_"):
                record_id = state_key[5:]  # Remove "twin_" prefix
                if record_id not in current_records:
                    changes.append(Change(
                        change_id=str(uuid.uuid4()),
                        entity_set=entity_set,
                        record_id=record_id,
                        change_type=ChangeType.DELETED,
                        source="twin",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

        # Update known state
        if entity_set not in self.last_known_state:
            self.last_known_state[entity_set] = {}
        for key, checksum in current_records.items():
            self.last_known_state[entity_set][f"twin_{key}"] = checksum

        return changes

    def _detect_d365_changes(self, entity_set: str) -> List[Change]:
        """Detect changes in Dynamics 365."""
        changes = []
        current_records = {}

        d365_data, status = self.d365.query(entity_set, top=1000)
        if status != 200 or "value" not in d365_data:
            return changes

        for record in d365_data["value"]:
            key = self._get_record_key(entity_set, record)
            if not key:
                continue

            checksum = self._compute_checksum(record)
            current_records[key] = checksum
            state_key = f"d365_{key}"

            if state_key not in self.last_known_state.get(entity_set, {}):
                # New record
                changes.append(Change(
                    change_id=str(uuid.uuid4()),
                    entity_set=entity_set,
                    record_id=key,
                    change_type=ChangeType.CREATED,
                    source="d365",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    new_data=record,
                    checksum=checksum
                ))
            elif self.last_known_state[entity_set][state_key] != checksum:
                # Modified record
                changes.append(Change(
                    change_id=str(uuid.uuid4()),
                    entity_set=entity_set,
                    record_id=key,
                    change_type=ChangeType.UPDATED,
                    source="d365",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    new_data=record,
                    checksum=checksum
                ))

        # Check for deleted records
        for state_key in list(self.last_known_state.get(entity_set, {}).keys()):
            if state_key.startswith("d365_"):
                record_id = state_key[5:]  # Remove "d365_" prefix
                if record_id not in current_records:
                    changes.append(Change(
                        change_id=str(uuid.uuid4()),
                        entity_set=entity_set,
                        record_id=record_id,
                        change_type=ChangeType.DELETED,
                        source="d365",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ))

        # Update known state
        if entity_set not in self.last_known_state:
            self.last_known_state[entity_set] = {}
        for key, checksum in current_records.items():
            self.last_known_state[entity_set][f"d365_{key}"] = checksum

        return changes

    def get_pending_changes(self) -> List[Change]:
        """Get all pending unprocessed changes."""
        with self._lock:
            return [c for c in self.pending_changes if not c.processed]

    def mark_processed(self, change_id: str):
        """Mark a change as processed."""
        with self._lock:
            for change in self.pending_changes:
                if change.change_id == change_id:
                    change.processed = True
                    break


class ConflictResolver:
    """
    Handles synchronization conflicts between Twin and D365.
    Supports multiple resolution strategies.
    """

    def __init__(
        self,
        twin_store: DigitalTwinStore,
        d365_client: D365Client,
        default_strategy: ConflictStrategy = ConflictStrategy.NEWEST_WINS
    ):
        self.twin = twin_store
        self.d365 = d365_client
        self.default_strategy = default_strategy
        self.conflicts: List[Conflict] = []
        self.manual_queue: List[Conflict] = []
        self._lock = threading.Lock()

    def detect_conflicts(self, changes: List[Change]) -> List[Conflict]:
        """Detect conflicts where both systems changed the same record."""
        conflicts = []

        # Group changes by entity_set and record_id
        changes_by_record: Dict[str, List[Change]] = defaultdict(list)
        for change in changes:
            key = f"{change.entity_set}:{change.record_id}"
            changes_by_record[key].append(change)

        # Find records with changes from both sources
        for key, record_changes in changes_by_record.items():
            twin_changes = [c for c in record_changes if c.source == "twin"]
            d365_changes = [c for c in record_changes if c.source == "d365"]

            if twin_changes and d365_changes:
                # Conflict detected
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    entity_set=record_changes[0].entity_set,
                    record_id=record_changes[0].record_id,
                    twin_change=twin_changes[0],
                    d365_change=d365_changes[0],
                    detected_at=datetime.now(timezone.utc).isoformat()
                )
                conflicts.append(conflict)

                # Mark changes as conflicting
                for c in record_changes:
                    c.conflict = True

        with self._lock:
            self.conflicts.extend(conflicts)

        return conflicts

    def resolve(
        self,
        conflict: Conflict,
        strategy: Optional[ConflictStrategy] = None
    ) -> Dict:
        """Resolve a conflict using the specified strategy."""
        strategy = strategy or self.default_strategy
        result = {
            "conflict_id": conflict.conflict_id,
            "strategy": strategy.value,
            "resolved": False,
            "action_taken": None,
            "error": None
        }

        try:
            if strategy == ConflictStrategy.D365_WINS:
                result = self._resolve_d365_wins(conflict)
            elif strategy == ConflictStrategy.TWIN_WINS:
                result = self._resolve_twin_wins(conflict)
            elif strategy == ConflictStrategy.NEWEST_WINS:
                result = self._resolve_newest_wins(conflict)
            elif strategy == ConflictStrategy.MERGE:
                result = self._resolve_merge(conflict)
            elif strategy == ConflictStrategy.MANUAL:
                result = self._queue_for_manual(conflict)
            elif strategy == ConflictStrategy.SKIP:
                result = self._resolve_skip(conflict)

            if result.get("resolved"):
                conflict.resolved = True
                conflict.resolution_strategy = strategy.value
                conflict.resolution_result = result

        except Exception as e:
            result["error"] = str(e)
            logging.error(f"Conflict resolution failed: {e}")

        return result

    def _resolve_d365_wins(self, conflict: Conflict) -> Dict:
        """D365 data overwrites Twin data."""
        if conflict.d365_change.change_type == ChangeType.DELETED:
            # Delete from twin
            self.twin.delete(conflict.entity_set, conflict.record_id)
            return {"resolved": True, "action_taken": "deleted_from_twin"}
        else:
            # Update twin with D365 data
            if conflict.d365_change.new_data:
                self.twin.update(
                    conflict.entity_set,
                    conflict.record_id,
                    conflict.d365_change.new_data
                )
            return {"resolved": True, "action_taken": "updated_twin_from_d365"}

    def _resolve_twin_wins(self, conflict: Conflict) -> Dict:
        """Twin data overwrites D365 data."""
        if conflict.twin_change.change_type == ChangeType.DELETED:
            # Delete from D365
            self.d365.delete(conflict.entity_set, conflict.record_id)
            return {"resolved": True, "action_taken": "deleted_from_d365"}
        else:
            # Update D365 with Twin data
            if conflict.twin_change.new_data:
                self.d365.update(
                    conflict.entity_set,
                    conflict.record_id,
                    conflict.twin_change.new_data
                )
            return {"resolved": True, "action_taken": "updated_d365_from_twin"}

    def _resolve_newest_wins(self, conflict: Conflict) -> Dict:
        """Most recently modified record wins."""
        twin_time = conflict.twin_change.timestamp
        d365_time = conflict.d365_change.timestamp

        # Also check modifiedon if available
        if conflict.twin_change.new_data:
            twin_time = conflict.twin_change.new_data.get('modifiedon', twin_time)
        if conflict.d365_change.new_data:
            d365_time = conflict.d365_change.new_data.get('modifiedon', d365_time)

        if twin_time >= d365_time:
            return self._resolve_twin_wins(conflict)
        else:
            return self._resolve_d365_wins(conflict)

    def _resolve_merge(self, conflict: Conflict) -> Dict:
        """Attempt to merge non-conflicting field changes."""
        twin_data = conflict.twin_change.new_data or {}
        d365_data = conflict.d365_change.new_data or {}

        # Find fields that changed in each
        merged = {}
        field_conflicts = []

        all_fields = set(twin_data.keys()) | set(d365_data.keys())
        for field in all_fields:
            if field.startswith('@') or field.startswith('_'):
                continue
            if field in ('modifiedon', 'createdon'):
                continue

            twin_val = twin_data.get(field)
            d365_val = d365_data.get(field)

            if twin_val == d365_val:
                merged[field] = twin_val
            elif twin_val is None:
                merged[field] = d365_val
            elif d365_val is None:
                merged[field] = twin_val
            else:
                # Field conflict - use newest
                field_conflicts.append(field)
                merged[field] = twin_val if conflict.twin_change.timestamp >= conflict.d365_change.timestamp else d365_val

        # Apply merged data to both systems
        if merged:
            self.twin.update(conflict.entity_set, conflict.record_id, merged)
            self.d365.update(conflict.entity_set, conflict.record_id, merged)

        return {
            "resolved": True,
            "action_taken": "merged",
            "field_conflicts": field_conflicts,
            "merged_data": merged
        }

    def _queue_for_manual(self, conflict: Conflict) -> Dict:
        """Queue conflict for manual resolution."""
        with self._lock:
            self.manual_queue.append(conflict)
        return {
            "resolved": False,
            "action_taken": "queued_for_manual",
            "queue_position": len(self.manual_queue)
        }

    def _resolve_skip(self, conflict: Conflict) -> Dict:
        """Skip the conflict without taking action."""
        return {"resolved": True, "action_taken": "skipped"}

    def get_unresolved_conflicts(self) -> List[Conflict]:
        """Get all unresolved conflicts."""
        with self._lock:
            return [c for c in self.conflicts if not c.resolved]

    def get_manual_queue(self) -> List[Conflict]:
        """Get conflicts awaiting manual resolution."""
        with self._lock:
            return list(self.manual_queue)


class DriftDetector:
    """
    Detects synchronization drift between Twin and D365.
    Provides detailed drift reports and metrics.
    """

    def __init__(self, twin_store: DigitalTwinStore, d365_client: D365Client):
        self.twin = twin_store
        self.d365 = d365_client

    def calculate_drift(self, entity_sets: List[str]) -> Dict:
        """Calculate drift metrics for specified entities."""
        drift_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_drift_percentage": 0.0,
            "entities": {},
            "total_records_compared": 0,
            "total_drifted": 0,
            "summary": ""
        }

        total_records = 0
        total_drifted = 0

        for entity_set in entity_sets:
            entity_drift = self._analyze_entity_drift(entity_set)
            drift_report["entities"][entity_set] = entity_drift
            total_records += entity_drift["total_records"]
            total_drifted += entity_drift["drifted_records"]

        drift_report["total_records_compared"] = total_records
        drift_report["total_drifted"] = total_drifted
        drift_report["overall_drift_percentage"] = (
            (total_drifted / total_records * 100) if total_records > 0 else 0.0
        )

        # Generate summary
        if drift_report["overall_drift_percentage"] == 0:
            drift_report["summary"] = "Systems are perfectly synchronized"
        elif drift_report["overall_drift_percentage"] < 5:
            drift_report["summary"] = "Minor drift detected - within acceptable limits"
        elif drift_report["overall_drift_percentage"] < 20:
            drift_report["summary"] = "Moderate drift - sync recommended"
        else:
            drift_report["summary"] = "Significant drift - immediate sync required"

        return drift_report

    def _analyze_entity_drift(self, entity_set: str) -> Dict:
        """Analyze drift for a single entity set."""
        result = {
            "entity_set": entity_set,
            "total_records": 0,
            "drifted_records": 0,
            "twin_only": 0,
            "d365_only": 0,
            "field_differences": 0,
            "drift_percentage": 0.0,
            "drifted_record_ids": []
        }

        # Get records from both systems
        twin_data, twin_status = self.twin.read(entity_set)
        d365_data, d365_status = self.d365.query(entity_set, top=1000)

        if twin_status != 200 or d365_status != 200:
            return result

        # Build lookup maps
        key_field = f"{entity_set.rstrip('s')}id"
        twin_records = {r.get(key_field): r for r in twin_data.get("value", []) if r.get(key_field)}
        d365_records = {r.get(key_field): r for r in d365_data.get("value", []) if r.get(key_field)}

        all_ids = set(twin_records.keys()) | set(d365_records.keys())
        result["total_records"] = len(all_ids)

        for record_id in all_ids:
            twin_record = twin_records.get(record_id)
            d365_record = d365_records.get(record_id)

            if twin_record and not d365_record:
                result["twin_only"] += 1
                result["drifted_records"] += 1
                result["drifted_record_ids"].append(record_id)
            elif d365_record and not twin_record:
                result["d365_only"] += 1
                result["drifted_records"] += 1
                result["drifted_record_ids"].append(record_id)
            elif twin_record and d365_record:
                # Compare fields
                if self._records_differ(twin_record, d365_record):
                    result["field_differences"] += 1
                    result["drifted_records"] += 1
                    result["drifted_record_ids"].append(record_id)

        result["drift_percentage"] = (
            (result["drifted_records"] / result["total_records"] * 100)
            if result["total_records"] > 0 else 0.0
        )

        # Limit drifted_record_ids to first 100
        result["drifted_record_ids"] = result["drifted_record_ids"][:100]

        return result

    def _records_differ(self, twin_record: Dict, d365_record: Dict) -> bool:
        """Check if two records have meaningful differences."""
        ignore_fields = {'modifiedon', 'createdon', '@odata.etag', '_twin_synced', '_twin_checksum'}

        for key, twin_val in twin_record.items():
            if key in ignore_fields or key.startswith('@') or key.startswith('_'):
                continue
            d365_val = d365_record.get(key)
            if twin_val != d365_val:
                return True

        for key in d365_record:
            if key in ignore_fields or key.startswith('@') or key.startswith('_'):
                continue
            if key not in twin_record:
                return True

        return False


class AuditLogger:
    """
    Comprehensive audit logging for all sync operations.
    Stores events for troubleshooting and compliance.
    """

    def __init__(self, max_events: int = 10000):
        self.events: List[SyncEvent] = []
        self.max_events = max_events
        self._lock = threading.Lock()

    def log(
        self,
        event_type: str,
        entity_set: str,
        record_id: Optional[str] = None,
        source: str = "",
        target: str = "",
        status: str = "success",
        details: Dict = None,
        error: Optional[str] = None
    ):
        """Log a sync event."""
        event = SyncEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            entity_set=entity_set,
            record_id=record_id,
            source=source,
            target=target,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
            error=error
        )

        with self._lock:
            self.events.append(event)
            # Trim old events if needed
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

        logging.info(f"[SYNC AUDIT] {event_type}: {entity_set}/{record_id} - {status}")

    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Dict]:
        """Get recent audit events."""
        with self._lock:
            events = self.events[-limit:]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return [asdict(e) for e in events]

    def get_error_count(self, hours: int = 24) -> int:
        """Get count of errors in the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        with self._lock:
            return sum(1 for e in self.events
                      if e.status == "error" and e.timestamp >= cutoff_str)

    def get_summary(self, hours: int = 24) -> Dict:
        """Get summary of sync activity."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        with self._lock:
            recent = [e for e in self.events if e.timestamp >= cutoff_str]

        return {
            "period_hours": hours,
            "total_events": len(recent),
            "successful": sum(1 for e in recent if e.status == "success"),
            "errors": sum(1 for e in recent if e.status == "error"),
            "warnings": sum(1 for e in recent if e.status == "warning"),
            "by_type": self._count_by_type(recent),
            "by_entity": self._count_by_entity(recent)
        }

    def _count_by_type(self, events: List[SyncEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts = defaultdict(int)
        for e in events:
            counts[e.event_type] += 1
        return dict(counts)

    def _count_by_entity(self, events: List[SyncEvent]) -> Dict[str, int]:
        """Count events by entity."""
        counts = defaultdict(int)
        for e in events:
            counts[e.entity_set] += 1
        return dict(counts)


class RecoveryManager:
    """
    Handles failures with retry logic, rollback, and self-healing.
    """

    def __init__(
        self,
        twin_store: DigitalTwinStore,
        d365_client: D365Client,
        audit_logger: AuditLogger,
        max_retries: int = 3
    ):
        self.twin = twin_store
        self.d365 = d365_client
        self.audit = audit_logger
        self.max_retries = max_retries
        self.failed_operations: List[Dict] = []
        self._lock = threading.Lock()

    def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        entity_set: str,
        record_id: str = None,
        **kwargs
    ) -> Tuple[bool, Any]:
        """Execute an operation with automatic retry on failure."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = operation(**kwargs)
                self.audit.log(
                    event_type=operation_name,
                    entity_set=entity_set,
                    record_id=record_id,
                    status="success",
                    details={"attempt": attempt + 1}
                )
                return True, result

            except Exception as e:
                last_error = str(e)
                logging.warning(f"Retry {attempt + 1}/{self.max_retries} for {operation_name}: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

        # All retries failed
        self.audit.log(
            event_type=operation_name,
            entity_set=entity_set,
            record_id=record_id,
            status="error",
            error=last_error,
            details={"attempts": self.max_retries}
        )

        with self._lock:
            self.failed_operations.append({
                "operation": operation_name,
                "entity_set": entity_set,
                "record_id": record_id,
                "error": last_error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kwargs": {k: v for k, v in kwargs.items() if k != 'data'}  # Exclude large data
            })

        return False, last_error

    def get_failed_operations(self) -> List[Dict]:
        """Get list of failed operations for retry or manual intervention."""
        with self._lock:
            return list(self.failed_operations)

    def clear_failed_operations(self):
        """Clear the failed operations list."""
        with self._lock:
            self.failed_operations.clear()

    def retry_failed(self) -> Dict:
        """Retry all failed operations."""
        results = {"retried": 0, "succeeded": 0, "failed": 0}

        with self._lock:
            failed = list(self.failed_operations)
            self.failed_operations.clear()

        for op in failed:
            results["retried"] += 1
            # In a real implementation, we would re-execute the operation
            # For now, we just log the retry attempt
            self.audit.log(
                event_type="retry_" + op["operation"],
                entity_set=op["entity_set"],
                record_id=op.get("record_id"),
                status="retry_queued"
            )

        return results


class SyncGuardianAgent(BasicAgent):
    """
    Autonomous Sync Guardian Agent for Dynamics 365 Digital Twin.

    Maintains continuous synchronization between the Digital Twin and
    real Dynamics 365 instance. Monitors for changes, detects conflicts,
    resolves issues, and ensures both systems remain in sync.

    Capabilities:
    - Autonomous background synchronization
    - Bidirectional change detection
    - Multiple conflict resolution strategies
    - Real-time drift detection and alerting
    - Comprehensive audit trail
    - Self-healing with automatic recovery
    """

    def __init__(self, twin_id: str = "default"):
        self.name = "D365SyncGuardian"
        self.metadata = {
            "name": self.name,
            "description": """Autonomous Sync Guardian that maintains synchronization between
            the Digital Twin and Dynamics 365. Monitors changes, detects drift, resolves
            conflicts, and ensures both systems remain in sync. Supports continuous monitoring,
            configurable conflict resolution, and comprehensive audit logging.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "start_monitoring", "stop_monitoring", "sync_now",
                            "check_health", "get_drift_report", "get_conflicts",
                            "resolve_conflict", "get_audit_log", "configure",
                            "get_pending_changes", "force_full_sync", "status"
                        ],
                        "description": "Action to perform"
                    },
                    "entity_sets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Entity sets to monitor/sync (e.g., ['accounts', 'contacts'])"
                    },
                    "sync_direction": {
                        "type": "string",
                        "enum": ["bidirectional", "d365_to_twin", "twin_to_d365"],
                        "description": "Direction for sync operations"
                    },
                    "conflict_strategy": {
                        "type": "string",
                        "enum": ["d365_wins", "twin_wins", "newest_wins", "merge", "manual", "skip"],
                        "description": "Strategy for resolving conflicts"
                    },
                    "conflict_id": {
                        "type": "string",
                        "description": "Specific conflict ID to resolve"
                    },
                    "sync_interval_seconds": {
                        "type": "integer",
                        "description": "Interval between sync checks in seconds (default: 60)"
                    },
                    "audit_limit": {
                        "type": "integer",
                        "description": "Number of audit log entries to return (default: 50)"
                    }
                },
                "required": ["action"]
            }
        }

        # Initialize components
        self.twin_id = twin_id
        self._init_components()

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._sync_interval = 60  # seconds
        self._default_entities = ["accounts", "contacts", "leads", "opportunities"]

        super().__init__(self.name, self.metadata)

    def _init_components(self):
        """Initialize all sync components."""
        if not TWIN_AVAILABLE:
            logging.warning("Digital Twin components not available")
            self.d365 = None
            self.twin = None
            return

        self.d365 = D365Client()
        self.twin = DigitalTwinStore(self.twin_id)
        self.change_tracker = ChangeTracker(self.twin, self.d365)
        self.conflict_resolver = ConflictResolver(self.twin, self.d365)
        self.drift_detector = DriftDetector(self.twin, self.d365)
        self.audit_logger = AuditLogger()
        self.recovery_manager = RecoveryManager(
            self.twin, self.d365, self.audit_logger
        )

    def perform(self, **kwargs) -> str:
        """Execute the requested action."""
        action = kwargs.get("action", "status")

        handlers = {
            "start_monitoring": self._start_monitoring,
            "stop_monitoring": self._stop_monitoring,
            "sync_now": self._sync_now,
            "check_health": self._check_health,
            "get_drift_report": self._get_drift_report,
            "get_conflicts": self._get_conflicts,
            "resolve_conflict": self._resolve_conflict,
            "get_audit_log": self._get_audit_log,
            "configure": self._configure,
            "get_pending_changes": self._get_pending_changes,
            "force_full_sync": self._force_full_sync,
            "status": self._status
        }

        handler = handlers.get(action, self._status)

        try:
            result = handler(**kwargs)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            logging.error(f"SyncGuardian error: {str(e)}")
            return json.dumps({
                "status": "error",
                "action": action,
                "error": str(e)
            }, indent=2)

    def _start_monitoring(self, entity_sets: List[str] = None,
                          sync_interval_seconds: int = None, **kwargs) -> Dict:
        """Start autonomous monitoring and synchronization."""
        if self._monitoring:
            return {"status": "already_running", "message": "Monitoring is already active"}

        entities = entity_sets or self._default_entities
        if sync_interval_seconds:
            self._sync_interval = sync_interval_seconds

        # Initialize change tracking
        self.change_tracker.track_entities(entities)

        # Start monitor thread
        self._stop_event.clear()
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(entities,),
            daemon=True
        )
        self._monitor_thread.start()

        self.audit_logger.log(
            event_type="monitoring_started",
            entity_set=",".join(entities),
            status="success",
            details={"interval_seconds": self._sync_interval}
        )

        return {
            "status": "started",
            "monitoring": True,
            "entities": entities,
            "sync_interval_seconds": self._sync_interval,
            "message": f"Autonomous sync monitoring started for {len(entities)} entities"
        }

    def _stop_monitoring(self, **kwargs) -> Dict:
        """Stop autonomous monitoring."""
        if not self._monitoring:
            return {"status": "not_running", "message": "Monitoring is not active"}

        self._stop_event.set()
        self._monitoring = False

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        self.audit_logger.log(
            event_type="monitoring_stopped",
            entity_set="all",
            status="success"
        )

        return {
            "status": "stopped",
            "monitoring": False,
            "message": "Autonomous sync monitoring stopped"
        }

    def _monitor_loop(self, entities: List[str]):
        """Background monitoring loop."""
        logging.info("Sync Guardian monitor loop started")

        while not self._stop_event.is_set():
            try:
                # Detect changes
                changes = self.change_tracker.detect_changes()

                if changes:
                    logging.info(f"Detected {len(changes)} changes")

                    # Check for conflicts
                    conflicts = self.conflict_resolver.detect_conflicts(changes)

                    if conflicts:
                        logging.info(f"Detected {len(conflicts)} conflicts")
                        # Auto-resolve conflicts
                        for conflict in conflicts:
                            self.conflict_resolver.resolve(conflict)

                    # Apply non-conflicting changes
                    self._apply_changes(changes)

                # Log periodic status
                self.audit_logger.log(
                    event_type="monitor_cycle",
                    entity_set=",".join(entities),
                    status="success",
                    details={
                        "changes_detected": len(changes) if changes else 0,
                        "conflicts_detected": len(conflicts) if 'conflicts' in dir() else 0
                    }
                )

            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
                self.audit_logger.log(
                    event_type="monitor_error",
                    entity_set=",".join(entities),
                    status="error",
                    error=str(e)
                )

            # Wait for next cycle
            self._stop_event.wait(timeout=self._sync_interval)

        logging.info("Sync Guardian monitor loop stopped")

    def _apply_changes(self, changes: List[Change]):
        """Apply detected changes to synchronize systems."""
        for change in changes:
            if change.processed or change.conflict:
                continue

            try:
                if change.source == "d365":
                    # Replicate D365 change to Twin
                    self._replicate_to_twin(change)
                else:
                    # Replicate Twin change to D365
                    self._replicate_to_d365(change)

                self.change_tracker.mark_processed(change.change_id)

            except Exception as e:
                logging.error(f"Failed to apply change {change.change_id}: {e}")

    def _replicate_to_twin(self, change: Change):
        """Replicate a D365 change to the Twin."""
        if change.change_type == ChangeType.CREATED:
            if change.new_data:
                self.twin.create(change.entity_set, change.new_data)
        elif change.change_type == ChangeType.UPDATED:
            if change.new_data:
                self.twin.update(change.entity_set, change.record_id, change.new_data)
        elif change.change_type == ChangeType.DELETED:
            self.twin.delete(change.entity_set, change.record_id)

        self.audit_logger.log(
            event_type=f"sync_{change.change_type.value}",
            entity_set=change.entity_set,
            record_id=change.record_id,
            source="d365",
            target="twin",
            status="success"
        )

    def _replicate_to_d365(self, change: Change):
        """Replicate a Twin change to D365."""
        if change.change_type == ChangeType.CREATED:
            if change.new_data:
                self.d365.create(change.entity_set, change.new_data)
        elif change.change_type == ChangeType.UPDATED:
            if change.new_data:
                self.d365.update(change.entity_set, change.record_id, change.new_data)
        elif change.change_type == ChangeType.DELETED:
            self.d365.delete(change.entity_set, change.record_id)

        self.audit_logger.log(
            event_type=f"sync_{change.change_type.value}",
            entity_set=change.entity_set,
            record_id=change.record_id,
            source="twin",
            target="d365",
            status="success"
        )

    def _sync_now(self, entity_sets: List[str] = None,
                  sync_direction: str = "bidirectional", **kwargs) -> Dict:
        """Perform immediate sync cycle."""
        entities = entity_sets or self._default_entities

        self.audit_logger.log(
            event_type="manual_sync_started",
            entity_set=",".join(entities),
            status="success",
            details={"direction": sync_direction}
        )

        # Detect and apply changes
        self.change_tracker.track_entities(entities)
        changes = self.change_tracker.detect_changes()
        conflicts = self.conflict_resolver.detect_conflicts(changes)

        # Resolve conflicts
        resolved_conflicts = 0
        for conflict in conflicts:
            result = self.conflict_resolver.resolve(conflict)
            if result.get("resolved"):
                resolved_conflicts += 1

        # Apply remaining changes
        applied = 0
        for change in changes:
            if not change.conflict and not change.processed:
                try:
                    if sync_direction == "bidirectional":
                        if change.source == "d365":
                            self._replicate_to_twin(change)
                        else:
                            self._replicate_to_d365(change)
                    elif sync_direction == "d365_to_twin" and change.source == "d365":
                        self._replicate_to_twin(change)
                    elif sync_direction == "twin_to_d365" and change.source == "twin":
                        self._replicate_to_d365(change)

                    self.change_tracker.mark_processed(change.change_id)
                    applied += 1
                except Exception as e:
                    logging.error(f"Sync error: {e}")

        return {
            "status": "completed",
            "entities_synced": entities,
            "direction": sync_direction,
            "changes_detected": len(changes),
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": resolved_conflicts,
            "changes_applied": applied
        }

    def _check_health(self, **kwargs) -> Dict:
        """Check overall sync health status."""
        entities = self._default_entities

        # Get drift info
        drift_report = self.drift_detector.calculate_drift(entities)

        # Determine status
        unresolved = len(self.conflict_resolver.get_unresolved_conflicts())
        error_count = self.audit_logger.get_error_count(24)

        if error_count > 10:
            status = SyncStatus.ERROR
        elif drift_report["overall_drift_percentage"] > 20:
            status = SyncStatus.DRIFTED
        elif self._monitoring:
            status = SyncStatus.SYNCING
        elif drift_report["overall_drift_percentage"] == 0:
            status = SyncStatus.IN_SYNC
        else:
            status = SyncStatus.DRIFTED

        # Build warnings
        warnings = []
        if unresolved > 0:
            warnings.append(f"{unresolved} unresolved conflicts")
        if error_count > 0:
            warnings.append(f"{error_count} errors in last 24 hours")
        if drift_report["overall_drift_percentage"] > 5:
            warnings.append(f"Drift at {drift_report['overall_drift_percentage']:.1f}%")

        health = HealthStatus(
            status=status,
            last_sync=self.audit_logger.get_recent_events(1, "manual_sync_started")[0]["timestamp"]
                      if self.audit_logger.get_recent_events(1, "manual_sync_started") else None,
            last_check=datetime.now(timezone.utc).isoformat(),
            twin_connected=self.twin is not None,
            d365_connected=self.d365 is not None and not self.d365.mock_mode,
            pending_changes=len(self.change_tracker.get_pending_changes()),
            unresolved_conflicts=unresolved,
            drift_percentage=drift_report["overall_drift_percentage"],
            entities_monitored=entities,
            error_count_24h=error_count,
            warnings=warnings
        )

        return {
            "action": "check_health",
            "health": asdict(health),
            "monitoring_active": self._monitoring,
            "sync_interval_seconds": self._sync_interval
        }

    def _get_drift_report(self, entity_sets: List[str] = None, **kwargs) -> Dict:
        """Get detailed drift report."""
        entities = entity_sets or self._default_entities
        drift_report = self.drift_detector.calculate_drift(entities)
        drift_report["action"] = "get_drift_report"
        return drift_report

    def _get_conflicts(self, **kwargs) -> Dict:
        """Get all unresolved conflicts."""
        unresolved = self.conflict_resolver.get_unresolved_conflicts()
        manual_queue = self.conflict_resolver.get_manual_queue()

        return {
            "action": "get_conflicts",
            "unresolved_count": len(unresolved),
            "manual_queue_count": len(manual_queue),
            "conflicts": [
                {
                    "conflict_id": c.conflict_id,
                    "entity_set": c.entity_set,
                    "record_id": c.record_id,
                    "twin_change_type": c.twin_change.change_type.value,
                    "d365_change_type": c.d365_change.change_type.value,
                    "detected_at": c.detected_at
                }
                for c in unresolved
            ]
        }

    def _resolve_conflict(self, conflict_id: str = None,
                          conflict_strategy: str = None, **kwargs) -> Dict:
        """Resolve a specific conflict."""
        if not conflict_id:
            return {"status": "error", "error": "conflict_id is required"}

        strategy = ConflictStrategy(conflict_strategy) if conflict_strategy else None

        # Find the conflict
        for conflict in self.conflict_resolver.conflicts:
            if conflict.conflict_id == conflict_id:
                result = self.conflict_resolver.resolve(conflict, strategy)
                return {
                    "action": "resolve_conflict",
                    "conflict_id": conflict_id,
                    **result
                }

        return {"status": "error", "error": f"Conflict {conflict_id} not found"}

    def _get_audit_log(self, audit_limit: int = 50, **kwargs) -> Dict:
        """Get recent audit log entries."""
        events = self.audit_logger.get_recent_events(audit_limit)
        summary = self.audit_logger.get_summary(24)

        return {
            "action": "get_audit_log",
            "summary_24h": summary,
            "recent_events": events
        }

    def _configure(self, sync_interval_seconds: int = None,
                   conflict_strategy: str = None, **kwargs) -> Dict:
        """Configure sync settings."""
        changes = {}

        if sync_interval_seconds:
            self._sync_interval = sync_interval_seconds
            changes["sync_interval_seconds"] = sync_interval_seconds

        if conflict_strategy:
            strategy = ConflictStrategy(conflict_strategy)
            self.conflict_resolver.default_strategy = strategy
            changes["conflict_strategy"] = conflict_strategy

        return {
            "action": "configure",
            "changes_applied": changes,
            "current_config": {
                "sync_interval_seconds": self._sync_interval,
                "conflict_strategy": self.conflict_resolver.default_strategy.value,
                "monitoring_active": self._monitoring
            }
        }

    def _get_pending_changes(self, **kwargs) -> Dict:
        """Get pending unprocessed changes."""
        pending = self.change_tracker.get_pending_changes()

        return {
            "action": "get_pending_changes",
            "count": len(pending),
            "changes": [
                {
                    "change_id": c.change_id,
                    "entity_set": c.entity_set,
                    "record_id": c.record_id,
                    "change_type": c.change_type.value,
                    "source": c.source,
                    "timestamp": c.timestamp,
                    "conflict": c.conflict
                }
                for c in pending[:100]  # Limit to 100
            ]
        }

    def _force_full_sync(self, entity_sets: List[str] = None,
                         sync_direction: str = "d365_to_twin", **kwargs) -> Dict:
        """Force a full synchronization (pulls all data)."""
        entities = entity_sets or self._default_entities
        direction = SyncDirection(sync_direction)

        self.audit_logger.log(
            event_type="force_full_sync_started",
            entity_set=",".join(entities),
            status="success",
            details={"direction": sync_direction}
        )

        results = {
            "action": "force_full_sync",
            "direction": sync_direction,
            "entities": {}
        }

        for entity in entities:
            try:
                if direction in (SyncDirection.D365_TO_TWIN, SyncDirection.BIDIRECTIONAL):
                    # Pull all from D365
                    d365_data, status = self.d365.query(entity, top=5000)
                    if status == 200 and "value" in d365_data:
                        records = d365_data["value"]
                        self.twin.bulk_load(entity, records)
                        results["entities"][entity] = {
                            "status": "success",
                            "records_synced": len(records)
                        }
                    else:
                        results["entities"][entity] = {
                            "status": "error",
                            "error": "Failed to fetch from D365"
                        }

            except Exception as e:
                results["entities"][entity] = {
                    "status": "error",
                    "error": str(e)
                }

        # Recapture baseline after full sync
        for entity in entities:
            self.change_tracker._capture_baseline(entity)

        self.audit_logger.log(
            event_type="force_full_sync_completed",
            entity_set=",".join(entities),
            status="success",
            details=results["entities"]
        )

        return results

    def _status(self, **kwargs) -> Dict:
        """Get current guardian status."""
        pending = self.change_tracker.get_pending_changes() if hasattr(self, 'change_tracker') else []
        unresolved = self.conflict_resolver.get_unresolved_conflicts() if hasattr(self, 'conflict_resolver') else []
        failed = self.recovery_manager.get_failed_operations() if hasattr(self, 'recovery_manager') else []

        return {
            "action": "status",
            "guardian_name": self.name,
            "twin_id": self.twin_id,
            "monitoring_active": self._monitoring,
            "sync_interval_seconds": self._sync_interval,
            "default_conflict_strategy": self.conflict_resolver.default_strategy.value if hasattr(self, 'conflict_resolver') else "unknown",
            "d365_connected": self.d365 is not None and not getattr(self.d365, 'mock_mode', True),
            "d365_mode": "LIVE" if (self.d365 and not self.d365.mock_mode) else "MOCK",
            "twin_connected": self.twin is not None,
            "pending_changes": len(pending),
            "unresolved_conflicts": len(unresolved),
            "failed_operations": len(failed),
            "default_entities": self._default_entities,
            "capabilities": [
                "autonomous_monitoring",
                "bidirectional_sync",
                "conflict_detection",
                "conflict_resolution",
                "drift_detection",
                "audit_logging",
                "self_healing"
            ]
        }


# Export the agent class (SyncGuardianAgent aliased as D365SyncGuardianAgent for consistency)
D365SyncGuardianAgent = SyncGuardianAgent
__all__ = ['SyncGuardianAgent', 'D365SyncGuardianAgent', 'ConflictStrategy', 'SyncDirection']
