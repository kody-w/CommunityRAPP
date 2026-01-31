from agents.basic_agent import BasicAgent
import json
from datetime import datetime, timedelta
import random

class CxSalesPipelineAgent(BasicAgent):
    """
    Sales Pipeline Agent - Works with BOTH Salesforce and Dynamics 365
    Demonstrates immediate value during migration period.

    KEY VALUE PROP: Sales teams get AI-powered insights DAY 1,
    regardless of which CRM their data currently lives in.
    """

    def __init__(self):
        self.name = 'SalesPipeline'
        self.metadata = {
            "name": self.name,
            "description": "Get real-time sales pipeline insights, opportunity analysis, and forecasting. Works seamlessly whether your data is in Salesforce, Dynamics 365, or both during migration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["pipeline_summary", "at_risk_deals", "forecast", "top_opportunities", "team_performance"],
                        "description": "Type of pipeline insight needed"
                    },
                    "region": {
                        "type": "string",
                        "description": "Optional: Filter by region (e.g., 'EMEA', 'North America', 'APAC')"
                    },
                    "time_period": {
                        "type": "string",
                        "description": "Optional: Time period (e.g., 'Q1', 'this_month', 'this_quarter')"
                    }
                },
                "required": ["query_type"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        query_type = kwargs.get('query_type', 'pipeline_summary')
        region = kwargs.get('region', 'All Regions')
        time_period = kwargs.get('time_period', 'This Quarter')

        # Simulate unified data from both SF and D365
        if query_type == "pipeline_summary":
            return self._get_pipeline_summary(region, time_period)
        elif query_type == "at_risk_deals":
            return self._get_at_risk_deals(region)
        elif query_type == "forecast":
            return self._get_forecast(region, time_period)
        elif query_type == "top_opportunities":
            return self._get_top_opportunities(region)
        elif query_type == "team_performance":
            return self._get_team_performance(region)
        else:
            return self._get_pipeline_summary(region, time_period)

    def _get_pipeline_summary(self, region, time_period):
        return json.dumps({
            "status": "success",
            "data_sources": ["Salesforce (35,000 users)", "Dynamics 365 (10,000 migrated)"],
            "unified_view": True,
            "pipeline_summary": {
                "region": region,
                "period": time_period,
                "total_pipeline_value": "$847.3M",
                "qualified_opportunities": 1247,
                "stage_breakdown": {
                    "Discovery": {"count": 423, "value": "$156.2M"},
                    "Qualification": {"count": 312, "value": "$198.7M"},
                    "Proposal": {"count": 287, "value": "$243.1M"},
                    "Negotiation": {"count": 156, "value": "$187.4M"},
                    "Closing": {"count": 69, "value": "$61.9M"}
                },
                "vs_last_quarter": "+12.3%",
                "win_rate_trend": "67% (up from 61%)",
                "avg_deal_size": "$679K"
            },
            "ai_insight": "Pipeline velocity has increased 23% since unified reporting went live. Teams using the AI assistant close deals 8 days faster on average.",
            "migration_note": "Seamlessly aggregating data from both Salesforce and Dynamics 365 - no disruption to your sales motion."
        }, indent=2)

    def _get_at_risk_deals(self, region):
        return json.dumps({
            "status": "success",
            "at_risk_opportunities": [
                {
                    "account": "Global Manufacturing Corp",
                    "value": "$4.2M",
                    "stage": "Negotiation",
                    "days_stalled": 18,
                    "risk_factors": ["No executive engagement", "Competitor identified", "Budget review pending"],
                    "recommended_actions": [
                        "Schedule executive briefing with their CFO",
                        "Prepare competitive differentiation deck",
                        "Offer pilot program to reduce perceived risk"
                    ],
                    "source_system": "Salesforce"
                },
                {
                    "account": "TechStart Industries",
                    "value": "$2.8M",
                    "stage": "Proposal",
                    "days_stalled": 12,
                    "risk_factors": ["Champion went silent", "Q1 budget constraints mentioned"],
                    "recommended_actions": [
                        "Multi-thread: engage procurement and IT leads",
                        "Propose Q2 start with Q1 pilot",
                        "Share ROI case study from similar customer"
                    ],
                    "source_system": "Dynamics 365"
                },
                {
                    "account": "Energy Solutions Ltd",
                    "value": "$3.1M",
                    "stage": "Qualification",
                    "days_stalled": 21,
                    "risk_factors": ["Competing priority projects", "Key stakeholder on leave"],
                    "recommended_actions": [
                        "Wait for stakeholder return (Jan 15)",
                        "Send value summary to backup contact",
                        "Prepare business case for their board meeting"
                    ],
                    "source_system": "Salesforce"
                }
            ],
            "total_at_risk_value": "$10.1M",
            "ai_insight": "These 3 deals represent 34% of your Q1 commit. Prioritize Global Manufacturing Corp - highest value with clear action path."
        }, indent=2)

    def _get_forecast(self, region, time_period):
        return json.dumps({
            "status": "success",
            "forecast": {
                "period": time_period,
                "region": region,
                "committed": "$234.5M",
                "best_case": "$312.7M",
                "pipeline": "$847.3M",
                "target": "$280.0M",
                "attainment_prediction": "94% confidence of hitting target",
                "upside_opportunities": [
                    {"account": "Nordic Energy", "value": "$8.2M", "close_probability": "72%"},
                    {"account": "Swiss Pharma AG", "value": "$5.6M", "close_probability": "68%"},
                    {"account": "AutoTech GmbH", "value": "$4.1M", "close_probability": "81%"}
                ]
            },
            "ai_insight": "Based on historical patterns, pushing Nordic Energy and AutoTech this week could move you from 94% to 103% of target.",
            "data_freshness": "Real-time sync from Salesforce + Dynamics 365"
        }, indent=2)

    def _get_top_opportunities(self, region):
        return json.dumps({
            "status": "success",
            "top_opportunities": [
                {"rank": 1, "account": "Schneider Electric Internal", "value": "$12.4M", "stage": "Proposal", "health": "Strong", "source": "D365"},
                {"rank": 2, "account": "Global Logistics Partners", "value": "$8.7M", "stage": "Negotiation", "health": "Strong", "source": "Salesforce"},
                {"rank": 3, "account": "Nordic Energy Consortium", "value": "$8.2M", "stage": "Qualification", "health": "Medium", "source": "Salesforce"},
                {"rank": 4, "account": "Asia Pacific Manufacturing", "value": "$6.9M", "stage": "Discovery", "health": "Strong", "source": "D365"},
                {"rank": 5, "account": "European Retail Group", "value": "$5.8M", "stage": "Proposal", "health": "Medium", "source": "Salesforce"}
            ],
            "ai_insight": "Your top 5 deals total $42M. Focus on Nordic Energy - it's the largest deal still in early stages with room to influence scope."
        }, indent=2)

    def _get_team_performance(self, region):
        return json.dumps({
            "status": "success",
            "team_performance": {
                "region": region,
                "period": "Q4 2024",
                "total_reps": 847,
                "quota_attainment": {
                    "above_100": 312,
                    "80_to_100": 298,
                    "below_80": 237
                },
                "top_performers": [
                    {"name": "Demo Rep 2", "region": "APAC", "attainment": "142%", "closed": "$4.2M"},
                    {"name": "Marcus Weber", "region": "EMEA", "attainment": "138%", "closed": "$3.8M"},
                    {"name": "Demo Customer 1", "region": "NA", "attainment": "127%", "closed": "$3.5M"}
                ],
                "coaching_opportunities": [
                    {"pattern": "23 reps struggling with discovery-to-qualification conversion", "recommendation": "Deploy discovery call framework training"},
                    {"pattern": "18 reps have strong pipeline but low close rate", "recommendation": "Negotiation skills workshop"}
                ]
            },
            "ai_insight": "Top performers use the AI assistant 3.2x more frequently than average. Consider mandating AI briefings before key meetings."
        }, indent=2)
