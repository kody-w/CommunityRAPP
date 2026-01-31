"""
Fraud Detection and Alert Agent - Financial Services
Generated via RAPP Pipeline Process

Industry: Financial Services
Use Case: Real-time fraud detection, behavioral analytics, alert prioritization

Key Outcomes:
- Real-time fraud detection across transactions
- False positive reduction by 60%
- Fraud loss prevention
- Regulatory compliance maintenance

Target Users: Fraud Analysts, Risk Managers, Compliance Officers
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class FraudDetectionAgent(BasicAgent):
    """
    AI-powered fraud detection agent for real-time transaction
    monitoring, behavioral analytics, and alert management.
    """

    def __init__(self):
        self.name = 'FraudDetection'
        self.metadata = {
            "name": self.name,
            "description": "Scores transactions for fraud risk in real-time, detects behavioral anomalies, identifies fraud rings, and prioritizes alerts for investigation teams.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "score_transaction",
                            "analyze_account",
                            "detect_anomalies",
                            "get_alerts",
                            "investigate_case",
                            "generate_sar",
                            "get_fraud_metrics"
                        ],
                        "description": "Action to perform"
                    },
                    "transaction_id": {
                        "type": "string",
                        "description": "Transaction identifier"
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["24h", "7d", "30d"],
                        "description": "Analysis time period"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action', 'get_alerts')
        logger.info(f"FraudDetectionAgent performing action: {action}")

        try:
            if action == 'score_transaction':
                return self._score_transaction(kwargs)
            elif action == 'analyze_account':
                return self._analyze_account(kwargs.get('account_id'), kwargs)
            elif action == 'detect_anomalies':
                return self._detect_anomalies(kwargs)
            elif action == 'get_alerts':
                return self._get_alerts(kwargs)
            elif action == 'investigate_case':
                return self._investigate_case(kwargs)
            elif action == 'generate_sar':
                return self._generate_sar(kwargs)
            elif action == 'get_fraud_metrics':
                return self._get_fraud_metrics(kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"FraudDetectionAgent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _score_transaction(self, params: Dict) -> str:
        """Score transaction for fraud risk in real-time."""

        txn_id = params.get('transaction_id', 'TXN-2026-001234')

        score = {
            "transaction_id": txn_id,
            "scored_at": datetime.now().isoformat(),
            "processing_time_ms": 45,
            "transaction_details": {
                "amount": "$4,500.00",
                "type": "Wire Transfer",
                "channel": "Online Banking",
                "timestamp": datetime.now().isoformat(),
                "source_account": "****1234",
                "destination": "External - First National Bank",
                "destination_country": "United States",
                "ip_address": "192.168.1.xxx",
                "device_id": "DEV-789456"
            },
            "risk_score": {
                "overall": 72,
                "level": "Medium-High",
                "decision": "Review Required",
                "confidence": 0.89
            },
            "risk_factors": [
                {
                    "factor": "Unusual Amount",
                    "contribution": 25,
                    "detail": "Transaction 3x higher than 90-day average"
                },
                {
                    "factor": "New Beneficiary",
                    "contribution": 20,
                    "detail": "First transaction to this recipient"
                },
                {
                    "factor": "Velocity Check",
                    "contribution": 15,
                    "detail": "3rd high-value transfer this week"
                },
                {
                    "factor": "Time Anomaly",
                    "contribution": 12,
                    "detail": "Transaction at unusual hour (2:34 AM)"
                }
            ],
            "mitigating_factors": [
                {"factor": "Known Device", "reduction": -10, "detail": "Device used for 18 months"},
                {"factor": "Domestic Transfer", "reduction": -5, "detail": "US to US transfer"},
                {"factor": "Account Age", "reduction": -5, "detail": "Account holder for 8 years"}
            ],
            "recommended_action": "HOLD_FOR_REVIEW",
            "similar_fraud_patterns": [
                {"pattern": "Account Takeover - Wire Fraud", "similarity": 0.72},
                {"pattern": "Authorized Push Payment", "similarity": 0.65}
            ],
            "verification_options": [
                "Call customer to verify transaction",
                "Send push notification for confirmation",
                "Require step-up authentication"
            ]
        }

        return json.dumps({"status": "success", "risk_score": score}, indent=2)

    def _analyze_account(self, account_id: str, params: Dict) -> str:
        """Analyze account for fraud indicators."""

        analysis = {
            "account_id": account_id or "ACCT-123456",
            "analysis_date": datetime.now().isoformat(),
            "account_profile": {
                "type": "Personal Checking",
                "opened": "2018-03-15",
                "age_months": 94,
                "status": "Active",
                "tier": "Premium",
                "owner": "Demo User"
            },
            "behavioral_baseline": {
                "avg_monthly_transactions": 45,
                "avg_monthly_volume": "$12,500",
                "typical_channels": ["Mobile App", "Debit Card", "ACH"],
                "typical_locations": ["Portland, OR", "Seattle, WA"],
                "typical_hours": "8 AM - 10 PM PST"
            },
            "current_period_activity": {
                "transactions": 52,
                "volume": "$28,400",
                "deviation_from_baseline": "+127%",
                "new_channels_used": ["Wire Transfer"],
                "new_locations": ["Miami, FL"]
            },
            "risk_indicators": [
                {
                    "indicator": "Volume Spike",
                    "severity": "High",
                    "detail": "127% increase from baseline",
                    "first_seen": "2026-01-10"
                },
                {
                    "indicator": "New Channel Usage",
                    "severity": "Medium",
                    "detail": "First wire transfers in account history",
                    "first_seen": "2026-01-12"
                },
                {
                    "indicator": "Geographic Anomaly",
                    "severity": "Medium",
                    "detail": "Transactions from new location (Miami)",
                    "first_seen": "2026-01-11"
                }
            ],
            "account_risk_score": 68,
            "risk_level": "Elevated",
            "related_accounts": [
                {"account": "****5678", "relationship": "Joint Account", "risk": "Normal"},
                {"account": "****9012", "relationship": "Savings", "risk": "Normal"}
            ],
            "recommended_actions": [
                "Initiate customer contact for activity verification",
                "Enable enhanced monitoring for 30 days",
                "Review recent credential changes"
            ],
            "recent_security_events": [
                {"event": "Password Changed", "date": "2026-01-09", "channel": "Mobile App"},
                {"event": "New Device Added", "date": "2026-01-08", "device": "iPhone 15"}
            ]
        }

        return json.dumps({"status": "success", "account_analysis": analysis}, indent=2)

    def _detect_anomalies(self, params: Dict) -> str:
        """Detect behavioral anomalies across transactions."""

        anomalies = {
            "detection_run": datetime.now().isoformat(),
            "period_analyzed": params.get('time_period', '24h'),
            "transactions_analyzed": 125000,
            "anomalies_detected": 342,
            "anomaly_categories": {
                "velocity_anomalies": {
                    "count": 89,
                    "description": "Unusual transaction frequency",
                    "examples": ["5+ transactions within 10 minutes", "Daily limit approaching"]
                },
                "amount_anomalies": {
                    "count": 67,
                    "description": "Unusual transaction amounts",
                    "examples": ["Amount 5x higher than average", "Round-number pattern"]
                },
                "geographic_anomalies": {
                    "count": 54,
                    "description": "Impossible travel or new locations",
                    "examples": ["Transaction in 2 countries within 1 hour", "First-time country"]
                },
                "behavioral_anomalies": {
                    "count": 78,
                    "description": "Deviation from established patterns",
                    "examples": ["New merchant category", "Unusual time of day"]
                },
                "network_anomalies": {
                    "count": 34,
                    "description": "Suspicious network patterns",
                    "examples": ["Multiple accounts to same beneficiary", "Ring pattern detected"]
                },
                "device_anomalies": {
                    "count": 20,
                    "description": "Device or session irregularities",
                    "examples": ["New device", "VPN/proxy detected", "Rooted device"]
                }
            },
            "high_priority_anomalies": [
                {
                    "id": "ANM-001",
                    "type": "Network Pattern",
                    "severity": "Critical",
                    "accounts_involved": 12,
                    "description": "Potential fraud ring - 12 accounts transferring to same beneficiary",
                    "total_value": "$287,000",
                    "recommended_action": "Escalate to fraud ring investigation team"
                },
                {
                    "id": "ANM-002",
                    "type": "Account Takeover",
                    "severity": "High",
                    "accounts_involved": 1,
                    "description": "Credential change followed by immediate high-value transfer",
                    "total_value": "$45,000",
                    "recommended_action": "Block transaction, contact customer"
                }
            ],
            "model_performance": {
                "true_positive_rate": "92%",
                "false_positive_rate": "8%",
                "precision": "87%",
                "recall": "92%"
            }
        }

        return json.dumps({"status": "success", "anomaly_detection": anomalies}, indent=2)

    def _get_alerts(self, params: Dict) -> str:
        """Get prioritized fraud alerts for investigation."""

        alerts = {
            "as_of": datetime.now().isoformat(),
            "alert_summary": {
                "total_open": 156,
                "critical": 8,
                "high": 34,
                "medium": 67,
                "low": 47,
                "avg_age_hours": 4.2
            },
            "prioritized_alerts": [
                {
                    "alert_id": "ALT-2026-0001",
                    "priority": "Critical",
                    "created": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "type": "Potential Account Takeover",
                    "account": "****1234",
                    "amount_at_risk": "$125,000",
                    "risk_score": 95,
                    "summary": "Password change, new device, immediate wire transfer attempt",
                    "recommended_action": "Block pending transactions, contact customer immediately",
                    "assigned_to": "Unassigned"
                },
                {
                    "alert_id": "ALT-2026-0002",
                    "priority": "Critical",
                    "created": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "type": "Fraud Ring Pattern",
                    "accounts": "12 accounts",
                    "amount_at_risk": "$287,000",
                    "risk_score": 92,
                    "summary": "Multiple accounts transferring to same beneficiary within 24 hours",
                    "recommended_action": "Hold all related transactions, escalate to ring investigation",
                    "assigned_to": "Demo Exec 1"
                },
                {
                    "alert_id": "ALT-2026-0003",
                    "priority": "High",
                    "created": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "type": "Unusual Wire Activity",
                    "account": "****5678",
                    "amount_at_risk": "$45,000",
                    "risk_score": 78,
                    "summary": "First international wire, high amount, new beneficiary",
                    "recommended_action": "Verify with customer before releasing",
                    "assigned_to": "Demo Rep 1"
                }
            ],
            "sla_status": {
                "critical_avg_response": "15 minutes",
                "critical_sla": "30 minutes",
                "high_avg_response": "1.2 hours",
                "high_sla": "2 hours",
                "sla_compliance": "94%"
            },
            "team_workload": [
                {"analyst": "Demo Exec 1", "open_alerts": 12, "critical": 1, "capacity": "At Capacity"},
                {"analyst": "Demo Rep 1", "open_alerts": 8, "critical": 0, "capacity": "Available"},
                {"analyst": "Sarah Kim", "open_alerts": 10, "critical": 1, "capacity": "Available"}
            ]
        }

        return json.dumps({"status": "success", "alerts": alerts}, indent=2)

    def _investigate_case(self, params: Dict) -> str:
        """Provide investigation package for fraud case."""

        investigation = {
            "case_id": "CASE-2026-001234",
            "alert_id": params.get('transaction_id', 'ALT-2026-0001'),
            "investigation_started": datetime.now().isoformat(),
            "case_type": "Account Takeover",
            "status": "Under Investigation",
            "subject": {
                "account": "****1234",
                "customer": "Demo User",
                "relationship_since": "2018",
                "products": ["Checking", "Savings", "Credit Card"]
            },
            "timeline": [
                {"timestamp": "2026-01-14 23:45:00", "event": "Password changed via mobile app"},
                {"timestamp": "2026-01-14 23:52:00", "event": "New device added (iPhone)"},
                {"timestamp": "2026-01-15 00:15:00", "event": "Wire transfer initiated ($45,000)"},
                {"timestamp": "2026-01-15 00:16:00", "event": "Transaction blocked by fraud system"},
                {"timestamp": "2026-01-15 00:20:00", "event": "Alert generated and escalated"}
            ],
            "evidence": {
                "credential_changes": {
                    "password_change": {"time": "2026-01-14 23:45", "ip": "45.33.xxx.xxx", "location": "Miami, FL"},
                    "previous_password_age": "245 days",
                    "recovery_email_changed": False
                },
                "device_analysis": {
                    "new_device": True,
                    "device_type": "iPhone 15 Pro",
                    "first_seen": "2026-01-14 23:52",
                    "other_accounts_on_device": 0
                },
                "transaction_analysis": {
                    "amount": "$45,000",
                    "beneficiary": "First National Bank - Account ending 9876",
                    "beneficiary_first_seen": "2026-01-15",
                    "similar_fraud_cases": 3
                },
                "network_intelligence": {
                    "ip_reputation": "Suspicious - VPN/Proxy",
                    "ip_location": "Miami, FL",
                    "customer_home_location": "Portland, OR",
                    "known_fraud_association": False
                }
            },
            "customer_contact": {
                "attempted": True,
                "result": "Confirmed - Customer did NOT initiate transaction",
                "contact_time": "2026-01-15 08:30",
                "notes": "Customer confirmed account compromise. Password stolen via phishing."
            },
            "recommended_disposition": "CONFIRMED_FRAUD",
            "next_steps": [
                "File SAR within 24 hours",
                "Block all pending transactions",
                "Issue new credentials",
                "Credit customer account for any losses",
                "Add beneficiary to internal watchlist"
            ],
            "similar_cases": [
                {"case": "CASE-2025-089234", "similarity": "87%", "outcome": "Confirmed Fraud"},
                {"case": "CASE-2025-091456", "similarity": "82%", "outcome": "Confirmed Fraud"}
            ]
        }

        return json.dumps({"status": "success", "investigation": investigation}, indent=2)

    def _generate_sar(self, params: Dict) -> str:
        """Generate Suspicious Activity Report."""

        sar = {
            "sar_id": f"SAR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "case_reference": "CASE-2026-001234",
            "filing_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "sar_type": "Account Takeover / Wire Fraud",
            "subject_information": {
                "subject_type": "Account Holder (Victim)",
                "name": "Demo User",
                "account_numbers": ["****1234"],
                "ssn_tin": "XXX-XX-1234",
                "address": "Portland, OR",
                "occupation": "Software Engineer"
            },
            "suspicious_activity": {
                "activity_date_range": "2026-01-14 to 2026-01-15",
                "total_amount": "$45,000",
                "activity_type": "Wire Transfer Fraud",
                "description": "Account credentials were compromised via phishing attack. Unauthorized actor changed password, added new device, and attempted wire transfer to unknown beneficiary. Transaction was blocked by fraud detection system."
            },
            "narrative": """
