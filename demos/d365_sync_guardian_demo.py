#!/usr/bin/env python3
"""
Dynamics 365 Sync Guardian Demo

Demonstrates the autonomous Sync Guardian agent that maintains synchronization
between the Digital Twin and Dynamics 365. Shows:

1. Starting autonomous monitoring
2. Change detection in both systems
3. Conflict detection and resolution
4. Drift detection and health monitoring
5. Audit logging and recovery
6. Manual sync operations

Usage:
    python d365_sync_guardian_demo.py

The demo runs in mock mode by default, simulating changes and conflicts
to demonstrate the full capability of the Sync Guardian.
"""

import sys
import os
import json
import time
import threading
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.d365_sync_guardian_agent import D365SyncGuardianAgent, ConflictStrategy
from experimental.d365_digital_twin_agent import D365DigitalTwinAgent


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def print_result(result: str, max_lines: int = 40):
    """Print JSON result with optional truncation."""
    try:
        data = json.loads(result)
        formatted = json.dumps(data, indent=2)
        lines = formatted.split('\n')
        if len(lines) > max_lines:
            print('\n'.join(lines[:max_lines]))
            print(f"\n... ({len(lines) - max_lines} more lines)")
        else:
            print(formatted)
    except:
        print(result)


def simulate_changes(twin_agent: D365DigitalTwinAgent):
    """Simulate changes in both systems to trigger sync."""
    print_subheader("Simulating Changes in Both Systems")

    # Create some records in the twin only (simulates local changes)
    print("\n[Creating records in Digital Twin only...]")
    twin_agent.perform(
        operation="create",
        entity_set="accounts",
        data={
            "name": "Twin-Side Corp",
            "telephone1": "+1-555-TWIN",
            "description": "Created in Twin - should sync to D365"
        },
        twin_only=True
    )

    twin_agent.perform(
        operation="create",
        entity_set="contacts",
        data={
            "firstname": "Twin",
            "lastname": "Created",
            "emailaddress1": "twin.created@example.com"
        },
        twin_only=True
    )

    print("  - Created 'Twin-Side Corp' account")
    print("  - Created 'Twin Created' contact")


def demo_guardian_status(guardian: D365SyncGuardianAgent):
    """Check guardian status."""
    print_header("1. SYNC GUARDIAN STATUS")
    print("Checking the current state of the Sync Guardian...")

    result = guardian.perform(action="status")
    print_result(result)


def demo_start_monitoring(guardian: D365SyncGuardianAgent):
    """Start autonomous monitoring."""
    print_header("2. START AUTONOMOUS MONITORING")
    print("Starting the Sync Guardian to autonomously monitor and sync changes...")
    print("The guardian will run in the background, detecting changes every 5 seconds.")

    result = guardian.perform(
        action="start_monitoring",
        entity_sets=["accounts", "contacts", "leads", "opportunities"],
        sync_interval_seconds=5  # Fast interval for demo
    )
    print_result(result)


def demo_health_check(guardian: D365SyncGuardianAgent):
    """Check sync health."""
    print_header("3. HEALTH CHECK")
    print("Checking overall sync health status...")
    print("This shows sync status, drift, conflicts, and any warnings.")

    result = guardian.perform(action="check_health")
    print_result(result)


def demo_drift_report(guardian: D365SyncGuardianAgent):
    """Get drift report."""
    print_header("4. DRIFT DETECTION REPORT")
    print("Analyzing synchronization drift between systems...")
    print("This compares record counts and field values.")

    result = guardian.perform(
        action="get_drift_report",
        entity_sets=["accounts", "contacts"]
    )
    print_result(result)


def demo_manual_sync(guardian: D365SyncGuardianAgent):
    """Perform manual sync."""
    print_header("5. MANUAL SYNC OPERATION")
    print("Triggering immediate bidirectional sync...")

    result = guardian.perform(
        action="sync_now",
        entity_sets=["accounts", "contacts"],
        sync_direction="bidirectional"
    )
    print_result(result)


def demo_pending_changes(guardian: D365SyncGuardianAgent):
    """Get pending changes."""
    print_header("6. PENDING CHANGES")
    print("Showing changes detected but not yet processed...")

    result = guardian.perform(action="get_pending_changes")
    print_result(result)


def demo_conflicts(guardian: D365SyncGuardianAgent):
    """Get conflicts."""
    print_header("7. CONFLICT DETECTION")
    print("Showing any detected conflicts between systems...")

    result = guardian.perform(action="get_conflicts")
    print_result(result)


def demo_configure(guardian: D365SyncGuardianAgent):
    """Configure guardian settings."""
    print_header("8. CONFIGURE SYNC SETTINGS")
    print("Changing conflict resolution strategy to 'newest_wins'...")

    result = guardian.perform(
        action="configure",
        conflict_strategy="newest_wins",
        sync_interval_seconds=10
    )
    print_result(result)


def demo_audit_log(guardian: D365SyncGuardianAgent):
    """Get audit log."""
    print_header("9. AUDIT LOG")
    print("Showing recent sync audit events...")

    result = guardian.perform(
        action="get_audit_log",
        audit_limit=20
    )
    print_result(result)


def demo_force_full_sync(guardian: D365SyncGuardianAgent):
    """Force full sync."""
    print_header("10. FORCE FULL SYNC")
    print("Forcing a complete sync of all records from D365 to Twin...")
    print("This pulls ALL data, not just changes.")

    result = guardian.perform(
        action="force_full_sync",
        entity_sets=["accounts"],
        sync_direction="d365_to_twin"
    )
    print_result(result)


