"""
Trade Reconciliation Agent - Capital Markets MVP
Generated via RAPP Pipeline Process

Customer: Meridian Capital Partners (Sample)
Industry: Capital Markets / Investment Banking
Use Case: Automated trade break detection and resolution

Problem Statement:
- Manual trade reconciliation takes 4-5 hours daily with team of 12 analysts
- Failed trades resulted in $47,000 quarterly penalties
- High analyst turnover due to repetitive manual work

Success Criteria:
- Reduce reconciliation time from 4-5 hours to 30 minutes
- Achieve 90% auto-resolution rate for trade breaks
- Full audit trail for SEC/FINRA compliance

Data Sources:
- Charles River OMS (Order Management System)
- DTCC Clearing Reports
- Prime Broker APIs (Goldman Sachs, Morgan Stanley, JP Morgan)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class TradeReconciliationAgent(BasicAgent):
    """
    AI-powered trade reconciliation agent for capital markets operations.

    Capabilities:
    - Compare trades across OMS, clearing, and prime broker systems
    - Identify trade breaks with root cause analysis
    - Suggest automatic resolutions for common break types
    - Generate compliance-ready audit reports
    - Track resolution metrics and SLA compliance
    """

    def __init__(self):
        self.name = 'TradeReconciliation'
        self.metadata = {
            "name": self.name,
            "description": "Automates trade reconciliation across OMS, clearing, and prime broker systems. Identifies breaks, suggests resolutions, and maintains compliance audit trails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "reconcile_daily",
                            "analyze_break",
                            "suggest_resolution",
                            "get_break_summary",
                            "generate_audit_report",
                            "check_sla_status"
                        ],
                        "description": "Action to perform"
                    },
                    "trade_date": {
                        "type": "string",
                        "description": "Trade date in YYYY-MM-DD format (defaults to today)"
                    },
                    "break_id": {
                        "type": "string",
                        "description": "Specific break ID to analyze or resolve"
                    },
                    "system_filter": {
                        "type": "string",
                        "enum": ["OMS", "DTCC", "PRIME_BROKER", "ALL"],
                        "description": "Filter by source system"
                    },
                    "severity_filter": {
                        "type": "string",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "ALL"],
                        "description": "Filter by break severity"
                    },
                    "include_resolved": {
                        "type": "boolean",
                        "description": "Include already resolved breaks in results"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Break type definitions with auto-resolution rules
        self.break_types = {
            "QUANTITY_MISMATCH": {
                "description": "Trade quantity differs between systems",
                "auto_resolvable": True,
                "resolution_rule": "Use OMS quantity as source of truth if within 0.1% variance"
            },
            "PRICE_VARIANCE": {
                "description": "Execution price varies beyond tolerance",
                "auto_resolvable": True,
                "resolution_rule": "Accept clearing price if variance < $0.01 per share"
            },
            "SETTLEMENT_DATE_MISMATCH": {
                "description": "Settlement dates don't align across systems",
                "auto_resolvable": False,
                "resolution_rule": "Requires manual review - potential T+1/T+2 confusion"
            },
            "MISSING_TRADE": {
                "description": "Trade exists in one system but not another",
                "auto_resolvable": False,
                "resolution_rule": "Check for late reporting, cancellations, or data feed issues"
            },
            "COUNTERPARTY_MISMATCH": {
                "description": "Counterparty identification differs",
                "auto_resolvable": True,
                "resolution_rule": "Match on LEI code, fallback to DTCC participant ID"
            },
            "COMMISSION_VARIANCE": {
                "description": "Commission amounts don't match",
                "auto_resolvable": True,
                "resolution_rule": "Accept prime broker commission if variance < 1%"
            }
        }

        # Prime broker configurations
        self.prime_brokers = {
            "GS": {"name": "Goldman Sachs", "participant_id": "GSPB001"},
            "MS": {"name": "Morgan Stanley", "participant_id": "MSPB002"},
            "JPM": {"name": "JP Morgan", "participant_id": "JPMPB003"}
        }

    def perform(self, **kwargs) -> str:
        """Execute the requested trade reconciliation action."""
        action = kwargs.get('action', 'get_break_summary')
        trade_date = kwargs.get('trade_date', datetime.now().strftime('%Y-%m-%d'))

        logger.info(f"TradeReconciliationAgent performing action: {action} for date: {trade_date}")

        try:
            if action == 'reconcile_daily':
                return self._reconcile_daily(trade_date, kwargs)
            elif action == 'analyze_break':
                return self._analyze_break(kwargs.get('break_id'), kwargs)
            elif action == 'suggest_resolution':
                return self._suggest_resolution(kwargs.get('break_id'), kwargs)
            elif action == 'get_break_summary':
                return self._get_break_summary(trade_date, kwargs)
            elif action == 'generate_audit_report':
                return self._generate_audit_report(trade_date, kwargs)
            elif action == 'check_sla_status':
                return self._check_sla_status(trade_date)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}"
                })
        except Exception as e:
            logger.error(f"TradeReconciliationAgent error: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def _reconcile_daily(self, trade_date: str, params: Dict) -> str:
        """Run full daily reconciliation across all systems."""

        # Simulate fetching data from multiple systems
        oms_trades = self._fetch_oms_trades(trade_date)
        dtcc_trades = self._fetch_dtcc_trades(trade_date)
        pb_trades = self._fetch_prime_broker_trades(trade_date)

        # Perform three-way reconciliation
        breaks = self._compare_trades(oms_trades, dtcc_trades, pb_trades)

        # Attempt auto-resolution where possible
        auto_resolved = []
        requires_review = []

        for break_item in breaks:
            break_type = self.break_types.get(break_item['type'])
            if break_type and break_type['auto_resolvable']:
                resolution = self._attempt_auto_resolution(break_item)
                if resolution['resolved']:
                    auto_resolved.append({**break_item, 'resolution': resolution})
                else:
                    requires_review.append(break_item)
            else:
                requires_review.append(break_item)

        # Calculate metrics
        total_trades = len(oms_trades)
        total_breaks = len(breaks)
        auto_resolution_rate = (len(auto_resolved) / total_breaks * 100) if total_breaks > 0 else 100

        return json.dumps({
            "status": "success",
            "reconciliation_date": trade_date,
            "summary": {
                "total_trades_processed": total_trades,
                "total_breaks_identified": total_breaks,
                "auto_resolved": len(auto_resolved),
                "requires_manual_review": len(requires_review),
                "auto_resolution_rate": f"{auto_resolution_rate:.1f}%"
            },
            "auto_resolved_breaks": auto_resolved[:5],  # Show sample
            "breaks_requiring_review": requires_review,
            "processing_time_minutes": 2.3,  # Simulated
            "compliance_status": "AUDIT_TRAIL_COMPLETE",
            "sla_status": "WITHIN_TARGET" if len(requires_review) < 10 else "AT_RISK"
        }, indent=2)

    def _analyze_break(self, break_id: str, params: Dict) -> str:
        """Perform detailed analysis of a specific trade break."""

        if not break_id:
            return json.dumps({
                "status": "error",
                "message": "break_id is required for analysis"
            })

        # Simulate break analysis
        break_detail = {
            "break_id": break_id,
            "identified_at": datetime.now().isoformat(),
            "trade_details": {
                "oms_record": {
                    "trade_id": "CR-2026-001234",
                    "symbol": "AAPL",
                    "quantity": 10000,
                    "price": 178.52,
                    "side": "BUY",
                    "execution_time": "2026-01-15T14:32:15Z"
                },
                "dtcc_record": {
                    "trade_id": "DTCC-2026-789012",
                    "symbol": "AAPL",
                    "quantity": 10000,
                    "price": 178.53,  # $0.01 variance
                    "side": "BUY",
                    "execution_time": "2026-01-15T14:32:15Z"
                },
                "prime_broker_record": {
                    "trade_id": "GS-2026-456789",
                    "symbol": "AAPL",
                    "quantity": 10000,
                    "price": 178.53,
                    "side": "BUY",
                    "execution_time": "2026-01-15T14:32:16Z"
                }
            },
            "break_type": "PRICE_VARIANCE",
            "variance_amount": 0.01,
            "variance_percentage": "0.006%",
            "root_cause_analysis": {
                "likely_cause": "Execution price rounding between OMS and clearing",
                "confidence": "HIGH",
                "historical_pattern": "This variance pattern occurs in 23% of AAPL trades"
            },
            "risk_assessment": {
                "financial_impact": "$100.00",
                "settlement_risk": "LOW",
                "regulatory_risk": "NONE"
            }
        }

        return json.dumps({
            "status": "success",
            "analysis": break_detail,
            "recommendation": "Auto-resolve: Accept clearing price as variance is within tolerance"
        }, indent=2)

    def _suggest_resolution(self, break_id: str, params: Dict) -> str:
        """Generate resolution suggestions for a trade break."""

        return json.dumps({
            "status": "success",
            "break_id": break_id or "SAMPLE-001",
            "resolution_options": [
                {
                    "option": "AUTO_ACCEPT_CLEARING",
                    "description": "Accept DTCC clearing price as authoritative",
                    "confidence": "HIGH",
                    "auto_executable": True,
                    "compliance_approved": True,
                    "historical_success_rate": "99.2%"
                },
                {
                    "option": "MANUAL_OVERRIDE_OMS",
                    "description": "Update OMS record to match clearing",
                    "confidence": "HIGH",
                    "auto_executable": False,
                    "requires_approval": ["Operations Manager"],
                    "compliance_approved": True
                },
                {
                    "option": "ESCALATE_TO_BROKER",
                    "description": "Request price clarification from executing broker",
                    "confidence": "MEDIUM",
                    "auto_executable": False,
                    "estimated_resolution_time": "2-4 hours"
                }
            ],
            "recommended_action": "AUTO_ACCEPT_CLEARING",
            "reason": "Variance ($0.01) is within auto-resolution threshold ($0.05)"
        }, indent=2)

    def _get_break_summary(self, trade_date: str, params: Dict) -> str:
        """Get summary of all breaks for a given date."""

        severity_filter = params.get('severity_filter', 'ALL')
        system_filter = params.get('system_filter', 'ALL')
        include_resolved = params.get('include_resolved', False)

        # Simulated break summary
        summary = {
            "trade_date": trade_date,
            "summary_generated_at": datetime.now().isoformat(),
            "break_counts_by_type": {
                "QUANTITY_MISMATCH": 3,
                "PRICE_VARIANCE": 12,
                "SETTLEMENT_DATE_MISMATCH": 1,
                "MISSING_TRADE": 2,
                "COUNTERPARTY_MISMATCH": 4,
                "COMMISSION_VARIANCE": 8
            },
            "break_counts_by_severity": {
                "CRITICAL": 1,
                "HIGH": 5,
                "MEDIUM": 14,
                "LOW": 10
            },
            "break_counts_by_system": {
                "OMS_DTCC": 15,
                "OMS_PRIME_BROKER": 8,
                "DTCC_PRIME_BROKER": 7
            },
            "resolution_status": {
                "auto_resolved": 22,
                "pending_review": 6,
                "escalated": 2
            },
            "financial_exposure": {
                "total_value_at_risk": "$45,230.00",
                "potential_penalties": "$2,100.00",
                "settlement_failures_projected": 2
            },
            "top_priority_breaks": [
                {
                    "break_id": "BRK-2026-0001",
                    "type": "MISSING_TRADE",
                    "severity": "CRITICAL",
                    "value": "$1,250,000",
                    "age_hours": 4.5
                },
                {
                    "break_id": "BRK-2026-0015",
                    "type": "SETTLEMENT_DATE_MISMATCH",
                    "severity": "HIGH",
                    "value": "$890,000",
                    "age_hours": 2.1
                }
            ]
        }

        return json.dumps({
            "status": "success",
            "filters_applied": {
                "severity": severity_filter,
                "system": system_filter,
                "include_resolved": include_resolved
            },
            "summary": summary
        }, indent=2)

    def _generate_audit_report(self, trade_date: str, params: Dict) -> str:
        """Generate compliance-ready audit report."""

        report = {
            "report_type": "DAILY_RECONCILIATION_AUDIT",
            "report_date": trade_date,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "TradeReconciliationAgent v1.0",
            "regulatory_frameworks": ["SEC Rule 17a-4", "FINRA Rule 4511"],
            "executive_summary": {
                "total_trades": 2847,
                "reconciled_successfully": 2817,
                "breaks_identified": 30,
                "auto_resolved": 24,
                "manually_resolved": 4,
                "pending_resolution": 2,
                "reconciliation_rate": "98.95%"
            },
            "system_coverage": {
                "charles_river_oms": {
                    "status": "COMPLETE",
                    "records_processed": 2847,
                    "processing_time": "00:01:23"
                },
                "dtcc_clearing": {
                    "status": "COMPLETE",
                    "records_processed": 2845,
                    "processing_time": "00:00:45"
                },
                "prime_brokers": {
                    "goldman_sachs": {"status": "COMPLETE", "records": 1423},
                    "morgan_stanley": {"status": "COMPLETE", "records": 892},
                    "jp_morgan": {"status": "COMPLETE", "records": 532}
                }
            },
            "break_resolution_audit_trail": [
                {
                    "break_id": "BRK-2026-0005",
                    "resolution_type": "AUTO",
                    "rule_applied": "PRICE_VARIANCE < $0.01",
                    "timestamp": "2026-01-15T09:15:22Z",
                    "approved_by": "SYSTEM"
                }
            ],
            "compliance_attestation": {
                "all_trades_reconciled": True,
                "audit_trail_complete": True,
                "exceptions_documented": True,
                "ready_for_regulatory_review": True
            },
            "retention_policy": {
                "report_retained_until": "2033-01-15",
                "storage_location": "Azure Blob - Compliance Archive"
            }
        }

        return json.dumps({
            "status": "success",
            "report": report,
            "download_formats_available": ["PDF", "JSON", "CSV"]
        }, indent=2)

    def _check_sla_status(self, trade_date: str) -> str:
        """Check SLA compliance status for reconciliation."""

        return json.dumps({
            "status": "success",
            "sla_dashboard": {
                "trade_date": trade_date,
                "current_time": datetime.now().isoformat(),
                "sla_targets": {
                    "reconciliation_complete_by": "09:30 ET",
                    "exceptions_resolved_by": "11:00 ET",
                    "audit_report_by": "12:00 ET"
                },
                "current_status": {
                    "reconciliation": {
                        "status": "COMPLETE",
                        "completed_at": "09:12 ET",
                        "within_sla": True
                    },
                    "exception_resolution": {
                        "status": "IN_PROGRESS",
                        "pending_count": 2,
                        "projected_completion": "10:45 ET",
                        "within_sla": True
                    },
                    "audit_report": {
                        "status": "PENDING",
                        "projected_completion": "11:30 ET",
                        "within_sla": True
                    }
                },
                "metrics_vs_target": {
                    "auto_resolution_rate": {"actual": "80%", "target": "90%", "status": "BELOW_TARGET"},
                    "processing_time": {"actual": "23 min", "target": "30 min", "status": "ON_TARGET"},
                    "break_rate": {"actual": "1.05%", "target": "2%", "status": "EXCEEDS_TARGET"}
                },
                "alerts": [
                    {
                        "severity": "MEDIUM",
                        "message": "Auto-resolution rate below 90% target",
                        "recommendation": "Review QUANTITY_MISMATCH rules - higher manual intervention today"
                    }
                ]
            }
        }, indent=2)

    # Helper methods for data simulation
    def _fetch_oms_trades(self, trade_date: str) -> List[Dict]:
        """Fetch trades from Charles River OMS."""
        return [{"id": f"OMS-{i}", "symbol": "AAPL", "qty": 1000} for i in range(100)]

    def _fetch_dtcc_trades(self, trade_date: str) -> List[Dict]:
        """Fetch trades from DTCC clearing."""
        return [{"id": f"DTCC-{i}", "symbol": "AAPL", "qty": 1000} for i in range(100)]

    def _fetch_prime_broker_trades(self, trade_date: str) -> List[Dict]:
        """Fetch trades from prime broker APIs."""
        return [{"id": f"PB-{i}", "symbol": "AAPL", "qty": 1000} for i in range(100)]

    def _compare_trades(self, oms: List, dtcc: List, pb: List) -> List[Dict]:
        """Compare trades across all three systems."""
        # Simulated breaks for demo
        return [
            {"id": "BRK-001", "type": "PRICE_VARIANCE", "severity": "MEDIUM"},
            {"id": "BRK-002", "type": "QUANTITY_MISMATCH", "severity": "LOW"},
        ]

    def _attempt_auto_resolution(self, break_item: Dict) -> Dict:
        """Attempt to auto-resolve a break based on rules."""
        return {"resolved": True, "rule": "AUTO_ACCEPT", "timestamp": datetime.now().isoformat()}
