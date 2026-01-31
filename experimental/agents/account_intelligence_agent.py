"""
Account Intelligence Agent - B2B Sales Pipeline Analytics
Generated via RAPP Pipeline Process

Industry: B2B Sales
Use Case: Pipeline health analysis, stalled deal detection, competitive intelligence

Key Outcomes:
- Pipeline visibility with deal-level metrics and trends
- Stalled deal identification with root cause analysis
- Account health scoring and risk identification
- Revenue at risk quantification

Target Users: Sales Managers, Account Executives, Sales Leadership
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class AccountIntelligenceAgent(BasicAgent):
    """
    AI-powered account intelligence for B2B sales teams providing
    pipeline analytics, deal progression tracking, and competitive insights.
    """

    def __init__(self):
        self.name = 'AccountIntelligence'
        self.metadata = {
            "name": self.name,
            "description": "Analyzes B2B sales pipeline health, identifies stalled deals, provides competitive intelligence, and recommends next-best-actions for account executives.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "analyze_pipeline",
                            "identify_stalled_deals",
                            "get_account_health",
                            "get_competitive_intel",
                            "recommend_actions",
                            "quantify_risk",
                            "get_org_chart",
                            "forecast_revenue"
                        ],
                        "description": "Action to perform"
                    },
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    },
                    "deal_id": {
                        "type": "string",
                        "description": "Specific deal/opportunity ID"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["this_quarter", "next_quarter", "this_year"],
                        "description": "Time period for analysis"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action', 'analyze_pipeline')
        logger.info(f"AccountIntelligenceAgent performing action: {action}")

        try:
            if action == 'analyze_pipeline':
                return self._analyze_pipeline(kwargs)
            elif action == 'identify_stalled_deals':
                return self._identify_stalled_deals(kwargs)
            elif action == 'get_account_health':
                return self._get_account_health(kwargs.get('account_id'), kwargs)
            elif action == 'get_competitive_intel':
                return self._get_competitive_intel(kwargs.get('account_id'), kwargs)
            elif action == 'recommend_actions':
                return self._recommend_actions(kwargs.get('deal_id'), kwargs)
            elif action == 'quantify_risk':
                return self._quantify_risk(kwargs)
            elif action == 'get_org_chart':
                return self._get_org_chart(kwargs.get('account_id'), kwargs)
            elif action == 'forecast_revenue':
                return self._forecast_revenue(kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"AccountIntelligenceAgent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _analyze_pipeline(self, params: Dict) -> str:
        """Analyze overall pipeline health with deal-level metrics."""

        pipeline = {
            "analysis_date": datetime.now().isoformat(),
            "time_period": params.get('time_period', 'this_quarter'),
            "summary": {
                "total_pipeline": "$18.2M",
                "weighted_pipeline": "$12.4M",
                "deal_count": 47,
                "avg_deal_size": "$387K",
                "pipeline_coverage": "3.2x quota",
                "health_score": 72
            },
            "by_stage": [
                {"stage": "Discovery", "value": "$3.2M", "count": 15, "avg_age": 12},
                {"stage": "Qualification", "value": "$4.8M", "count": 12, "avg_age": 28},
                {"stage": "Proposal", "value": "$5.1M", "count": 10, "avg_age": 35},
                {"stage": "Negotiation", "value": "$3.5M", "count": 7, "avg_age": 21},
                {"stage": "Closing", "value": "$1.6M", "count": 3, "avg_age": 14}
            ],
            "velocity_metrics": {
                "avg_sales_cycle": 78,
                "benchmark": 65,
                "stage_conversion": {
                    "discovery_to_qual": "65%",
                    "qual_to_proposal": "58%",
                    "proposal_to_nego": "72%",
                    "nego_to_close": "45%"
                }
            },
            "risk_indicators": {
                "stalled_deals": {"count": 8, "value": "$4.2M"},
                "no_activity_7d": {"count": 12, "value": "$3.8M"},
                "missing_close_date": {"count": 5, "value": "$1.9M"},
                "single_threaded": {"count": 15, "value": "$5.2M"}
            },
            "opportunities": {
                "quick_wins": {"count": 4, "value": "$810K"},
                "upside_potential": {"count": 6, "value": "$2.1M"},
                "add_to_commit": {"count": 3, "value": "$1.4M"}
            }
        }

        return json.dumps({"status": "success", "pipeline_analysis": pipeline}, indent=2)

    def _identify_stalled_deals(self, params: Dict) -> str:
        """Identify deals stuck beyond normal velocity thresholds."""

        stalled = {
            "analysis_date": datetime.now().isoformat(),
            "total_stalled": "$4.2M",
            "stalled_count": 8,
            "deals": [
                {
                    "deal_id": "OPP-001",
                    "account": "TechCorp Industries",
                    "value": "$850K",
                    "stage": "Proposal",
                    "days_in_stage": 45,
                    "expected_days": 21,
                    "owner": "Demo Rep 2",
                    "root_cause": "Missing economic buyer engagement",
                    "last_activity": "2026-01-02",
                    "recommended_actions": [
                        "Request executive sponsor introduction",
                        "Develop CFO-specific ROI analysis",
                        "Propose limited pilot to reduce risk"
                    ]
                },
                {
                    "deal_id": "OPP-002",
                    "account": "Global Manufacturing",
                    "value": "$620K",
                    "stage": "Negotiation",
                    "days_in_stage": 32,
                    "expected_days": 14,
                    "owner": "Demo Rep 3",
                    "root_cause": "Competitive evaluation underway",
                    "last_activity": "2026-01-08",
                    "recommended_actions": [
                        "Request competitive clarification call",
                        "Prepare differentiation deck",
                        "Offer proof-of-concept"
                    ]
                },
                {
                    "deal_id": "OPP-003",
                    "account": "Financial Services Co",
                    "value": "$1.2M",
                    "stage": "Qualification",
                    "days_in_stage": 52,
                    "expected_days": 28,
                    "owner": "Demo Exec 1",
                    "root_cause": "Budget cycle misalignment",
                    "last_activity": "2025-12-20",
                    "recommended_actions": [
                        "Confirm new budget timeline",
                        "Propose bridge arrangement",
                        "Identify quick-win module"
                    ]
                }
            ],
            "common_root_causes": [
                {"cause": "Missing stakeholder engagement", "frequency": 4},
                {"cause": "Competitive evaluation", "frequency": 2},
                {"cause": "Budget/timing issues", "frequency": 2}
            ],
            "recovery_potential": {
                "high": {"count": 3, "value": "$1.8M"},
                "medium": {"count": 3, "value": "$1.5M"},
                "low": {"count": 2, "value": "$0.9M"}
            }
        }

        return json.dumps({"status": "success", "stalled_deals": stalled}, indent=2)

    def _get_account_health(self, account_id: str, params: Dict) -> str:
        """Get comprehensive account health assessment."""

        health = {
            "account_id": account_id or "ACCT-001",
            "account_name": "TechCorp Industries",
            "health_score": 68,
            "score_components": {
                "engagement": {"score": 72, "trend": "Declining"},
                "stakeholder_coverage": {"score": 55, "trend": "Stable"},
                "competitive_position": {"score": 78, "trend": "Improving"},
                "deal_momentum": {"score": 62, "trend": "Declining"},
                "relationship_depth": {"score": 71, "trend": "Stable"}
            },
            "active_opportunities": [
                {"deal": "Platform Expansion", "value": "$850K", "stage": "Proposal", "probability": 0.45},
                {"deal": "Services Add-on", "value": "$120K", "stage": "Negotiation", "probability": 0.75}
            ],
            "relationship_map": {
                "champions": 2,
                "supporters": 3,
                "neutral": 4,
                "detractors": 1,
                "unknown": 5
            },
            "recent_signals": [
                {"signal": "CTO visited pricing page 3x this week", "type": "Positive"},
                {"signal": "CFO opened competitor email", "type": "Risk"},
                {"signal": "New project announced", "type": "Opportunity"}
            ],
            "risk_factors": [
                "CFO engagement gap (no contact in 45 days)",
                "Competitor actively pursuing account",
                "Primary champion moving to new role"
            ],
            "recommended_actions": [
                {"action": "Schedule CFO meeting", "priority": "High", "owner": "AE"},
                {"action": "Competitive displacement strategy", "priority": "High", "owner": "SE"},
                {"action": "Champion succession planning", "priority": "Medium", "owner": "CSM"}
            ]
        }

        return json.dumps({"status": "success", "account_health": health}, indent=2)

    def _get_competitive_intel(self, account_id: str, params: Dict) -> str:
        """Get competitive intelligence for account."""

        intel = {
            "account_id": account_id or "ACCT-001",
            "competitive_landscape": {
                "primary_competitors": ["Competitor A", "Competitor B"],
                "active_evaluation": True,
                "incumbent": "None (greenfield)",
                "competitive_threat_level": "Medium"
            },
            "competitor_analysis": [
                {
                    "competitor": "Competitor A",
                    "presence": "Evaluating",
                    "strengths": ["Price", "Local support", "Integration ecosystem"],
                    "weaknesses": ["Scalability", "AI capabilities", "Enterprise features"],
                    "win_strategy": "Focus on enterprise scale and AI differentiation",
                    "recent_activity": "Demo scheduled for next week"
                },
                {
                    "competitor": "Competitor B",
                    "presence": "Initial discussions",
                    "strengths": ["Brand recognition", "Analyst rankings"],
                    "weaknesses": ["Implementation complexity", "Total cost of ownership"],
                    "win_strategy": "Emphasize faster time-to-value and lower TCO",
                    "recent_activity": "Sent pricing information"
                }
            ],
            "differentiation_talking_points": [
                "3x faster implementation vs Competitor A",
                "40% lower TCO over 3 years vs Competitor B",
                "Native AI capabilities vs bolt-on solutions",
                "Customer references in same industry"
            ],
            "objection_handlers": {
                "Price concern": "Total cost of ownership analysis shows 40% savings over 3 years",
                "Unknown vendor": "Reference calls with Fortune 500 customers available",
                "Feature gap": "Roadmap addresses requirement in Q2, can provide early access"
            },
            "win_rate_vs_competitors": {
                "Competitor A": "62%",
                "Competitor B": "58%",
                "Overall": "55%"
            }
        }

        return json.dumps({"status": "success", "competitive_intelligence": intel}, indent=2)

    def _recommend_actions(self, deal_id: str, params: Dict) -> str:
        """Generate next-best-action recommendations for a deal."""

        recommendations = {
            "deal_id": deal_id or "OPP-001",
            "deal_name": "TechCorp Platform Expansion",
            "current_stage": "Proposal",
            "deal_value": "$850K",
            "recommended_actions": [
                {
                    "priority": 1,
                    "action": "Schedule CFO meeting for ROI review",
                    "rationale": "Economic buyer not engaged - blocking progression",
                    "suggested_approach": "Leverage CTO relationship for introduction",
                    "template_available": True,
                    "estimated_impact": "High - likely to unblock deal"
                },
                {
                    "priority": 2,
                    "action": "Deliver competitive differentiation deck",
                    "rationale": "Competitor A demo scheduled - need to reinforce value",
                    "suggested_approach": "Focus on AI capabilities and TCO",
                    "template_available": True,
                    "estimated_impact": "Medium - defensive move"
                },
                {
                    "priority": 3,
                    "action": "Propose limited proof-of-concept",
                    "rationale": "Reduce perceived risk and create urgency",
                    "suggested_approach": "30-day pilot with success metrics",
                    "template_available": True,
                    "estimated_impact": "Medium - accelerate decision"
                }
            ],
            "information_gaps": [
                "Budget confirmation and approval process",
                "Complete stakeholder map (missing IT and Legal)",
                "Decision timeline and competing priorities"
            ],
            "stakeholder_actions": {
                "CTO (Champion)": "Confirm executive sponsor role, request CFO intro",
                "VP Ops (User)": "Validate technical requirements and success criteria",
                "CFO (Economic)": "Schedule ROI review meeting"
            },
            "meeting_suggestions": [
                {
                    "meeting_type": "Executive ROI Review",
                    "attendees": ["CFO", "CTO", "VP Ops"],
                    "agenda": ["Value delivered to date", "Expansion ROI", "Investment timeline"],
                    "suggested_date": "Within 7 days"
                }
            ]
        }

        return json.dumps({"status": "success", "recommendations": recommendations}, indent=2)

    def _quantify_risk(self, params: Dict) -> str:
        """Quantify revenue at risk across portfolio."""

        risk = {
            "analysis_date": datetime.now().isoformat(),
            "time_period": params.get('time_period', 'this_quarter'),
            "total_at_risk": "$5.1M",
            "risk_breakdown": {
                "high_risk": {
                    "value": "$2.1M",
                    "count": 5,
                    "deals": [
                        {"deal": "TechCorp Expansion", "value": "$850K", "risk_reason": "Competitive threat"},
                        {"deal": "Financial Services Deal", "value": "$1.2M", "risk_reason": "Budget freeze"}
                    ]
                },
                "medium_risk": {
                    "value": "$1.8M",
                    "count": 7,
                    "deals": [
                        {"deal": "Healthcare Pilot", "value": "$400K", "risk_reason": "Slow procurement"},
                        {"deal": "Retail Expansion", "value": "$550K", "risk_reason": "Champion leaving"}
                    ]
                },
                "low_risk": {
                    "value": "$1.2M",
                    "count": 8
                }
            },
            "risk_by_category": {
                "competitive": {"value": "$1.5M", "percentage": "29%"},
                "budget_timing": {"value": "$1.8M", "percentage": "35%"},
                "stakeholder": {"value": "$1.1M", "percentage": "22%"},
                "technical": {"value": "$0.7M", "percentage": "14%"}
            },
            "mitigation_impact": {
                "addressable": "$3.8M",
                "mitigation_actions": 12,
                "expected_recovery": "$2.4M"
            },
            "week_over_week_trend": {
                "at_risk_change": "+$400K",
                "new_risks": 2,
                "risks_mitigated": 1
            }
        }

        return json.dumps({"status": "success", "risk_quantification": risk}, indent=2)

    def _get_org_chart(self, account_id: str, params: Dict) -> str:
        """Get organizational chart and stakeholder intelligence."""

        org_chart = {
            "account_id": account_id or "ACCT-001",
            "account_name": "TechCorp Industries",
            "org_structure": {
                "executives": [
                    {"name": "Demo User", "title": "CEO", "engagement": "None", "priority": "Low"},
                    {"name": "Demo Contact A", "title": "CFO", "engagement": "Low", "priority": "High"},
                    {"name": "Demo Rep 1", "title": "CTO", "engagement": "High", "priority": "High"}
                ],
                "decision_makers": [
                    {"name": "Lisa Wang", "title": "VP Operations", "engagement": "Medium", "role": "User Buyer"},
                    {"name": "David Kim", "title": "VP IT", "engagement": "Low", "role": "Technical Buyer"}
                ],
                "influencers": [
                    {"name": "Emily Brown", "title": "Director Analytics", "engagement": "High", "role": "Champion"},
                    {"name": "James Wilson", "title": "IT Manager", "engagement": "Medium", "role": "Evaluator"}
                ]
            },
            "buying_committee": {
                "identified": 7,
                "engaged": 4,
                "coverage_score": "57%",
                "gaps": ["Legal (unknown)", "Procurement (unknown)", "CFO (low engagement)"]
            },
            "relationship_strength": {
                "champions": ["Emily Brown", "Demo Rep 1"],
                "supporters": ["Lisa Wang"],
                "neutral": ["James Wilson", "David Kim"],
                "blockers": [],
                "unknown": ["Demo Contact A", "Demo User"]
            },
            "recommended_mapping_actions": [
                "Identify Legal and Procurement contacts",
                "Increase CFO engagement through CTO introduction",
                "Develop backup champion (Lisa Wang)"
            ]
        }

        return json.dumps({"status": "success", "org_chart": org_chart}, indent=2)

    def _forecast_revenue(self, params: Dict) -> str:
        """Generate revenue forecast with confidence intervals."""

        forecast = {
            "time_period": params.get('time_period', 'this_quarter'),
            "quota": "$5.7M",
            "forecast": {
                "commit": {"value": "$4.8M", "deals": 12, "probability": "90%+"},
                "best_case": {"value": "$6.2M", "deals": 18, "probability": "50%+"},
                "upside": {"value": "$7.8M", "deals": 25, "probability": "25%+"}
            },
            "coverage_analysis": {
                "commit_to_quota": "84%",
                "best_case_to_quota": "109%",
                "gap_to_commit": "$0.9M",
                "deals_to_close_gap": 3
            },
            "forecast_risks": [
                {"risk": "Two large deals in competitive evaluation", "impact": "-$1.2M"},
                {"risk": "Q1 budget freezes at 3 accounts", "impact": "-$0.6M"}
            ],
            "forecast_opportunities": [
                {"opportunity": "Acceleration of Healthcare pilot", "impact": "+$0.4M"},
                {"opportunity": "Early close on negotiation deals", "impact": "+$0.8M"}
            ],
            "confidence_score": 72,
            "forecast_accuracy_history": {
                "last_quarter": "94%",
                "ytd_average": "91%"
            }
        }

        return json.dumps({"status": "success", "revenue_forecast": forecast}, indent=2)
