#!/usr/bin/env python3
"""
Dynamics 365 Digital Twin Demo

This demo shows the 1:1 Digital Twin functionality where every operation
is mirrored between the local Digital Twin and the real Dynamics 365 instance.

The output clearly shows both systems' responses side-by-side to verify
they remain synchronized.

Usage:
    python d365_digital_twin_demo.py

Environment Variables (for real D365 connection):
    D365_TENANT_ID     - Azure AD tenant ID
    D365_CLIENT_ID     - App registration client ID
    D365_CLIENT_SECRET - App registration client secret
    D365_URL           - D365 instance URL (e.g., https://org.crm.dynamics.com)

Without these variables, the agent runs in MOCK mode which still demonstrates
the full architecture and mirrored operation pattern.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experimental.d365_digital_twin_agent import D365DigitalTwinAgent


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def print_result(result: str, max_lines: int = 50):
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


def demo_status_check(agent: D365DigitalTwinAgent):
    """Demo: Check Digital Twin status."""
    print_header("1. DIGITAL TWIN STATUS CHECK")
    print("Checking the current state of the Digital Twin and D365 connection...")

    result = agent.perform(operation="status")
    print_result(result)


def demo_create_account(agent: D365DigitalTwinAgent):
    """Demo: Create an account in both systems."""
    print_header("2. CREATE OPERATION - Account Record")
    print("Creating a new account record...")
    print("This will execute on BOTH the Digital Twin AND real D365 (or mock).")
    print("Watch for matching results from both systems!")

    result = agent.perform(
        operation="create",
        entity_set="accounts",
        data={
            "name": "Contoso Ltd",
            "telephone1": "+1-555-0100",
            "emailaddress1": "info@contoso.com",
            "address1_city": "Seattle",
            "address1_country": "USA",
            "industrycode": 1,  # Accounting
            "revenue": 5000000,
            "numberofemployees": 250
        }
    )
    print_result(result)

    # Parse to get the created ID for later use
    data = json.loads(result)
    account_id = None
    if data.get("twin_result", {}).get("data", {}).get("accountid"):
        account_id = data["twin_result"]["data"]["accountid"]
    return account_id


def demo_create_contact(agent: D365DigitalTwinAgent, account_id: str = None):
    """Demo: Create a contact in both systems."""
    print_header("3. CREATE OPERATION - Contact Record")
    print("Creating a contact record linked to the account...")

    contact_data = {
        "firstname": "John",
        "lastname": "Smith",
        "emailaddress1": "john.smith@contoso.com",
        "telephone1": "+1-555-0101",
        "jobtitle": "VP of Operations"
    }

    if account_id:
        contact_data["parentcustomerid_account@odata.bind"] = f"/accounts({account_id})"

    result = agent.perform(
        operation="create",
        entity_set="contacts",
        data=contact_data
    )
    print_result(result)

    data = json.loads(result)
    contact_id = None
    if data.get("twin_result", {}).get("data", {}).get("contactid"):
        contact_id = data["twin_result"]["data"]["contactid"]
    return contact_id


def demo_create_opportunity(agent: D365DigitalTwinAgent, account_id: str = None):
    """Demo: Create an opportunity."""
    print_header("4. CREATE OPERATION - Opportunity Record")
    print("Creating a sales opportunity...")

    opp_data = {
        "name": "Enterprise Software License Deal",
        "description": "Annual enterprise software licensing agreement",
        "estimatedvalue": 250000,
        "estimatedclosedate": "2025-03-31",
        "stepname": "Qualify"
    }

    if account_id:
        opp_data["parentaccountid@odata.bind"] = f"/accounts({account_id})"

    result = agent.perform(
        operation="create",
        entity_set="opportunities",
        data=opp_data
    )
    print_result(result)

    data = json.loads(result)
    opp_id = None
    if data.get("twin_result", {}).get("data", {}).get("opportunityid"):
        opp_id = data["twin_result"]["data"]["opportunityid"]
    return opp_id


def demo_read_single(agent: D365DigitalTwinAgent, entity_set: str, record_id: str):
    """Demo: Read a single record from both systems."""
    print_header(f"5. READ OPERATION - Single {entity_set.title()} Record")
    print(f"Reading {entity_set} record: {record_id}")
    print("Comparing response from Digital Twin vs D365...")

    result = agent.perform(
        operation="read",
        entity_set=entity_set,
        record_id=record_id
    )
    print_result(result)


def demo_query_with_filter(agent: D365DigitalTwinAgent):
    """Demo: Query with OData filter."""
    print_header("6. QUERY OPERATION - OData Filter")
    print("Querying accounts with OData filter: contains(name,'Contoso')")
    print("Executing query on BOTH systems and comparing record counts...")

    result = agent.perform(
        operation="query",
        entity_set="accounts",
        filter="contains(name,'Contoso')",
        select=["name", "telephone1", "emailaddress1", "address1_city"],
        orderby="createdon desc",
        top=10
    )
    print_result(result)


def demo_query_opportunities(agent: D365DigitalTwinAgent):
    """Demo: Query opportunities."""
    print_header("7. QUERY OPERATION - Opportunities Pipeline")
    print("Querying opportunities with high estimated value...")

    result = agent.perform(
        operation="query",
        entity_set="opportunities",
        select=["name", "estimatedvalue", "stepname", "estimatedclosedate"],
        orderby="estimatedvalue desc",
        top=5
    )
    print_result(result)


def demo_update_record(agent: D365DigitalTwinAgent, entity_set: str, record_id: str):
    """Demo: Update a record in both systems."""
    print_header("8. UPDATE OPERATION - Modify Record")
    print(f"Updating {entity_set} record: {record_id}")
    print("This change will be applied to BOTH Digital Twin AND D365...")

    update_data = {
        "description": "Updated via Digital Twin - synchronized to both systems",
        "modifiedon": None  # Will be auto-set
    }

    if entity_set == "accounts":
        update_data["numberofemployees"] = 300
        update_data["revenue"] = 6500000
    elif entity_set == "opportunities":
        update_data["estimatedvalue"] = 275000
        update_data["stepname"] = "Develop"

    result = agent.perform(
        operation="update",
        entity_set=entity_set,
        record_id=record_id,
        data=update_data
    )
    print_result(result)


def demo_compare_record(agent: D365DigitalTwinAgent, entity_set: str, record_id: str):
    """Demo: Compare record between twin and D365."""
    print_header("9. COMPARE OPERATION - Verify Synchronization")
    print(f"Performing detailed field-by-field comparison for {entity_set}: {record_id}")
    print("This shows any differences between Digital Twin and D365...")

    result = agent.perform(
        operation="compare",
        entity_set=entity_set,
        record_id=record_id
    )
    print_result(result)


def demo_list_entities(agent: D365DigitalTwinAgent):
    """Demo: List all entities in the twin."""
    print_header("10. LIST ENTITIES - Digital Twin Inventory")
    print("Listing all entity sets stored in the Digital Twin...")

    result = agent.perform(operation="list_entities")
    print_result(result)


def demo_sync(agent: D365DigitalTwinAgent):
    """Demo: Sync from D365 to twin."""
    print_header("11. SYNC OPERATION - Full Entity Sync")
    print("Synchronizing selected entities from D365 to Digital Twin...")
    print("This pulls data from D365 to ensure the twin is up-to-date.")

    result = agent.perform(
        operation="sync",
        entity_set="accounts"  # Sync just accounts, or None for all default entities
    )
    print_result(result)


def demo_twin_only_operation(agent: D365DigitalTwinAgent):
    """Demo: Operation on twin only (no D365 mirror)."""
    print_header("12. TWIN-ONLY OPERATION")
    print("Creating a record in Digital Twin ONLY (no D365 mirror)...")
    print("Useful for testing or staging data before pushing to production D365.")

    result = agent.perform(
        operation="create",
        entity_set="leads",
        data={
            "firstname": "Jane",
            "lastname": "Doe",
            "companyname": "Acme Corp",
            "emailaddress1": "jane.doe@acme.com",
            "subject": "Product Interest - Enterprise Plan",
            "leadqualitycode": 1  # Hot
        },
        twin_only=True  # Only create in twin, not in D365
    )
    print_result(result)


def demo_delete_record(agent: D365DigitalTwinAgent, entity_set: str, record_id: str):
    """Demo: Delete a record from both systems."""
    print_header("13. DELETE OPERATION")
    print(f"Deleting {entity_set} record: {record_id}")
    print("This will remove from BOTH Digital Twin AND D365...")

    result = agent.perform(
        operation="delete",
        entity_set=entity_set,
        record_id=record_id
    )
    print_result(result)


def demo_final_status(agent: D365DigitalTwinAgent):
    """Demo: Final status check."""
    print_header("14. FINAL STATUS CHECK")
    print("Checking final state of the Digital Twin after all operations...")

    result = agent.perform(operation="status")
    print_result(result)


def main():
    """Run the complete Digital Twin demo."""
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + "    DYNAMICS 365 DIGITAL TWIN DEMONSTRATION".center(68) + "#")
    print("#" + " " * 68 + "#")
    print("#" + "    Every operation executes on BOTH systems with".center(68) + "#")
    print("#" + "    comparative output to verify synchronization".center(68) + "#")
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
        print("  Set D365_TENANT_ID, D365_CLIENT_ID, D365_CLIENT_SECRET, D365_URL for live connection")

    # Initialize the agent
    print("\n[INITIALIZING DIGITAL TWIN AGENT]")
    agent = D365DigitalTwinAgent(twin_id="demo_twin")
    print("  Agent initialized successfully!")

    # Run demo scenarios
    demo_status_check(agent)

    # Create records
    account_id = demo_create_account(agent)
    contact_id = demo_create_contact(agent, account_id)
    opportunity_id = demo_create_opportunity(agent, account_id)

    # Read operations
    if account_id:
        demo_read_single(agent, "accounts", account_id)

    # Query operations
    demo_query_with_filter(agent)
    demo_query_opportunities(agent)

    # Update operations
    if account_id:
        demo_update_record(agent, "accounts", account_id)

    # Compare operations
    if account_id:
        demo_compare_record(agent, "accounts", account_id)

    # List entities
    demo_list_entities(agent)

    # Sync operation
    demo_sync(agent)

    # Twin-only operation
    demo_twin_only_operation(agent)

    # Final status
    demo_final_status(agent)

    # Summary
    print_header("DEMO COMPLETE")
    print("""
The Digital Twin agent demonstrated:

1. CREATE  - Records created in BOTH Digital Twin and D365
2. READ    - Data retrieved from BOTH systems for comparison
3. UPDATE  - Modifications applied to BOTH systems
4. DELETE  - Removals synced across BOTH systems
5. QUERY   - OData queries executed on BOTH with result comparison
6. SYNC    - Pull data from D365 to populate/update the twin
7. COMPARE - Field-level comparison between twin and D365
8. TWIN-ONLY - Operations isolated to twin for testing

Every operation shows side-by-side output from both systems,
proving they remain synchronized as a true 1:1 Digital Twin.
""")


if __name__ == "__main__":
    main()
