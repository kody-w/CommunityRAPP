"""
Call Center Customer Service Agent - D365 Integration MVP
Generated via RAPP Pipeline Process

Customer: Pacific Northwest Insurance Group (Sample)
Industry: Insurance / Financial Services
Use Case: Unified agent desktop with AI-powered customer context

Problem Statement:
- Agents juggle 6-7 systems resulting in 12-minute average handle time vs 6-minute benchmark
- CSAT declined from 4.2 to 3.6, NPS from +32 to +18
- 45% agent turnover citing frustration with tools
- 8% customer churn following poor service experiences

Success Criteria:
- Reduce average handle time from 12 minutes to 6 minutes
- Improve CSAT from 3.6 to 4.2
- Reduce agent turnover through better tooling

Data Sources:
- Dynamics 365 Customer Service (CRM data, case history)
- Guidewire PolicyCenter (policy information)
- Oracle Financial Services (billing and payments)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class CallCenterAgent(BasicAgent):
    """
    AI-powered call center agent providing unified customer context
    and intelligent response suggestions for service representatives.

    Capabilities:
    - Unified customer view across CRM, policy, and billing systems
    - Real-time customer context on call initiation
    - Suggested responses based on conversation context
    - Policy coverage lookup and explanation
    - Billing inquiry resolution
    - Case creation and escalation support
    """

    def __init__(self):
        self.name = 'CallCenter'
        self.metadata = {
            "name": self.name,
            "description": "Provides unified customer context, suggested responses, and intelligent support for call center agents handling insurance customer inquiries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_customer_context",
                            "suggest_response",
                            "lookup_policy",
                            "check_billing",
                            "create_case",
                            "get_call_summary",
                            "escalate_to_supervisor"
                        ],
                        "description": "Action to perform"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier (phone, email, or policy number)"
                    },
                    "policy_number": {
                        "type": "string",
                        "description": "Insurance policy number"
                    },
                    "inquiry_type": {
                        "type": "string",
                        "enum": ["billing", "claims", "coverage", "policy_change", "general"],
                        "description": "Type of customer inquiry"
                    },
                    "customer_message": {
                        "type": "string",
                        "description": "Customer's question or concern"
                    },
                    "case_details": {
                        "type": "string",
                        "description": "Details for case creation"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Response templates by inquiry type
        self.response_templates = {
            "billing": {
                "payment_due": "I can see your payment of ${amount} is due on {date}. Would you like me to help you make a payment today, or would you prefer to set up automatic payments?",
                "payment_received": "Great news! I can confirm we received your payment of ${amount} on {date}. Your account is current.",
                "payment_plan": "I understand budgeting can be challenging. Let me look at some payment plan options that might work better for you."
            },
            "claims": {
                "status": "I can see your claim #{claim_id} was filed on {date}. It's currently {status}. {next_steps}",
                "file_new": "I'm sorry to hear about your situation. Let me help you file a claim right now. I'll need a few details about what happened.",
                "escalate": "I understand this claim is important to you. Let me get a claims specialist on the line to help resolve this today."
            },
            "coverage": {
                "verify": "Let me verify your coverage for {service}. Based on your {policy_type} policy, you have {coverage_details}.",
                "explain": "Your {coverage_type} provides {benefit_summary}. Your deductible is ${deductible} and your copay for this service would be ${copay}.",
                "upgrade": "I can see you're looking for additional coverage. Based on your current policy, I'd recommend our {recommended_plan} which would add {benefits}."
            }
        }

    def perform(self, **kwargs) -> str:
        """Execute the requested call center action."""
        action = kwargs.get('action', 'get_customer_context')
        customer_id = kwargs.get('customer_id')

        logger.info(f"CallCenterAgent performing action: {action}")

        try:
            if action == 'get_customer_context':
                return self._get_customer_context(customer_id, kwargs)
            elif action == 'suggest_response':
                return self._suggest_response(kwargs)
            elif action == 'lookup_policy':
                return self._lookup_policy(kwargs.get('policy_number'), kwargs)
            elif action == 'check_billing':
                return self._check_billing(customer_id, kwargs)
            elif action == 'create_case':
                return self._create_case(customer_id, kwargs)
            elif action == 'get_call_summary':
                return self._get_call_summary(customer_id, kwargs)
            elif action == 'escalate_to_supervisor':
                return self._escalate_to_supervisor(customer_id, kwargs)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}"
                })
        except Exception as e:
            logger.error(f"CallCenterAgent error: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def _get_customer_context(self, customer_id: str, params: Dict) -> str:
        """Get comprehensive customer context for call handling."""

        # Simulate unified customer data from multiple systems
        context = {
            "customer_id": customer_id or "CUST-789012",
            "retrieved_at": datetime.now().isoformat(),
            "profile": {
                "name": "Demo Customer 1",
                "preferred_name": "Jenny",
                "member_since": "2019-03-15",
                "tier": "Gold Member",
                "language": "English",
                "communication_preference": "Email",
                "time_zone": "Pacific"
            },
            "contact": {
                "primary_phone": "(503) 555-0123",
                "email": "j.martinez@email.com",
                "address": "1234 Pine Street, Portland, OR 97201"
            },
            "policies": [
                {
                    "policy_number": "HO-2026-456789",
                    "type": "Homeowners",
                    "status": "Active",
                    "effective_date": "2024-01-01",
                    "premium": "$1,850/year",
                    "next_payment": "2026-02-01"
                },
                {
                    "policy_number": "AU-2026-123456",
                    "type": "Auto",
                    "status": "Active",
                    "effective_date": "2024-03-15",
                    "premium": "$2,400/year",
                    "vehicles": ["2023 Toyota RAV4", "2021 Honda Civic"]
                }
            ],
            "recent_interactions": [
                {
                    "date": "2026-01-10",
                    "channel": "Phone",
                    "reason": "Billing inquiry",
                    "resolution": "Payment plan established",
                    "agent": "Demo Agent",
                    "satisfaction": "Satisfied"
                },
                {
                    "date": "2025-12-05",
                    "channel": "Web Chat",
                    "reason": "Coverage question",
                    "resolution": "Coverage verified",
                    "agent": "AI Assistant",
                    "satisfaction": "Very Satisfied"
                }
            ],
            "open_cases": [
                {
                    "case_id": "CASE-2026-001234",
                    "subject": "Add new vehicle to policy",
                    "status": "Pending Documentation",
                    "opened": "2026-01-12",
                    "priority": "Normal"
                }
            ],
            "billing_summary": {
                "total_balance": "$0.00",
                "payment_status": "Current",
                "autopay_enrolled": True,
                "next_payment_amount": "$358.33",
                "next_payment_date": "2026-02-01"
            },
            "risk_indicators": {
                "churn_risk": "Low",
                "payment_risk": "Low",
                "lifetime_value": "$45,000+",
                "nps_response": "Promoter (9)"
            },
            "suggested_actions": [
                {
                    "priority": "HIGH",
                    "action": "Follow up on pending vehicle addition",
                    "reason": "Case open for 4 days"
                },
                {
                    "priority": "MEDIUM",
                    "action": "Offer umbrella policy",
                    "reason": "Multi-policy customer, high lifetime value"
                }
            ],
            "call_greeting": "Hello Jenny! I can see you're a Gold Member since 2019. How can I help you today?"
        }

        return json.dumps({
            "status": "success",
            "customer_context": context,
            "systems_queried": ["D365 Customer Service", "Guidewire PolicyCenter", "Oracle Financial"],
            "retrieval_time_ms": 234
        }, indent=2)

    def _suggest_response(self, params: Dict) -> str:
        """Generate suggested responses based on customer message and context."""

        customer_message = params.get('customer_message', '')
        inquiry_type = params.get('inquiry_type', 'general')

        # Analyze message intent
        intent_analysis = {
            "detected_intent": "billing_inquiry",
            "confidence": 0.92,
            "sentiment": "neutral",
            "urgency": "normal"
        }

        # Generate response suggestions
        suggestions = [
            {
                "response": "I'd be happy to help you with your billing question. I can see your account is current with autopay set up for the 1st of each month. Was there a specific charge you wanted to discuss?",
                "type": "acknowledge_and_clarify",
                "recommended": True
            },
            {
                "response": "Your next payment of $358.33 is scheduled for February 1st. Would you like me to review the breakdown of that amount?",
                "type": "proactive_information",
                "recommended": False
            },
            {
                "response": "I see you have both homeowners and auto policies with us. Is your question about a specific policy?",
                "type": "clarify_context",
                "recommended": False
            }
        ]

        # Knowledge base articles for reference
        knowledge_articles = [
            {
                "article_id": "KB-001234",
                "title": "Understanding Your Monthly Statement",
                "relevance": 0.89
            },
            {
                "article_id": "KB-002345",
                "title": "Payment Options and Methods",
                "relevance": 0.76
            }
        ]

        return json.dumps({
            "status": "success",
            "customer_message": customer_message,
            "intent_analysis": intent_analysis,
            "suggested_responses": suggestions,
            "knowledge_articles": knowledge_articles,
            "compliance_notes": [
                "Customer has consented to call recording",
                "No sensitive health information in this inquiry"
            ]
        }, indent=2)

    def _lookup_policy(self, policy_number: str, params: Dict) -> str:
        """Look up detailed policy information."""

        policy = {
            "policy_number": policy_number or "HO-2026-456789",
            "type": "Homeowners Insurance",
            "status": "Active",
            "holder": "Demo Customer 1",
            "effective_dates": {
                "start": "2024-01-01",
                "end": "2026-01-01",
                "renewal_date": "2026-01-01"
            },
            "property": {
                "address": "1234 Pine Street, Portland, OR 97201",
                "type": "Single Family Home",
                "year_built": 2005,
                "square_feet": 2400,
                "construction": "Wood Frame"
            },
            "coverages": {
                "dwelling": {"limit": "$450,000", "deductible": "$1,000"},
                "personal_property": {"limit": "$225,000", "deductible": "$1,000"},
                "liability": {"limit": "$300,000", "deductible": "$0"},
                "medical_payments": {"limit": "$5,000", "deductible": "$0"},
                "loss_of_use": {"limit": "$90,000", "deductible": "$0"}
            },
            "endorsements": [
                {"name": "Water Backup", "limit": "$10,000"},
                {"name": "Scheduled Personal Property", "items": ["Jewelry - $5,000", "Electronics - $3,000"]},
                {"name": "Home Business", "limit": "$25,000"}
            ],
            "premium": {
                "annual": "$1,850",
                "monthly": "$154.17",
                "payment_method": "Autopay - Bank Account"
            },
            "claims_history": [
                {
                    "claim_number": "CLM-2023-001",
                    "date": "2023-08-15",
                    "type": "Water Damage",
                    "amount_paid": "$4,500",
                    "status": "Closed"
                }
            ],
            "discounts_applied": [
                {"name": "Multi-Policy", "amount": "15%"},
                {"name": "Claims-Free", "amount": "10%"},
                {"name": "Smart Home Devices", "amount": "5%"}
            ]
        }

        return json.dumps({
            "status": "success",
            "policy": policy,
            "source_system": "Guidewire PolicyCenter"
        }, indent=2)

    def _check_billing(self, customer_id: str, params: Dict) -> str:
        """Check billing and payment information."""

        billing = {
            "customer_id": customer_id or "CUST-789012",
            "account_number": "ACCT-456789",
            "account_status": "Current",
            "policies_billed": [
                {
                    "policy": "HO-2026-456789",
                    "type": "Homeowners",
                    "monthly_amount": "$154.17"
                },
                {
                    "policy": "AU-2026-123456",
                    "type": "Auto",
                    "monthly_amount": "$200.00"
                }
            ],
            "current_balance": "$0.00",
            "payment_schedule": {
                "frequency": "Monthly",
                "autopay_enrolled": True,
                "payment_method": "Bank Account ****1234",
                "next_payment": {
                    "date": "2026-02-01",
                    "amount": "$354.17"
                }
            },
            "payment_history": [
                {"date": "2026-01-01", "amount": "$354.17", "status": "Processed", "method": "Autopay"},
                {"date": "2025-12-01", "amount": "$354.17", "status": "Processed", "method": "Autopay"},
                {"date": "2025-11-01", "amount": "$354.17", "status": "Processed", "method": "Autopay"}
            ],
            "available_actions": [
                "Make one-time payment",
                "Change payment method",
                "Update autopay date",
                "Request payment extension",
                "Set up payment plan"
            ]
        }

        return json.dumps({
            "status": "success",
            "billing": billing,
            "source_system": "Oracle Financial Services"
        }, indent=2)

    def _create_case(self, customer_id: str, params: Dict) -> str:
        """Create a new customer service case."""

        case_details = params.get('case_details', 'Customer inquiry')
        inquiry_type = params.get('inquiry_type', 'general')

        new_case = {
            "case_id": f"CASE-2026-{datetime.now().strftime('%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "customer_id": customer_id or "CUST-789012",
            "subject": case_details[:100] if case_details else "General Inquiry",
            "description": case_details,
            "type": inquiry_type.title(),
            "status": "Open",
            "priority": "Normal",
            "assigned_to": "Unassigned",
            "sla": {
                "response_due": (datetime.now() + timedelta(hours=4)).isoformat(),
                "resolution_due": (datetime.now() + timedelta(days=2)).isoformat()
            },
            "next_steps": [
                "Case created and logged in D365",
                "Customer will receive confirmation email",
                "Route to appropriate department based on type"
            ]
        }

        return json.dumps({
            "status": "success",
            "case": new_case,
            "message": f"Case {new_case['case_id']} created successfully"
        }, indent=2)

    def _get_call_summary(self, customer_id: str, params: Dict) -> str:
        """Generate summary of the current call for after-call work."""

        summary = {
            "call_id": f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_id": customer_id or "CUST-789012",
            "customer_name": "Demo Customer 1",
            "call_start": (datetime.now() - timedelta(minutes=8)).isoformat(),
            "call_end": datetime.now().isoformat(),
            "duration_minutes": 8,
            "inquiry_summary": "Customer called to inquire about adding a new vehicle to their auto policy. Verified coverage details and explained the process.",
            "topics_discussed": [
                "Auto policy coverage review",
                "New vehicle addition process",
                "Documentation requirements",
                "Premium impact estimate"
            ],
            "actions_taken": [
                "Verified customer identity",
                "Reviewed current auto policy AU-2026-123456",
                "Explained vehicle addition process",
                "Created case CASE-2026-001234 for follow-up"
            ],
            "follow_up_required": True,
            "follow_up_items": [
                "Customer will email VIN and registration for new vehicle",
                "Update policy once documentation received",
                "Send updated premium quote"
            ],
            "disposition_code": "INQUIRY_RESOLVED",
            "customer_sentiment": "Positive",
            "recommended_notes": "Customer appreciated detailed explanation. High lifetime value - consider umbrella policy offer on next contact."
        }

        return json.dumps({
            "status": "success",
            "call_summary": summary,
            "ready_for_submission": True
        }, indent=2)

    def _escalate_to_supervisor(self, customer_id: str, params: Dict) -> str:
        """Initiate escalation to supervisor."""

        escalation = {
            "escalation_id": f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_id": customer_id or "CUST-789012",
            "initiated_at": datetime.now().isoformat(),
            "reason": params.get('case_details', 'Customer requested supervisor'),
            "urgency": "Normal",
            "available_supervisors": [
                {"name": "Demo Contact A", "status": "Available", "queue_depth": 0},
                {"name": "Robert Chen", "status": "On Call", "queue_depth": 2},
                {"name": "Maria Garcia", "status": "Away", "queue_depth": 0}
            ],
            "recommended_supervisor": "Demo Contact A",
            "estimated_wait": "< 1 minute",
            "customer_context_transferred": True,
            "pre_escalation_checklist": [
                {"item": "Customer identity verified", "complete": True},
                {"item": "Issue documented in case", "complete": True},
                {"item": "Previous resolution attempts noted", "complete": True},
                {"item": "Customer sentiment captured", "complete": True}
            ]
        }

        return json.dumps({
            "status": "success",
            "escalation": escalation,
            "message": "Escalation initiated. Supervisor Demo Contact A will join shortly."
        }, indent=2)