On January 14, 2026, at approximately 23:45 PST, the account holder's online banking credentials
were compromised. The unauthorized actor changed the account password and added a new mobile
device to the account within 7 minutes.

At 00:15 PST on January 15, 2026, a wire transfer of $45,000 was initiated to an external
account at First National Bank. The beneficiary account (ending 9876) had no prior relationship
with the account holder.

The institution's fraud detection system flagged the transaction based on multiple risk factors:
- Credential changes immediately prior to high-value transfer
- New device used for transaction
- Transaction amount significantly exceeded historical baseline
- Transfer initiated during unusual hours for this customer

The transaction was automatically held for review. Customer contact on January 15 confirmed
the account holder did not authorize the transaction and had received a phishing email
the previous day.

The attempted fraud was prevented and no funds were lost. The account has been secured with
new credentials and enhanced monitoring has been implemented.
            """.strip(),
            "law_enforcement_contact": False,
            "related_sars": [],
            "attachments": [
                "Transaction details",
                "IP and device logs",
                "Customer contact notes",
                "Phishing email sample (if available)"
            ],
            "preparer": {
                "name": "Fraud Investigation Team",
                "title": "Fraud Analyst",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "review_status": "Pending Review",
            "filing_status": "Not Yet Filed"
        }

        return json.dumps({"status": "success", "sar": sar}, indent=2)

    def _get_fraud_metrics(self, params: Dict) -> str:
        """Get fraud detection metrics and KPIs."""

        metrics = {
            "reporting_period": params.get('time_period', '30d'),
            "as_of": datetime.now().isoformat(),
            "transaction_metrics": {
                "total_transactions": 2500000,
                "total_value": "$1.2B",
                "flagged_for_review": 4250,
                "flag_rate": "0.17%"
            },
            "fraud_metrics": {
                "confirmed_fraud_cases": 127,
                "fraud_losses": "$892,000",
                "fraud_prevented": "$4.2M",
                "prevention_rate": "82%",
                "loss_rate": "0.074%"
            },
            "detection_performance": {
                "true_positive_rate": "91%",
                "false_positive_rate": "9%",
                "precision": "86%",
                "recall": "91%",
                "f1_score": "88%"
            },
            "alert_metrics": {
                "total_alerts": 4250,
                "alerts_investigated": 4180,
                "avg_investigation_time": "2.3 hours",
                "sla_compliance": "94%"
            },
            "fraud_by_type": {
                "account_takeover": {"count": 45, "loss": "$380K", "percentage": "35%"},
                "card_fraud": {"count": 38, "loss": "$245K", "percentage": "30%"},
                "wire_fraud": {"count": 22, "loss": "$180K", "percentage": "17%"},
                "ach_fraud": {"count": 15, "loss": "$62K", "percentage": "12%"},
                "check_fraud": {"count": 7, "loss": "$25K", "percentage": "6%"}
            },
            "trend_analysis": {
                "fraud_rate_trend": "Decreasing (-12% vs prior period)",
                "false_positive_trend": "Improving (-8% vs prior period)",
                "emerging_threats": ["AI-generated phishing", "Synthetic identity fraud"]
            },
            "regulatory_compliance": {
                "sars_filed": 45,
                "sars_pending": 8,
                "filing_compliance": "100%",
                "audit_findings": 0
            }
        }

        return json.dumps({"status": "success", "fraud_metrics": metrics}, indent=2)
