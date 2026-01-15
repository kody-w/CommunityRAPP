"""
IT Ticket Management Agent - Intelligent Support Automation
Generated via RAPP Pipeline Process

Industry: Cross-Industry (IT Operations)
Use Case: Automate IT support ticket routing, prioritization, and L1/L2 resolution

Key Outcomes:
- Automated ticket triage and routing
- L1/L2 ticket resolution without human intervention
- Reduced mean time to resolution
- Improved IT team productivity

Target Users: IT Help Desk, Support Teams, IT Managers
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class ITTicketAgent(BasicAgent):
    """
    Intelligent IT support agent for automated ticket management,
    triage, resolution, and escalation.
    """

    def __init__(self):
        self.name = 'ITTicketManagement'
        self.metadata = {
            "name": self.name,
            "description": "Automates IT support ticket routing, prioritization, and resolution. Handles L1/L2 issues autonomously and escalates complex cases appropriately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "triage_ticket",
                            "auto_resolve",
                            "suggest_solution",
                            "route_ticket",
                            "get_queue_status",
                            "escalate_ticket",
                            "get_knowledge_article"
                        ],
                        "description": "Action to perform"
                    },
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket identifier"
                    },
                    "ticket_description": {
                        "type": "string",
                        "description": "Description of the IT issue"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User reporting the issue"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["hardware", "software", "network", "access", "email", "other"],
                        "description": "Issue category"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Resolution templates for common issues
        self.resolution_templates = {
            "password_reset": {
                "category": "access",
                "auto_resolvable": True,
                "steps": ["Verify user identity", "Generate temporary password", "Send secure link", "Log action"]
            },
            "vpn_connection": {
                "category": "network",
                "auto_resolvable": True,
                "steps": ["Check VPN client version", "Verify credentials", "Clear VPN cache", "Reconnect"]
            },
            "email_sync": {
                "category": "email",
                "auto_resolvable": True,
                "steps": ["Check Outlook version", "Verify account settings", "Clear cache", "Restart client"]
            },
            "software_install": {
                "category": "software",
                "auto_resolvable": False,
                "steps": ["Verify license availability", "Check system requirements", "Submit to software team"]
            }
        }

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action', 'triage_ticket')
        logger.info(f"ITTicketAgent performing action: {action}")

        try:
            if action == 'triage_ticket':
                return self._triage_ticket(kwargs)
            elif action == 'auto_resolve':
                return self._auto_resolve(kwargs.get('ticket_id'), kwargs)
            elif action == 'suggest_solution':
                return self._suggest_solution(kwargs)
            elif action == 'route_ticket':
                return self._route_ticket(kwargs.get('ticket_id'), kwargs)
            elif action == 'get_queue_status':
                return self._get_queue_status(kwargs)
            elif action == 'escalate_ticket':
                return self._escalate_ticket(kwargs.get('ticket_id'), kwargs)
            elif action == 'get_knowledge_article':
                return self._get_knowledge_article(kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"ITTicketAgent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _triage_ticket(self, params: Dict) -> str:
        """Triage incoming ticket and determine routing/resolution path."""

        description = params.get('ticket_description', 'User unable to login')
        user_id = params.get('user_id', 'USER-001')

        triage = {
            "ticket_id": f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "submitted_at": datetime.now().isoformat(),
            "user": user_id,
            "original_description": description,
            "analysis": {
                "detected_category": "access",
                "detected_subcategory": "password_reset",
                "confidence": 0.92,
                "keywords_matched": ["login", "unable", "password"],
                "sentiment": "frustrated",
                "urgency_detected": "medium"
            },
            "classification": {
                "priority": "P2",
                "impact": "Single User",
                "category": "Access Management",
                "subcategory": "Password Reset",
                "sla_response": "4 hours",
                "sla_resolution": "8 hours"
            },
            "auto_resolution_eligible": True,
            "recommended_action": "AUTO_RESOLVE",
            "similar_tickets": [
                {"ticket": "TKT-2026-001234", "resolution": "Password reset completed", "similarity": 0.95},
                {"ticket": "TKT-2026-001156", "resolution": "Account unlocked", "similarity": 0.87}
            ],
            "user_context": {
                "department": "Marketing",
                "location": "Seattle Office",
                "vip_status": False,
                "recent_tickets": 2,
                "last_ticket_date": "2025-12-15"
            },
            "next_steps": [
                "Attempt auto-resolution via password reset portal",
                "Send user confirmation with temporary credentials",
                "Close ticket with resolution notes"
            ]
        }

        return json.dumps({"status": "success", "triage_result": triage}, indent=2)

    def _auto_resolve(self, ticket_id: str, params: Dict) -> str:
        """Attempt automatic resolution of ticket."""

        resolution = {
            "ticket_id": ticket_id or "TKT-2026-001500",
            "resolution_attempted": datetime.now().isoformat(),
            "resolution_type": "Automated",
            "issue_category": "Password Reset",
            "resolution_status": "SUCCESS",
            "actions_taken": [
                {"step": 1, "action": "Verified user identity via security questions", "status": "Complete"},
                {"step": 2, "action": "Generated temporary password", "status": "Complete"},
                {"step": 3, "action": "Sent secure password reset link to user email", "status": "Complete"},
                {"step": 4, "action": "Logged action in audit trail", "status": "Complete"}
            ],
            "user_communication": {
                "method": "Email",
                "sent_to": "user@company.com",
                "template_used": "PASSWORD_RESET_SUCCESS",
                "sent_at": datetime.now().isoformat()
            },
            "ticket_update": {
                "status": "Resolved",
                "resolution_code": "AUTO_RESOLVED",
                "resolution_notes": "Password reset completed automatically. User received secure reset link via email.",
                "time_to_resolution": "3 minutes"
            },
            "quality_metrics": {
                "first_contact_resolution": True,
                "customer_effort_score": "Low",
                "automation_confidence": 0.95
            },
            "follow_up_scheduled": {
                "type": "Satisfaction survey",
                "send_date": (datetime.now() + timedelta(days=1)).isoformat()
            }
        }

        return json.dumps({"status": "success", "resolution": resolution}, indent=2)

    def _suggest_solution(self, params: Dict) -> str:
        """Suggest solutions based on ticket description and knowledge base."""

        description = params.get('ticket_description', 'VPN not connecting')

        suggestions = {
            "query": description,
            "analysis": {
                "detected_issue": "VPN connectivity failure",
                "common_causes": [
                    "Outdated VPN client",
                    "Network firewall blocking",
                    "Expired credentials",
                    "DNS resolution issues"
                ],
                "confidence": 0.88
            },
            "suggested_solutions": [
                {
                    "solution_id": "SOL-001",
                    "title": "Update VPN Client",
                    "confidence": 0.85,
                    "steps": [
                        "Open Software Center",
                        "Search for 'VPN Client'",
                        "Click 'Update' if available",
                        "Restart computer and retry connection"
                    ],
                    "estimated_time": "10 minutes",
                    "success_rate": "72%"
                },
                {
                    "solution_id": "SOL-002",
                    "title": "Clear VPN Cache and Reconnect",
                    "confidence": 0.78,
                    "steps": [
                        "Right-click VPN icon in system tray",
                        "Select 'Disconnect'",
                        "Go to Settings > Network > VPN",
                        "Remove existing VPN profile",
                        "Re-add VPN connection with provided server address",
                        "Connect with your credentials"
                    ],
                    "estimated_time": "5 minutes",
                    "success_rate": "65%"
                },
                {
                    "solution_id": "SOL-003",
                    "title": "Reset Network Configuration",
                    "confidence": 0.65,
                    "steps": [
                        "Open Command Prompt as Administrator",
                        "Run: ipconfig /flushdns",
                        "Run: netsh winsock reset",
                        "Restart computer",
                        "Retry VPN connection"
                    ],
                    "estimated_time": "15 minutes",
                    "success_rate": "58%"
                }
            ],
            "knowledge_articles": [
                {"id": "KB-1234", "title": "VPN Troubleshooting Guide", "relevance": 0.92},
                {"id": "KB-1189", "title": "Network Connectivity Issues", "relevance": 0.78}
            ],
            "escalation_criteria": [
                "User has tried all suggested solutions",
                "Issue persists after VPN client update",
                "Multiple users affected"
            ]
        }

        return json.dumps({"status": "success", "suggestions": suggestions}, indent=2)

    def _route_ticket(self, ticket_id: str, params: Dict) -> str:
        """Route ticket to appropriate support team."""

        routing = {
            "ticket_id": ticket_id or "TKT-2026-001501",
            "routing_decision": {
                "assigned_team": "Network Operations",
                "assigned_agent": "David Kim",
                "queue": "Network-L2",
                "priority_in_queue": 3,
                "estimated_wait": "45 minutes"
            },
            "routing_rationale": {
                "category": "Network",
                "complexity": "L2 - Requires specialist",
                "skills_required": ["VPN", "Network Troubleshooting", "Firewall"],
                "matched_agent_skills": ["VPN Expert", "Network+", "Firewall Admin"]
            },
            "agent_context_provided": {
                "ticket_summary": "User unable to connect to VPN after client update",
                "troubleshooting_attempted": [
                    "VPN client reinstalled",
                    "Network cache cleared",
                    "Firewall temporarily disabled"
                ],
                "user_environment": "Windows 11, VPN Client v3.2.1, Seattle Office",
                "similar_resolved_tickets": 3
            },
            "sla_tracking": {
                "response_due": (datetime.now() + timedelta(hours=4)).isoformat(),
                "resolution_due": (datetime.now() + timedelta(hours=8)).isoformat(),
                "sla_status": "On Track"
            },
            "notifications_sent": [
                {"recipient": "User", "type": "Ticket routed notification"},
                {"recipient": "David Kim", "type": "New ticket assignment"},
                {"recipient": "Network Team Lead", "type": "Queue update"}
            ]
        }

        return json.dumps({"status": "success", "routing": routing}, indent=2)

    def _get_queue_status(self, params: Dict) -> str:
        """Get current queue status and metrics."""

        queue_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "open_tickets": 47,
                "in_progress": 23,
                "pending_user": 8,
                "resolved_today": 56,
                "avg_resolution_time": "2.3 hours",
                "first_contact_resolution": "68%"
            },
            "by_priority": {
                "P1_Critical": {"open": 2, "avg_age": "45 min", "sla_breach_risk": 0},
                "P2_High": {"open": 8, "avg_age": "2.1 hours", "sla_breach_risk": 1},
                "P3_Medium": {"open": 22, "avg_age": "4.5 hours", "sla_breach_risk": 3},
                "P4_Low": {"open": 15, "avg_age": "1.2 days", "sla_breach_risk": 0}
            },
            "by_category": {
                "Access Management": {"count": 15, "auto_resolved": 12},
                "Network": {"count": 10, "auto_resolved": 3},
                "Software": {"count": 12, "auto_resolved": 5},
                "Hardware": {"count": 6, "auto_resolved": 0},
                "Email": {"count": 4, "auto_resolved": 2}
            },
            "team_workload": [
                {"agent": "Sarah Chen", "assigned": 8, "capacity": 10, "status": "Available"},
                {"agent": "Michael Park", "assigned": 10, "capacity": 10, "status": "At Capacity"},
                {"agent": "David Kim", "assigned": 5, "capacity": 8, "status": "Available"}
            ],
            "automation_metrics": {
                "auto_resolved_today": 34,
                "auto_resolution_rate": "61%",
                "avg_auto_resolution_time": "4 minutes",
                "deflection_rate": "45%"
            },
            "alerts": [
                {"type": "SLA Risk", "ticket": "TKT-2026-001234", "time_remaining": "30 min"},
                {"type": "High Volume", "category": "Access Management", "increase": "+40%"}
            ]
        }

        return json.dumps({"status": "success", "queue_status": queue_status}, indent=2)

    def _escalate_ticket(self, ticket_id: str, params: Dict) -> str:
        """Escalate ticket to higher support tier."""

        escalation = {
            "ticket_id": ticket_id or "TKT-2026-001502",
            "escalation_details": {
                "from_tier": "L1",
                "to_tier": "L2",
                "escalation_reason": "Issue requires specialized network expertise",
                "escalated_by": "Auto-Escalation Engine",
                "escalated_at": datetime.now().isoformat()
            },
            "escalation_criteria_met": [
                "Auto-resolution failed",
                "User attempted all suggested solutions",
                "Issue persists after 2 hours",
                "Complexity score exceeds L1 threshold"
            ],
            "handoff_package": {
                "issue_summary": "VPN connectivity failure persisting after standard troubleshooting",
                "troubleshooting_log": [
                    "VPN client reinstalled - No change",
                    "Network cache cleared - No change",
                    "DNS flushed - No change",
                    "Firewall temporarily disabled - No change"
                ],
                "user_environment": {
                    "os": "Windows 11 Pro",
                    "vpn_client": "v3.2.1",
                    "location": "Seattle Office",
                    "network_type": "Corporate LAN"
                },
                "diagnostic_data_attached": True,
                "remote_session_consent": True
            },
            "new_assignment": {
                "team": "Network Operations - L2",
                "agent": "Jennifer Walsh",
                "priority": "P2",
                "new_sla_response": (datetime.now() + timedelta(hours=2)).isoformat(),
                "new_sla_resolution": (datetime.now() + timedelta(hours=6)).isoformat()
            },
            "notifications": [
                {"recipient": "User", "message": "Your ticket has been escalated to our Network specialists"},
                {"recipient": "Jennifer Walsh", "message": "New L2 escalation assigned"},
                {"recipient": "L1 Agent", "message": "Ticket escalated successfully"}
            ]
        }

        return json.dumps({"status": "success", "escalation": escalation}, indent=2)

    def _get_knowledge_article(self, params: Dict) -> str:
        """Retrieve relevant knowledge base article."""

        description = params.get('ticket_description', 'outlook not syncing')

        article = {
            "query": description,
            "top_article": {
                "id": "KB-2345",
                "title": "Resolving Outlook Email Synchronization Issues",
                "category": "Email",
                "last_updated": "2026-01-05",
                "relevance_score": 0.94,
                "view_count": 1247,
                "helpful_votes": 892,
                "content_summary": "Step-by-step guide to resolve Outlook sync issues including cache clearing, profile repair, and account reconfiguration.",
                "sections": [
                    "Quick Fix: Restart and Retry",
                    "Clear Outlook Cache",
                    "Repair Outlook Profile",
                    "Reconfigure Email Account",
                    "When to Escalate"
                ],
                "estimated_resolution_time": "15 minutes",
                "success_rate": "78%"
            },
            "related_articles": [
                {"id": "KB-2346", "title": "Outlook Performance Optimization", "relevance": 0.72},
                {"id": "KB-2301", "title": "Email Account Setup Guide", "relevance": 0.65},
                {"id": "KB-2389", "title": "Outlook Mobile Sync Troubleshooting", "relevance": 0.58}
            ],
            "user_feedback_prompt": "Was this article helpful?",
            "escalation_available": True
        }

        return json.dumps({"status": "success", "knowledge_article": article}, indent=2)