def demo_stop_monitoring(guardian: D365SyncGuardianAgent):
    """Stop autonomous monitoring."""
    print_header("11. STOP MONITORING")
    print("Stopping the autonomous sync guardian...")

    result = guardian.perform(action="stop_monitoring")
    print_result(result)


def demo_final_health(guardian: D365SyncGuardianAgent):
    """Final health check."""
    print_header("12. FINAL HEALTH CHECK")
    print("Final system health after all operations...")

    result = guardian.perform(action="check_health")
    print_result(result)


def demo_conflict_resolution_strategies():
    """Explain conflict resolution strategies."""
    print_header("CONFLICT RESOLUTION STRATEGIES")
    print("""
The Sync Guardian supports multiple strategies for handling conflicts
when the same record is modified in both systems:

  d365_wins   - Real D365 always takes precedence
                Use when D365 is the system of record

  twin_wins   - Digital Twin always takes precedence
                Use when Twin has authoritative changes

  newest_wins - Most recently modified record wins
                Use for general-purpose sync (DEFAULT)

  merge       - Attempt to merge non-conflicting field changes
                Use when different fields changed in each system

  manual      - Queue for manual review
                Use for critical data requiring human oversight

  skip        - Skip conflicting records without action
                Use when conflicts should be ignored temporarily

Configure with:
  guardian.perform(action="configure", conflict_strategy="merge")
""")


def main():
    """Run the Sync Guardian demo."""
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + "       DYNAMICS 365 SYNC GUARDIAN DEMONSTRATION".center(68) + "#")
    print("#" + " " * 68 + "#")
    print("#" + "    Autonomous synchronization between Digital Twin and D365".center(68) + "#")
    print("#" + " " * 68 + "#")
    print("#" * 70)

    # Check environment
    print("\n[ENVIRONMENT CHECK]")
    if os.environ.get('D365_URL'):
        print(f"  D365 URL: {os.environ.get('D365_URL')}")
        print("  Mode: LIVE D365 CONNECTION")
    else:
        print("  D365 URL: Not configured")
        print("  Mode: MOCK MODE (demonstrating architecture without real D365)")

    # Initialize agents
    print("\n[INITIALIZING AGENTS]")

    # Digital Twin agent for creating test data
    twin_agent = D365DigitalTwinAgent(twin_id="guardian_demo_twin")
    print("  - Digital Twin Agent initialized")

    # Sync Guardian agent
    guardian = D365SyncGuardianAgent(twin_id="guardian_demo_twin")
    print("  - Sync Guardian Agent initialized")

    # Run demo sequence
    demo_guardian_status(guardian)

    # Simulate some data first
    print_header("CREATING TEST DATA")
    print("Creating initial records in the Digital Twin...")

    twin_agent.perform(
        operation="create",
        entity_set="accounts",
        data={"name": "Demo Corp", "telephone1": "+1-555-0001"}
    )
    twin_agent.perform(
        operation="create",
        entity_set="contacts",
        data={"firstname": "Demo", "lastname": "User", "emailaddress1": "demo@example.com"}
    )
    print("  - Created initial test records")

    # Start monitoring
    demo_start_monitoring(guardian)

    # Let it run for a moment
    print("\n[Letting guardian monitor for 3 seconds...]")
    time.sleep(3)

    # Simulate changes
    simulate_changes(twin_agent)

    # Let sync detect changes
    print("\n[Waiting for change detection...]")
    time.sleep(3)

    # Check health
    demo_health_check(guardian)

    # Get drift report
    demo_drift_report(guardian)

    # Manual sync
    demo_manual_sync(guardian)

    # Check pending changes
    demo_pending_changes(guardian)

    # Check conflicts
    demo_conflicts(guardian)

    # Configure settings
    demo_configure(guardian)

    # Get audit log
    demo_audit_log(guardian)

    # Force full sync
    demo_force_full_sync(guardian)

    # Stop monitoring
    demo_stop_monitoring(guardian)

    # Final health check
    demo_final_health(guardian)

    # Show conflict resolution strategies
    demo_conflict_resolution_strategies()

    # Summary
    print_header("DEMO COMPLETE")
    print("""
The Sync Guardian Agent demonstrated:

 1. AUTONOMOUS MONITORING
    - Background thread continuously monitors both systems
    - Configurable sync interval (default 60s, demo used 5s)

 2. CHANGE DETECTION
    - Tracks changes in both Digital Twin and D365
    - Uses checksums to detect modifications
    - Identifies creates, updates, and deletes

 3. CONFLICT RESOLUTION
    - Detects when same record changed in both systems
    - Multiple resolution strategies available
    - Automatic or manual resolution options

 4. DRIFT DETECTION
    - Calculates drift percentage between systems
    - Identifies records only in one system
    - Reports field-level differences

 5. HEALTH MONITORING
    - Overall sync status (IN_SYNC, DRIFTED, ERROR)
    - Connection status for both systems
    - Warning aggregation

 6. AUDIT LOGGING
    - Complete history of all sync operations
    - Error tracking and retry management
    - 24-hour summaries

 7. SELF-HEALING
    - Automatic retry on failures
    - Recovery manager for failed operations
    - Graceful error handling

The guardian ensures your Digital Twin and D365 remain perfectly synchronized!
""")


if __name__ == "__main__":
    main()
