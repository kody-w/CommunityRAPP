"""
Customer 360 Agent - Unified Customer Intelligence
Generated via RAPP Pipeline Process

Industry: Cross-Industry (Agnostic)
Use Case: Consolidate customer data from CRM, support tickets, product usage,
and contracts into a unified view with proactive health monitoring.

Key Outcomes:
- Unified customer view aggregating all touchpoints into single profile
- Proactive churn prevention with early warning risk identification
- Systematic expansion revenue through data-driven cross-sell detection
- Relationship intelligence tracking stakeholder changes and engagement gaps

Target Users: CSMs, Account Executives, Account Managers, Sales Leadership
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class Customer360Agent(BasicAgent):
    """
    Comprehensive customer intelligence agent providing unified 360-degree
    customer profiles with health scoring, churn prediction, and expansion
    opportunity identification.
    """

    def __init__(self):
        self.name = 'Customer360'
        self.metadata = {
            "name": self.name,
            "description": "Provides unified 360-degree customer view with health scoring, churn risk prediction, expansion opportunities, and stakeholder intelligence across all touchpoints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "get_customer_profile",
                            "calculate_health_score",
                            "predict_churn_risk",
                            "identify_expansion_opportunities",
                            "get_stakeholder_map",
                            "prepare_meeting_brief",
                            "get_engagement_gaps",
                            "generate_retention_playbook"
                        ],
                        "description": "Action to perform"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer or account identifier"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["30d", "90d", "12m", "all"],
                        "description": "Time period for analysis"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include AI-generated recommendations"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Health score weights
        self.health_weights = {
            "product_usage": 0.25,
            "support_sentiment": 0.20,
            "engagement_frequency": 0.20,
            "contract_health": 0.15,
            "payment_history": 0.10,
            "nps_score": 0.10
        }

    def perform(self, **kwargs) -> str:
        """Execute the requested customer intelligence action."""
        action = kwargs.get('action', 'get_customer_profile')
        customer_id = kwargs.get('customer_id', 'ACCT-001')

        logger.info(f"Customer360Agent performing action: {action}")

        try:
            if action == 'get_customer_profile':
                return self._get_customer_profile(customer_id, kwargs)
            elif action == 'calculate_health_score':
                return self._calculate_health_score(customer_id, kwargs)
            elif action == 'predict_churn_risk':
                return self._predict_churn_risk(customer_id, kwargs)
            elif action == 'identify_expansion_opportunities':
                return self._identify_expansion_opportunities(customer_id, kwargs)
            elif action == 'get_stakeholder_map':
                return self._get_stakeholder_map(customer_id, kwargs)
            elif action == 'prepare_meeting_brief':
                return self._prepare_meeting_brief(customer_id, kwargs)
            elif action == 'get_engagement_gaps':
                return self._get_engagement_gaps(customer_id, kwargs)
            elif action == 'generate_retention_playbook':
                return self._generate_retention_playbook(customer_id, kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"Customer360Agent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _get_customer_profile(self, customer_id: str, params: Dict) -> str:
        """Get comprehensive 360-degree customer profile."""

        profile = {
            "customer_id": customer_id,
            "retrieved_at": datetime.now().isoformat(),
            "company": {
                "name": "Acme Corporation",
                "industry": "Technology",
                "size": "Enterprise (5,000+ employees)",
                "headquarters": "San Francisco, CA",
                "founded": 2010,
                "annual_revenue": "$500M-$1B"
            },
            "relationship": {
                "customer_since": "2021-03-15",
                "tier": "Strategic",
                "csm_assigned": "Demo Contact A",
                "ae_assigned": "Demo Rep 1",
                "executive_sponsor": "VP of Operations"
            },
            "contract": {
                "current_arr": "$450,000",
                "contract_start": "2024-01-01",
                "contract_end": "2026-12-31",
                "products": ["Platform Pro", "Analytics Suite", "Integration Hub"],
                "seats_purchased": 500,
                "seats_active": 423
            },
            "health_summary": {
                "overall_score": 78,
                "trend": "Stable",
                "risk_level": "Low",
                "last_updated": datetime.now().isoformat()
            },
            "engagement_summary": {
                "last_meeting": "2026-01-10",
                "meetings_90d": 4,
                "support_tickets_90d": 12,
                "feature_requests": 3,
                "nps_score": 8,
                "nps_date": "2025-12-15"
            },
            "product_usage": {
                "dau": 312,
                "mau": 423,
                "adoption_rate": "84.6%",
                "top_features": ["Dashboard", "Reports", "Integrations"],
                "underutilized": ["Advanced Analytics", "API Access"]
            },
            "financial": {
                "total_ltv": "$1.8M",
                "payment_status": "Current",
                "expansion_potential": "$150K"
            },
            "recent_interactions": [
                {"date": "2026-01-10", "type": "QBR", "attendees": 6, "outcome": "Positive"},
                {"date": "2026-01-05", "type": "Support", "ticket": "High priority resolved"},
                {"date": "2025-12-20", "type": "Feature Request", "status": "In roadmap"}
            ],
            "key_insights": [
                "Strong adoption but Advanced Analytics underutilized - training opportunity",
                "3 stakeholder changes in past 6 months - relationship risk",
                "Expansion discussion scheduled for Q2 renewal prep"
            ]
        }

        return json.dumps({
            "status": "success",
            "profile": profile,
            "data_sources": ["Salesforce CRM", "Zendesk", "Product Analytics", "DocuSign"]
        }, indent=2)

    def _calculate_health_score(self, customer_id: str, params: Dict) -> str:
        """Calculate comprehensive customer health score."""

        health = {
            "customer_id": customer_id,
            "overall_score": 78,
            "score_breakdown": {
                "product_usage": {"score": 85, "weight": 0.25, "contribution": 21.25},
                "support_sentiment": {"score": 72, "weight": 0.20, "contribution": 14.4},
                "engagement_frequency": {"score": 80, "weight": 0.20, "contribution": 16.0},
                "contract_health": {"score": 90, "weight": 0.15, "contribution": 13.5},
                "payment_history": {"score": 100, "weight": 0.10, "contribution": 10.0},
                "nps_score": {"score": 80, "weight": 0.10, "contribution": 8.0}
            },
            "trend": {
                "direction": "Stable",
                "30d_change": -2,
                "90d_change": +5
            },
            "risk_factors": [
                {"factor": "Support ticket volume increased 40%", "impact": "Medium"},
                {"factor": "Key stakeholder departure", "impact": "Low"}
            ],
            "positive_signals": [
                {"signal": "DAU up 15% month-over-month", "impact": "High"},
                {"signal": "Completed all QBRs on schedule", "impact": "Medium"},
                {"signal": "Expanding to new department", "impact": "High"}
            ],
            "recommendations": [
                "Schedule training session for Advanced Analytics module",
                "Re-engage with new VP of Operations within 2 weeks",
                "Address support ticket backlog with dedicated session"
            ]
        }

        return json.dumps({"status": "success", "health_score": health}, indent=2)

    def _predict_churn_risk(self, customer_id: str, params: Dict) -> str:
        """Predict customer churn risk with contributing factors."""

        churn = {
            "customer_id": customer_id,
            "churn_probability": 0.15,
            "risk_level": "Low",
            "days_to_renewal": 365,
            "confidence": 0.87,
            "risk_factors": [
                {
                    "factor": "Stakeholder changes",
                    "description": "3 key contacts changed in 6 months",
                    "contribution": 0.05,
                    "mitigation": "Schedule intro meetings with new stakeholders"
                },
                {
                    "factor": "Support sentiment decline",
                    "description": "CSAT dropped from 4.5 to 4.0",
                    "contribution": 0.04,
                    "mitigation": "Review recent tickets and address systemic issues"
                },
                {
                    "factor": "Feature adoption plateau",
                    "description": "No new feature adoption in 90 days",
                    "contribution": 0.03,
                    "mitigation": "Conduct feature discovery session"
                }
            ],
            "protective_factors": [
                {"factor": "Strong executive relationship", "contribution": -0.08},
                {"factor": "High product stickiness", "contribution": -0.06},
                {"factor": "Recent expansion", "contribution": -0.05}
            ],
            "similar_churned_accounts": [
                {"account": "Former Customer A", "similarity": 0.72, "churn_reason": "Stakeholder change"},
                {"account": "Former Customer B", "similarity": 0.65, "churn_reason": "Competitor switch"}
            ],
            "recommended_actions": [
                {"action": "Executive check-in call", "priority": "High", "timeline": "This week"},
                {"action": "Product roadmap preview", "priority": "Medium", "timeline": "Next 2 weeks"},
                {"action": "Success story development", "priority": "Low", "timeline": "This quarter"}
            ]
        }

        return json.dumps({"status": "success", "churn_prediction": churn}, indent=2)

    def _identify_expansion_opportunities(self, customer_id: str, params: Dict) -> str:
        """Identify cross-sell and upsell opportunities."""

        opportunities = {
            "customer_id": customer_id,
            "total_expansion_potential": "$150,000",
            "opportunities": [
                {
                    "opportunity_type": "Upsell",
                    "product": "Advanced Analytics Module",
                    "potential_arr": "$75,000",
                    "probability": 0.70,
                    "signals": [
                        "Frequently exports data for external analysis",
                        "Asked about predictive capabilities in QBR",
                        "Competitor using similar capability"
                    ],
                    "recommended_approach": "ROI-focused demo showing time savings",
                    "best_contact": "VP of Data Science",
                    "timing": "Q2 2026"
                },
                {
                    "opportunity_type": "Cross-sell",
                    "product": "API Access Package",
                    "potential_arr": "$50,000",
                    "probability": 0.55,
                    "signals": [
                        "Engineering team requested API documentation",
                        "Building internal data warehouse",
                        "Mentioned integration needs"
                    ],
                    "recommended_approach": "Technical deep-dive with engineering lead",
                    "best_contact": "CTO",
                    "timing": "Q1 2026"
                },
                {
                    "opportunity_type": "Expansion",
                    "product": "Additional Seats (100)",
                    "potential_arr": "$25,000",
                    "probability": 0.80,
                    "signals": [
                        "Marketing department interested",
                        "Seat utilization at 98%",
                        "Budget approval in progress"
                    ],
                    "recommended_approach": "Volume discount proposal",
                    "best_contact": "VP of Marketing",
                    "timing": "This month"
                }
            ],
            "whitespace_analysis": {
                "products_owned": ["Platform Pro", "Analytics Suite", "Integration Hub"],
                "products_not_owned": ["Advanced Analytics", "API Access", "Premium Support"],
                "peer_comparison": "Similar companies typically have 2 more products"
            }
        }

        return json.dumps({"status": "success", "expansion_opportunities": opportunities}, indent=2)

    def _get_stakeholder_map(self, customer_id: str, params: Dict) -> str:
        """Get stakeholder map with influence and engagement levels."""

        stakeholders = {
            "customer_id": customer_id,
            "stakeholder_count": 8,
            "stakeholders": [
                {
                    "name": "Demo Exec 1",
                    "title": "VP of Operations",
                    "influence": "Decision Maker",
                    "sentiment": "Champion",
                    "engagement_score": 95,
                    "last_contact": "2026-01-10",
                    "notes": "Strong advocate, drives internal adoption"
                },
                {
                    "name": "Robert Kim",
                    "title": "CTO",
                    "influence": "Technical Authority",
                    "sentiment": "Supportive",
                    "engagement_score": 72,
                    "last_contact": "2025-12-05",
                    "notes": "Interested in API capabilities, needs technical depth"
                },
                {
                    "name": "Demo Contact B",
                    "title": "CFO",
                    "influence": "Budget Authority",
                    "sentiment": "Neutral",
                    "engagement_score": 45,
                    "last_contact": "2025-09-15",
                    "notes": "Limited engagement - needs ROI story"
                },
                {
                    "name": "David Chen",
                    "title": "Director of Analytics",
                    "influence": "User Champion",
                    "sentiment": "Champion",
                    "engagement_score": 88,
                    "last_contact": "2026-01-08",
                    "notes": "Power user, great reference candidate"
                }
            ],
            "engagement_gaps": [
                {"stakeholder": "Demo Contact B (CFO)", "days_since_contact": 115, "risk": "High"},
                {"stakeholder": "New VP of Sales", "days_since_contact": "Never contacted", "risk": "High"}
            ],
            "recent_changes": [
                {"change": "New VP of Sales hired", "date": "2025-12-01", "impact": "Unknown"},
                {"change": "Director of IT departed", "date": "2025-11-15", "impact": "Low"}
            ],
            "recommended_actions": [
                "Schedule CFO meeting to present ROI analysis",
                "Introduce to new VP of Sales within 2 weeks",
                "Leverage Demo Exec 1 for executive sponsorship"
            ]
        }

        return json.dumps({"status": "success", "stakeholder_map": stakeholders}, indent=2)

    def _prepare_meeting_brief(self, customer_id: str, params: Dict) -> str:
        """Prepare comprehensive meeting brief for customer interaction."""

        brief = {
            "customer_id": customer_id,
            "customer_name": "Acme Corporation",
            "meeting_date": datetime.now().strftime("%Y-%m-%d"),
            "prepared_for": "Quarterly Business Review",
            "executive_summary": "Strong customer with 78 health score. Recent support ticket spike resolved. Expansion opportunity for Advanced Analytics. Key risk: CFO engagement gap.",
            "key_metrics": {
                "arr": "$450,000",
                "health_score": 78,
                "nps": 8,
                "adoption_rate": "84.6%",
                "days_to_renewal": 365
            },
            "talking_points": [
                "Celebrate: 15% DAU increase and successful Q4 rollout",
                "Address: Support ticket resolution and preventive measures",
                "Explore: Advanced Analytics interest for data science team",
                "Introduce: New customer success resources"
            ],
            "questions_to_ask": [
                "How has the new VP of Sales onboarded to the platform?",
                "What are your top priorities for 2026?",
                "How can we better support the data science team's needs?",
                "Are there other departments that could benefit from the platform?"
            ],
            "risks_to_monitor": [
                "CFO not engaged - may impact renewal discussions",
                "New VP of Sales unfamiliar with value delivered",
                "Support satisfaction dipped - need to demonstrate improvement"
            ],
            "opportunities_to_present": [
                "Advanced Analytics module demo",
                "Case study from similar company",
                "Expansion pricing for marketing team seats"
            ],
            "recent_support_summary": {
                "open_tickets": 2,
                "avg_resolution_time": "4.2 hours",
                "csat_trend": "Improving"
            },
            "competitive_intelligence": {
                "known_competitors_evaluated": ["Competitor A", "Competitor B"],
                "last_competitive_threat": "2025-06-15",
                "win_factors": ["Integration depth", "Customer support"]
            }
        }

        return json.dumps({"status": "success", "meeting_brief": brief}, indent=2)

    def _get_engagement_gaps(self, customer_id: str, params: Dict) -> str:
        """Identify engagement gaps across stakeholders and touchpoints."""

        gaps = {
            "customer_id": customer_id,
            "stakeholder_gaps": [
                {"stakeholder": "CFO", "gap_days": 115, "recommended_action": "ROI review meeting"},
                {"stakeholder": "New VP Sales", "gap_days": "Never", "recommended_action": "Introduction call"},
                {"stakeholder": "IT Director", "gap_days": 45, "recommended_action": "Technical check-in"}
            ],
            "product_adoption_gaps": [
                {"feature": "Advanced Analytics", "adoption": "12%", "benchmark": "65%"},
                {"feature": "API Access", "adoption": "0%", "benchmark": "45%"},
                {"feature": "Mobile App", "adoption": "23%", "benchmark": "55%"}
            ],
            "communication_gaps": [
                {"channel": "Product Updates", "last_sent": "45 days ago", "benchmark": "Monthly"},
                {"channel": "Training Resources", "last_sent": "90 days ago", "benchmark": "Quarterly"}
            ],
            "process_gaps": [
                {"process": "Executive Business Review", "status": "Overdue", "last": "4 months ago"},
                {"process": "Technical Health Check", "status": "Due", "last": "6 months ago"}
            ],
            "recommended_90_day_plan": [
                {"week": 1, "action": "CFO ROI presentation"},
                {"week": 2, "action": "VP Sales introduction"},
                {"week": 3, "action": "Advanced Analytics training"},
                {"week": 4, "action": "Technical health check"},
                {"week": 8, "action": "Executive Business Review"},
                {"week": 12, "action": "Expansion proposal presentation"}
            ]
        }

        return json.dumps({"status": "success", "engagement_gaps": gaps}, indent=2)

    def _generate_retention_playbook(self, customer_id: str, params: Dict) -> str:
        """Generate customized retention playbook for at-risk account."""

        playbook = {
            "customer_id": customer_id,
            "risk_level": "Medium",
            "churn_probability": 0.25,
            "playbook_type": "Proactive Retention",
            "30_day_actions": [
                {
                    "day": 1,
                    "action": "Executive sponsor call",
                    "owner": "CSM",
                    "objective": "Reaffirm commitment and understand concerns",
                    "talking_points": ["Value delivered", "Roadmap preview", "Support commitment"]
                },
                {
                    "day": 7,
                    "action": "Technical deep-dive session",
                    "owner": "Solutions Engineer",
                    "objective": "Address technical concerns and showcase advanced features"
                },
                {
                    "day": 14,
                    "action": "ROI review with finance",
                    "owner": "CSM + AE",
                    "objective": "Quantify value and address budget concerns"
                },
                {
                    "day": 21,
                    "action": "Success story development",
                    "owner": "Marketing + CSM",
                    "objective": "Create internal champions and external validation"
                },
                {
                    "day": 30,
                    "action": "Strategic planning session",
                    "owner": "CSM",
                    "objective": "Align on 2026 goals and expansion roadmap"
                }
            ],
            "escalation_triggers": [
                "No response to executive outreach within 5 days",
                "Competitor mentioned in any communication",
                "Budget freeze or organizational change announced",
                "Usage drops more than 20% in any week"
            ],
            "resources_available": [
                "Executive sponsor: VP of Customer Success",
                "Technical resource: Senior Solutions Architect",
                "Concession authority: Up to 15% discount or 3 months free"
            ],
            "success_metrics": [
                "Health score improvement to 80+",
                "NPS improvement to 9+",
                "Renewal commitment by end of quarter"
            ]
        }

        return json.dumps({"status": "success", "retention_playbook": playbook}, indent=2)
