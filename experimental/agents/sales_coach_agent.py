"""
Sales Coach Agent - AI-Powered Sales Training
Generated via RAPP Pipeline Process

Industry: Cross-Industry (Sales Enablement)
Use Case: Analyze sales calls, assess skills, provide personalized coaching

Key Outcomes:
- Close rate improvement from 18% to 24%
- Skill score improvements through targeted coaching
- Data-driven coaching at scale
- Deal rescue strategies for active opportunities

Target Users: Sales Reps, Sales Managers, Sales Enablement Directors
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class SalesCoachAgent(BasicAgent):
    """
    AI-powered sales coaching agent for call analysis, skill assessment,
    and personalized improvement recommendations.
    """

    def __init__(self):
        self.name = 'SalesCoach'
        self.metadata = {
            "name": self.name,
            "description": "Analyzes sales calls for effectiveness, assesses rep skills against competency frameworks, generates personalized coaching recommendations, and provides deal rescue strategies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "analyze_call",
                            "assess_skills",
                            "generate_coaching_plan",
                            "provide_deal_strategy",
                            "track_progress",
                            "compare_to_benchmark",
                            "simulate_objection"
                        ],
                        "description": "Action to perform"
                    },
                    "rep_id": {
                        "type": "string",
                        "description": "Sales representative identifier"
                    },
                    "call_id": {
                        "type": "string",
                        "description": "Call recording identifier"
                    },
                    "deal_id": {
                        "type": "string",
                        "description": "Deal/opportunity identifier"
                    },
                    "skill_area": {
                        "type": "string",
                        "enum": ["discovery", "qualification", "presentation", "objection_handling", "closing", "overall"],
                        "description": "Specific skill area to focus on"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Skill competency framework
        self.competencies = {
            "discovery": ["Open-ended questions", "Active listening", "Need identification", "Pain point exploration"],
            "qualification": ["BANT assessment", "Decision process mapping", "Stakeholder identification", "Budget validation"],
            "presentation": ["Value articulation", "Storytelling", "Demo effectiveness", "Customization"],
            "objection_handling": ["Empathy", "Reframing", "Evidence provision", "Competitive positioning"],
            "closing": ["Trial closes", "Urgency creation", "Commitment securing", "Next steps clarity"]
        }

    def perform(self, **kwargs) -> str:
        action = kwargs.get('action', 'analyze_call')
        logger.info(f"SalesCoachAgent performing action: {action}")

        try:
            if action == 'analyze_call':
                return self._analyze_call(kwargs.get('call_id'), kwargs)
            elif action == 'assess_skills':
                return self._assess_skills(kwargs.get('rep_id'), kwargs)
            elif action == 'generate_coaching_plan':
                return self._generate_coaching_plan(kwargs.get('rep_id'), kwargs)
            elif action == 'provide_deal_strategy':
                return self._provide_deal_strategy(kwargs.get('deal_id'), kwargs)
            elif action == 'track_progress':
                return self._track_progress(kwargs.get('rep_id'), kwargs)
            elif action == 'compare_to_benchmark':
                return self._compare_to_benchmark(kwargs.get('rep_id'), kwargs)
            elif action == 'simulate_objection':
                return self._simulate_objection(kwargs)
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"SalesCoachAgent error: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})

    def _analyze_call(self, call_id: str, params: Dict) -> str:
        """Analyze sales call for key moments and effectiveness."""

        analysis = {
            "call_id": call_id or "CALL-001",
            "analyzed_at": datetime.now().isoformat(),
            "call_metadata": {
                "rep": "Demo Rep 2",
                "customer": "TechCorp Industries",
                "deal": "Platform Expansion",
                "deal_value": "$850K",
                "call_type": "Discovery",
                "duration": "42 minutes",
                "date": "2026-01-15"
            },
            "talk_metrics": {
                "talk_ratio": {"rep": "45%", "customer": "55%", "benchmark": "40/60"},
                "longest_monologue": "2:15 (benchmark: <2:00)",
                "questions_asked": 18,
                "open_ended_questions": 12,
                "filler_words": "Low (3 per minute)"
            },
            "key_moments": [
                {
                    "timestamp": "03:45",
                    "type": "Pain Point Uncovered",
                    "description": "Customer revealed manual reporting takes 20 hours weekly",
                    "significance": "High - quantifiable pain point",
                    "coaching_note": "Good follow-up questions to quantify impact"
                },
                {
                    "timestamp": "12:30",
                    "type": "Objection Raised",
                    "description": "Customer concerned about implementation timeline",
                    "significance": "Medium - common objection",
                    "coaching_note": "Response was adequate but could leverage customer references"
                },
                {
                    "timestamp": "28:15",
                    "type": "Competitor Mentioned",
                    "description": "Customer comparing to Competitor A",
                    "significance": "High - competitive situation",
                    "coaching_note": "Missed opportunity to differentiate on AI capabilities"
                },
                {
                    "timestamp": "38:00",
                    "type": "Next Steps",
                    "description": "Scheduled demo for next week",
                    "significance": "High - deal progression",
                    "coaching_note": "Strong close, confirmed attendees and agenda"
                }
            ],
            "skill_scores": {
                "discovery": 82,
                "qualification": 75,
                "objection_handling": 68,
                "closing": 85,
                "overall": 78
            },
            "sentiment_analysis": {
                "customer_sentiment": "Positive (trending up)",
                "engagement_level": "High",
                "buying_signals": ["Asked about implementation", "Discussed internal stakeholders", "Requested pricing info"]
            },
            "coaching_recommendations": [
                {
                    "priority": "High",
                    "area": "Competitive Differentiation",
                    "recommendation": "When competitor mentioned, immediately pivot to unique AI capabilities",
                    "example_response": "That's a great comparison. What sets us apart is our native AI that..."
                },
                {
                    "priority": "Medium",
                    "area": "Objection Handling",
                    "recommendation": "Use customer references when addressing implementation concerns",
                    "example_response": "I understand timeline concerns. Let me share how TechCorp implemented in 6 weeks..."
                }
            ],
            "deal_impact": {
                "deal_health": "Positive",
                "stage_recommendation": "Advance to Proposal",
                "risk_factors": ["Competitive evaluation in progress"],
                "next_actions": ["Send competitive comparison", "Confirm demo attendees", "Prepare ROI analysis"]
            }
        }

        return json.dumps({"status": "success", "call_analysis": analysis}, indent=2)

    def _assess_skills(self, rep_id: str, params: Dict) -> str:
        """Assess rep skills against competency framework."""

        assessment = {
            "rep_id": rep_id or "REP-001",
            "rep_name": "Demo Rep 2",
            "assessment_date": datetime.now().isoformat(),
            "assessment_period": "Last 30 days",
            "calls_analyzed": 24,
            "overall_score": 74,
            "skill_breakdown": {
                "discovery": {
                    "score": 82,
                    "trend": "+5 from last month",
                    "strengths": ["Open-ended questions", "Pain point exploration"],
                    "improvement_areas": ["Technical need identification"],
                    "benchmark_comparison": "Above average (team avg: 75)"
                },
                "qualification": {
                    "score": 75,
                    "trend": "Stable",
                    "strengths": ["Stakeholder identification", "Timeline mapping"],
                    "improvement_areas": ["Budget validation", "Decision process"],
                    "benchmark_comparison": "Average (team avg: 76)"
                },
                "presentation": {
                    "score": 78,
                    "trend": "+3 from last month",
                    "strengths": ["Value articulation", "Storytelling"],
                    "improvement_areas": ["Demo customization"],
                    "benchmark_comparison": "Above average (team avg: 72)"
                },
                "objection_handling": {
                    "score": 68,
                    "trend": "-2 from last month",
                    "strengths": ["Empathy"],
                    "improvement_areas": ["Competitive positioning", "Evidence provision"],
                    "benchmark_comparison": "Below average (team avg: 74)"
                },
                "closing": {
                    "score": 54,
                    "trend": "Stable",
                    "strengths": ["Next steps clarity"],
                    "improvement_areas": ["Trial closes", "Urgency creation", "Commitment securing"],
                    "benchmark_comparison": "Needs improvement (team avg: 72)"
                }
            },
            "key_metrics": {
                "win_rate": "18%",
                "avg_deal_size": "$320K",
                "sales_cycle": "85 days",
                "pipeline_coverage": "2.8x"
            },
            "top_performers_comparison": {
                "top_performer_win_rate": "32%",
                "gap_analysis": "14 percentage points",
                "differentiating_behaviors": [
                    "2x more trial closes per call",
                    "45% more customer references cited",
                    "Stronger urgency creation techniques"
                ]
            },
            "priority_development_areas": [
                {"skill": "Closing", "gap": "18 points", "impact": "High - directly affects win rate"},
                {"skill": "Objection Handling", "gap": "6 points", "impact": "Medium - affects competitive deals"}
            ]
        }

        return json.dumps({"status": "success", "skill_assessment": assessment}, indent=2)

    def _generate_coaching_plan(self, rep_id: str, params: Dict) -> str:
        """Generate personalized coaching plan."""

        plan = {
            "rep_id": rep_id or "REP-001",
            "rep_name": "Demo Rep 2",
            "plan_created": datetime.now().isoformat(),
            "plan_duration": "30 days",
            "primary_focus": "Closing Skills Improvement",
            "target_outcome": "Improve closing score from 54 to 70, increase win rate from 18% to 24%",
            "weekly_structure": {
                "week_1": {
                    "theme": "Foundation - Understanding Closing Psychology",
                    "activities": [
                        {"type": "Learning", "content": "Closing techniques masterclass (45 min)", "completed": False},
                        {"type": "Exercise", "content": "Identify 3 trial close opportunities in past calls", "completed": False},
                        {"type": "Practice", "content": "Role play: 2 closing scenarios with peer", "completed": False}
                    ],
                    "coaching_session": "30-min 1:1 with manager - Review call recordings"
                },
                "week_2": {
                    "theme": "Trial Closes and Micro-Commitments",
                    "activities": [
                        {"type": "Learning", "content": "Trial close technique library", "completed": False},
                        {"type": "Application", "content": "Use 3 trial closes in live calls", "completed": False},
                        {"type": "Review", "content": "Self-assess trial close effectiveness", "completed": False}
                    ],
                    "coaching_session": "30-min 1:1 with manager - Real-time call coaching"
                },
                "week_3": {
                    "theme": "Creating Urgency and Handling Stalls",
                    "activities": [
                        {"type": "Learning", "content": "Urgency creation without pressure tactics", "completed": False},
                        {"type": "Exercise", "content": "Develop 5 urgency statements for your deals", "completed": False},
                        {"type": "Practice", "content": "Stall-handling role play", "completed": False}
                    ],
                    "coaching_session": "30-min 1:1 with manager - Deal strategy session"
                },
                "week_4": {
                    "theme": "Integration and Measurement",
                    "activities": [
                        {"type": "Application", "content": "Apply all techniques in live calls", "completed": False},
                        {"type": "Review", "content": "Analyze 5 calls for closing improvements", "completed": False},
                        {"type": "Assessment", "content": "Final skill assessment", "completed": False}
                    ],
                    "coaching_session": "30-min 1:1 with manager - Progress review and next steps"
                }
            },
            "resources": [
                {"type": "Video", "title": "The Psychology of Closing", "duration": "12 min"},
                {"type": "Article", "title": "15 Trial Close Techniques That Work", "read_time": "8 min"},
                {"type": "Template", "title": "Urgency Creation Framework", "type": "PDF"},
                {"type": "Recording", "title": "Top Performer Call Examples", "duration": "25 min"}
            ],
            "success_metrics": [
                {"metric": "Closing skill score", "current": 54, "target": 70},
                {"metric": "Trial closes per call", "current": 1.2, "target": 3.0},
                {"metric": "Win rate", "current": "18%", "target": "24%"},
                {"metric": "Deals progressed to close", "current": 3, "target": 5}
            ],
            "manager_checkpoints": [
                {"date": "Week 1 Friday", "focus": "Foundation understanding"},
                {"date": "Week 2 Friday", "focus": "Trial close application"},
                {"date": "Week 3 Friday", "focus": "Urgency techniques"},
                {"date": "Week 4 Friday", "focus": "Overall progress review"}
            ]
        }

        return json.dumps({"status": "success", "coaching_plan": plan}, indent=2)

    def _provide_deal_strategy(self, deal_id: str, params: Dict) -> str:
        """Provide strategic recommendations for specific deal."""

        strategy = {
            "deal_id": deal_id or "DEAL-001",
            "deal_name": "TechCorp Platform Expansion",
            "deal_value": "$850K",
            "current_stage": "Proposal",
            "days_in_stage": 21,
            "deal_health": "At Risk",
            "analysis": {
                "strengths": [
                    "Strong champion (VP Operations)",
                    "Clear pain point identified ($400K annual waste)",
                    "Technical fit confirmed"
                ],
                "risks": [
                    "Economic buyer (CFO) not engaged",
                    "Competitor actively evaluating",
                    "No clear timeline established"
                ],
                "gaps": [
                    "Missing IT stakeholder buy-in",
                    "ROI not quantified for CFO",
                    "No urgency driver identified"
                ]
            },
            "recommended_strategy": {
                "primary_approach": "Multi-threaded engagement with CFO focus",
                "rationale": "CFO engagement is blocking progression; need ROI story",
                "key_actions": [
                    {
                        "action": "Request CFO meeting via champion",
                        "script": "Jennifer, you mentioned the CFO needs to approve this. Would you be willing to introduce me so I can address any financial questions directly?",
                        "timing": "This week",
                        "success_metric": "CFO meeting scheduled"
                    },
                    {
                        "action": "Prepare CFO-specific ROI presentation",
                        "content": "3-year TCO, payback period, risk mitigation value",
                        "timing": "Before CFO meeting",
                        "success_metric": "CFO acknowledges financial value"
                    },
                    {
                        "action": "Create urgency with limited-time offer",
                        "script": "We have a Q1 implementation slot available, but it closes January 31st. This would align with your fiscal year planning.",
                        "timing": "During proposal review",
                        "success_metric": "Timeline commitment secured"
                    }
                ]
            },
            "competitive_positioning": {
                "competitor": "Competitor A",
                "differentiators": [
                    "Native AI vs bolt-on (3x faster insights)",
                    "40% lower TCO over 3 years",
                    "Enterprise references in their industry"
                ],
                "objection_handlers": {
                    "price": "Our TCO analysis shows 40% savings over 3 years when you factor in implementation and maintenance",
                    "unknown vendor": "Let me connect you with our customer at Similar Company who faced the same concerns"
                }
            },
            "closing_tactics": [
                {
                    "tactic": "Summary Close",
                    "script": "Based on our discussions, we've identified $400K in annual savings, the team is aligned on requirements, and we have an implementation slot for Q1. What would it take to move forward this month?"
                },
                {
                    "tactic": "Alternative Close",
                    "script": "Would you prefer to start with the full platform or begin with a pilot in the operations team?"
                }
            ],
            "next_call_prep": {
                "objectives": ["Secure CFO meeting", "Confirm Q1 timeline interest", "Address competitive concerns"],
                "questions_to_ask": [
                    "What's the approval process once you have CFO alignment?",
                    "How does our timeline fit with your Q1 planning?",
                    "What would make this a clear win for you personally?"
                ],
                "listen_for": ["Budget approval process", "Internal champions", "Competitive mentions"]
            }
        }

        return json.dumps({"status": "success", "deal_strategy": strategy}, indent=2)

    def _track_progress(self, rep_id: str, params: Dict) -> str:
        """Track coaching progress over time."""

        progress = {
            "rep_id": rep_id or "REP-001",
            "rep_name": "Demo Rep 2",
            "tracking_period": "30-day coaching plan",
            "current_week": 2,
            "overall_progress": "65%",
            "skill_progression": {
                "closing": {
                    "start_score": 54,
                    "current_score": 62,
                    "target_score": 70,
                    "progress": "+8 points",
                    "on_track": True
                },
                "objection_handling": {
                    "start_score": 68,
                    "current_score": 71,
                    "target_score": 75,
                    "progress": "+3 points",
                    "on_track": True
                }
            },
            "activity_completion": {
                "learning_modules": {"completed": 4, "total": 6, "percentage": "67%"},
                "practice_exercises": {"completed": 3, "total": 5, "percentage": "60%"},
                "coaching_sessions": {"completed": 2, "total": 4, "percentage": "50%"},
                "live_application": {"completed": 5, "total": 8, "percentage": "63%"}
            },
            "behavioral_changes": [
                {"behavior": "Trial closes per call", "before": 1.2, "now": 2.1, "target": 3.0},
                {"behavior": "Urgency statements used", "before": 0.5, "now": 1.3, "target": 2.0},
                {"behavior": "Commitment requests", "before": 0.8, "now": 1.5, "target": 2.0}
            ],
            "outcome_metrics": {
                "win_rate": {"before": "18%", "current": "22%", "target": "24%"},
                "deals_advanced": {"this_period": 3, "same_period_last": 2},
                "avg_deal_cycle": {"before": "85 days", "current": "78 days"}
            },
            "manager_feedback": [
                {"date": "Week 1", "feedback": "Strong engagement with learning materials. Apply more in live calls."},
                {"date": "Week 2", "feedback": "Good improvement on trial closes. Focus on urgency next."}
            ],
            "next_milestones": [
                {"milestone": "Complete urgency creation module", "due": "End of week 2"},
                {"milestone": "Apply urgency in 3 live calls", "due": "Week 3"},
                {"milestone": "Achieve closing score of 70", "due": "Week 4"}
            ]
        }

        return json.dumps({"status": "success", "progress": progress}, indent=2)

    def _compare_to_benchmark(self, rep_id: str, params: Dict) -> str:
        """Compare rep performance to team benchmarks and top performers."""

        comparison = {
            "rep_id": rep_id or "REP-001",
            "rep_name": "Demo Rep 2",
            "comparison_date": datetime.now().isoformat(),
            "overall_ranking": "8 of 24 reps",
            "percentile": "Top 33%",
            "skill_comparison": {
                "discovery": {"rep": 82, "team_avg": 75, "top_performer": 92, "gap_to_top": 10},
                "qualification": {"rep": 75, "team_avg": 76, "top_performer": 88, "gap_to_top": 13},
                "presentation": {"rep": 78, "team_avg": 72, "top_performer": 90, "gap_to_top": 12},
                "objection_handling": {"rep": 68, "team_avg": 74, "top_performer": 89, "gap_to_top": 21},
                "closing": {"rep": 54, "team_avg": 72, "top_performer": 91, "gap_to_top": 37}
            },
            "metric_comparison": {
                "win_rate": {"rep": "18%", "team_avg": "24%", "top_performer": "38%"},
                "avg_deal_size": {"rep": "$320K", "team_avg": "$285K", "top_performer": "$420K"},
                "sales_cycle": {"rep": "85 days", "team_avg": "72 days", "top_performer": "58 days"},
                "pipeline_coverage": {"rep": "2.8x", "team_avg": "3.2x", "top_performer": "4.1x"}
            },
            "top_performer_behaviors": [
                {
                    "behavior": "Trial closes",
                    "top_performer_avg": 4.2,
                    "rep_avg": 1.2,
                    "gap": "3x fewer",
                    "recommendation": "Practice trial closes in every call"
                },
                {
                    "behavior": "Customer references cited",
                    "top_performer_avg": 2.8,
                    "rep_avg": 0.6,
                    "gap": "4.7x fewer",
                    "recommendation": "Build reference library by industry"
                },
                {
                    "behavior": "Multi-threading",
                    "top_performer_avg": "4.2 stakeholders",
                    "rep_avg": "2.1 stakeholders",
                    "gap": "2x fewer",
                    "recommendation": "Always ask for additional stakeholders"
                }
            ],
            "quick_win_opportunities": [
                "Increasing trial closes would have highest immediate impact",
                "Citing customer references builds credibility quickly",
                "Multi-threading reduces deal risk and increases win rate"
            ]
        }

        return json.dumps({"status": "success", "benchmark_comparison": comparison}, indent=2)

    def _simulate_objection(self, params: Dict) -> str:
        """Simulate objection handling practice scenario."""

        simulation = {
            "simulation_id": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "scenario": {
                "objection_type": "Price",
                "customer_persona": "CFO at mid-market company",
                "context": "Final stages of deal, competitor has come in 20% lower",
                "customer_statement": "Your solution looks good, but your competitor is offering us 20% less. Can you match their price?"
            },
            "framework_reminder": {
                "method": "LAER (Listen, Acknowledge, Explore, Respond)",
                "steps": [
                    "Listen - Let them fully express the concern",
                    "Acknowledge - Show you understand their position",
                    "Explore - Ask questions to understand the full picture",
                    "Respond - Address with value, not just discount"
                ]
            },
            "sample_responses": {
                "weak_response": "Let me see what discount I can get approved.",
                "why_weak": "Immediately concedes without understanding needs or demonstrating value",
                "strong_response": "I appreciate you sharing that. Price is certainly important. Before we discuss numbers, help me understand - when you compare us side by side, what are the key differences you see beyond price?",
                "why_strong": "Acknowledges concern, pivots to value conversation, uncovers what competitor is missing"
            },
            "follow_up_questions": [
                "What would switching to the lower-priced solution cost you in terms of the features you mentioned you need?",
                "When you factor in implementation time and ongoing support, how does the total cost compare?",
                "What's the cost of not solving this problem for another 6 months if implementation takes longer?"
            ],
            "value_statements": [
                "Our customers typically see ROI in 6 months vs 18 months with alternatives",
                "The implementation support alone is worth $50K based on your team's hourly rates",
                "We're the only solution with native AI, which your team said was critical"
            ],
            "practice_prompt": "Try responding to this objection out loud. Focus on acknowledging, exploring, and pivoting to value.",
            "evaluation_criteria": [
                "Did you acknowledge the concern without being defensive?",
                "Did you ask questions to understand the full picture?",
                "Did you pivot to value rather than immediately discounting?",
                "Did you quantify value in terms meaningful to the CFO?"
            ]
        }

        return json.dumps({"status": "success", "simulation": simulation}, indent=2)
