from agents.basic_agent import BasicAgent
import json

class CxAccountIntelAgent(BasicAgent):
    """
    Account Intelligence Agent - Deep account insights in seconds

    KEY VALUE PROP: Sales reps get comprehensive account briefs before
    every meeting - no more scrambling through multiple systems.
    Works with data from Salesforce, D365, AND external sources.
    """

    def __init__(self):
        self.name = 'AccountIntel'
        self.metadata = {
            "name": self.name,
            "description": "Get comprehensive account intelligence including company overview, relationship history, opportunities, risks, news, and AI-generated meeting preparation briefs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Name of the account to research"
                    },
                    "intel_type": {
                        "type": "string",
                        "enum": ["full_brief", "meeting_prep", "relationship_map", "news_alerts", "competitive_intel", "expansion_opportunities"],
                        "description": "Type of intelligence needed"
                    }
                },
                "required": ["account_name"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        account_name = kwargs.get('account_name', 'Global Manufacturing Corp')
        intel_type = kwargs.get('intel_type', 'full_brief')

        intel_functions = {
            "full_brief": self._full_brief,
            "meeting_prep": self._meeting_prep,
            "relationship_map": self._relationship_map,
            "news_alerts": self._news_alerts,
            "competitive_intel": self._competitive_intel,
            "expansion_opportunities": self._expansion_opportunities
        }

        return intel_functions.get(intel_type, self._full_brief)(account_name)

    def _full_brief(self, account_name):
        return json.dumps({
            "status": "success",
            "account_brief": {
                "company": account_name,
                "overview": {
                    "industry": "Industrial Manufacturing",
                    "revenue": "$4.2B (2024)",
                    "employees": "12,500",
                    "headquarters": "Munich, Germany",
                    "fiscal_year_end": "December",
                    "stock": "Private Equity Owned (Carlyle Group)"
                },
                "relationship_summary": {
                    "customer_since": "2019",
                    "lifetime_value": "$8.7M",
                    "current_arr": "$1.2M",
                    "health_score": "72/100 (Medium)",
                    "nps_score": "+34",
                    "primary_products": ["EcoStruxure Plant", "PowerLogic", "Modicon PLCs"],
                    "contract_renewal": "March 2025"
                },
                "key_contacts": [
                    {"name": "Heinrich Mueller", "title": "CTO", "relationship": "Executive Sponsor", "sentiment": "Positive"},
                    {"name": "Anna Schmidt", "title": "VP Operations", "relationship": "Champion", "sentiment": "Very Positive"},
                    {"name": "Thomas Weber", "title": "Procurement Director", "relationship": "Economic Buyer", "sentiment": "Neutral"}
                ],
                "active_opportunities": [
                    {"name": "Plant Modernization Phase 2", "value": "$2.4M", "stage": "Proposal", "close_date": "Q1 2025"},
                    {"name": "Energy Management Expansion", "value": "$890K", "stage": "Discovery", "close_date": "Q2 2025"}
                ],
                "open_support_cases": 2,
                "data_sources": ["Salesforce CRM", "Dynamics 365", "ZoomInfo", "News APIs"]
            },
            "ai_insight": "Contract renewal in 3 months - this is your expansion window. Anna Schmidt is your champion; leverage her for executive access to close Plant Modernization."
        }, indent=2)

    def _meeting_prep(self, account_name):
        return json.dumps({
            "status": "success",
            "meeting_preparation_brief": {
                "account": account_name,
                "generated_for": "Upcoming meeting",
                "executive_summary": f"{account_name} is a strategic account with $1.2M ARR and strong growth potential. Key focus should be on the $2.4M Plant Modernization opportunity and upcoming contract renewal in March 2025.",
                "conversation_starters": [
                    "Congratulations on the Automotive Excellence Award last month - how is the expansion into EV components going?",
                    "I saw Thomas Weber posted about Industry 4.0 challenges - we have some interesting solutions there",
                    "Your Q3 earnings mentioned capacity expansion - perfect timing for our discussion"
                ],
                "key_talking_points": [
                    {
                        "topic": "Plant Modernization ROI",
                        "context": "They're evaluating Phase 2 investment",
                        "our_position": "Phase 1 delivered 23% efficiency gain - document and quantify",
                        "proof_points": ["Case study: Similar plant saw 18-month payback", "Their Phase 1 data shows $1.2M annual savings"]
                    },
                    {
                        "topic": "Contract Renewal",
                        "context": "Current contract expires March 2025",
                        "our_position": "Propose 3-year renewal with expanded scope",
                        "proof_points": ["Lock in current pricing before Q2 increase", "Bundle Energy Management for 15% discount"]
                    }
                ],
                "landmines_to_avoid": [
                    "Don't mention competitor Siemens - they lost a deal to them last year and it's sensitive",
                    "Procurement (Thomas) had issues with our invoicing last quarter - acknowledge if raised",
                    "Avoid discussing their Shanghai plant - regulatory issues ongoing"
                ],
                "relationship_history": {
                    "last_meeting": "Oct 15, 2024 - Quarterly Business Review",
                    "last_meeting_outcome": "Positive - agreed to evaluate Phase 2",
                    "open_action_items": ["Send ROI calculator", "Schedule plant visit"],
                    "pending_asks_from_them": ["Case studies from automotive sector", "Integration timeline for SAP"]
                },
                "competitive_threats": {
                    "active_competitors": ["Siemens (incumbent in some plants)", "ABB (evaluating)"],
                    "our_differentiators": ["Unified platform vs. point solutions", "Local support team in Munich", "Existing integration investment"]
                }
            },
            "ai_recommendation": "Lead with Phase 1 success metrics and Anna's endorsement. Position Phase 2 + renewal as a package deal. Have SAP integration timeline ready - Thomas mentioned this twice in recent emails."
        }, indent=2)

    def _relationship_map(self, account_name):
        return json.dumps({
            "status": "success",
            "relationship_map": {
                "account": account_name,
                "decision_making_unit": {
                    "economic_buyer": {
                        "name": "Thomas Weber",
                        "title": "Procurement Director",
                        "influence": "High - Controls budget approval",
                        "sentiment": "Neutral",
                        "engagement_level": "Low",
                        "action_needed": "Need more direct engagement - schedule 1:1"
                    },
                    "technical_buyer": {
                        "name": "Heinrich Mueller",
                        "title": "CTO",
                        "influence": "Very High - Final technical approval",
                        "sentiment": "Positive",
                        "engagement_level": "Medium",
                        "action_needed": "Invite to Innovation Summit in February"
                    },
                    "champion": {
                        "name": "Anna Schmidt",
                        "title": "VP Operations",
                        "influence": "High - Day-to-day decision maker",
                        "sentiment": "Very Positive",
                        "engagement_level": "High",
                        "action_needed": "Ask her to sponsor exec briefing"
                    },
                    "end_users": {
                        "count": 45,
                        "departments": ["Operations", "Maintenance", "Energy Management"],
                        "satisfaction": "4.2/5.0",
                        "training_status": "Complete"
                    }
                },
                "relationship_gaps": [
                    "No relationship with CFO (Klaus Fischer) - needed for large deals",
                    "IT Director (Maria Hoffmann) is new - not yet engaged",
                    "Board level relationships missing"
                ],
                "internal_schneider_team": [
                    {"name": "Marc Dubois", "role": "Account Executive", "tenure": "3 years with account"},
                    {"name": "Lisa Park", "role": "Solution Architect", "specialty": "Industrial Automation"},
                    {"name": "Robert Chen", "role": "Customer Success Manager", "focus": "Adoption & Value"}
                ]
            },
            "ai_recommendation": "Multi-thread urgently. Economic buyer Thomas is at risk - low engagement despite high influence. Ask Anna to facilitate introduction to CFO for the $2.4M deal."
        }, indent=2)

    def _news_alerts(self, account_name):
        return json.dumps({
            "status": "success",
            "news_and_signals": {
                "account": account_name,
                "alerts_last_30_days": [
                    {
                        "date": "2024-12-10",
                        "headline": f"{account_name} Announces €500M Investment in Smart Factory Initiative",
                        "source": "Reuters",
                        "relevance": "HIGH",
                        "opportunity": "Major expansion budget - align our proposals to this initiative",
                        "suggested_action": "Reference this in next meeting, position as enabling partner"
                    },
                    {
                        "date": "2024-12-05",
                        "headline": "New Chief Digital Officer Appointed",
                        "source": "Company Press Release",
                        "relevance": "HIGH",
                        "opportunity": "New executive to build relationship with",
                        "suggested_action": "Research CDO background, request introduction via Heinrich"
                    },
                    {
                        "date": "2024-11-28",
                        "headline": f"{account_name} Wins Automotive Industry Excellence Award",
                        "source": "Industry Week",
                        "relevance": "MEDIUM",
                        "opportunity": "Conversation starter, relationship building",
                        "suggested_action": "Send congratulations note to Anna"
                    },
                    {
                        "date": "2024-11-15",
                        "headline": "Q3 Earnings Beat Expectations, Announces Capacity Expansion",
                        "source": "Financial Times",
                        "relevance": "HIGH",
                        "opportunity": "Budget availability confirmed, expansion = our solutions",
                        "suggested_action": "Update opportunity values, accelerate proposals"
                    }
                ],
                "social_signals": [
                    {"person": "Heinrich Mueller", "platform": "LinkedIn", "activity": "Shared article on Industrial IoT trends"},
                    {"person": "Thomas Weber", "platform": "LinkedIn", "activity": "Posted about supply chain digitization challenges"}
                ],
                "hiring_signals": [
                    "3 open roles for Automation Engineers - expansion indicator",
                    "Hiring Energy Manager - aligns with our Energy Management opportunity"
                ]
            },
            "ai_summary": "Strong buying signals: €500M smart factory investment + Q3 expansion announcement + active hiring. New CDO is a wildcard - prioritize relationship building. This account is primed for a larger strategic conversation."
        }, indent=2)

    def _competitive_intel(self, account_name):
        return json.dumps({
            "status": "success",
            "competitive_intelligence": {
                "account": account_name,
                "competitive_landscape": {
                    "schneider_position": "Primary vendor for automation, secondary for energy",
                    "wallet_share": "35%",
                    "competitor_presence": [
                        {
                            "competitor": "Siemens",
                            "products": ["SIMATIC PLCs", "MindSphere"],
                            "footprint": "3 plants in Eastern Europe",
                            "relationship_strength": "Medium",
                            "threat_level": "Medium",
                            "vulnerabilities": ["Higher cost", "Complex integration", "Support response times"]
                        },
                        {
                            "competitor": "ABB",
                            "products": "Currently evaluating for motor control",
                            "footprint": "None currently",
                            "relationship_strength": "Low",
                            "threat_level": "Low",
                            "vulnerabilities": ["No existing relationship", "Would require new integration"]
                        },
                        {
                            "competitor": "Rockwell",
                            "products": ["FactoryTalk"],
                            "footprint": "US plant only",
                            "relationship_strength": "Low",
                            "threat_level": "Low",
                            "vulnerabilities": ["Limited European presence", "Not competitive on price in EU"]
                        }
                    ]
                },
                "recent_competitive_activity": [
                    "Siemens offered 20% discount on MindSphere renewal - customer shared with us",
                    "ABB conducted plant assessment in October - no proposal yet"
                ],
                "our_win_themes": [
                    "Unified platform across all plants (vs. competitor silos)",
                    "Local Munich support team - 4-hour response SLA",
                    "Existing integration investment would be lost switching",
                    "Proven Phase 1 ROI - they know our solution works"
                ],
                "competitive_battlecards": "Available in Sales Hub > Competitive > Global Manufacturing Corp"
            },
            "ai_recommendation": "Siemens discount offer is concerning - counter with multi-year value lock-in. Emphasize switching costs and Phase 1 success. ABB is exploratory; don't overreact but monitor closely."
        }, indent=2)

    def _expansion_opportunities(self, account_name):
        return json.dumps({
            "status": "success",
            "expansion_analysis": {
                "account": account_name,
                "current_products": [
                    {"product": "EcoStruxure Plant Advisor", "arr": "$480K", "users": 45, "health": "Green"},
                    {"product": "PowerLogic ION9000", "arr": "$320K", "units": 28, "health": "Green"},
                    {"product": "Modicon M580", "arr": "$400K", "units": 156, "health": "Yellow"}
                ],
                "whitespace_opportunities": [
                    {
                        "opportunity": "EcoStruxure Building Advisor",
                        "potential_arr": "$280K",
                        "rationale": "4 office/admin buildings not yet on our platform",
                        "champion": "Facilities Director (not yet engaged)",
                        "next_step": "Request intro from Anna Schmidt",
                        "probability": "60%"
                    },
                    {
                        "opportunity": "Cybersecurity Services",
                        "potential_arr": "$150K",
                        "rationale": "New EU NIS2 directive requires OT security",
                        "champion": "CISO (new relationship needed)",
                        "next_step": "Security assessment offer",
                        "probability": "70%"
                    },
                    {
                        "opportunity": "Predictive Maintenance",
                        "potential_arr": "$340K",
                        "rationale": "Current reactive maintenance costs €2M/year",
                        "champion": "Anna Schmidt (very interested)",
                        "next_step": "ROI workshop scheduled Jan 20",
                        "probability": "75%"
                    },
                    {
                        "opportunity": "Energy-as-a-Service",
                        "potential_arr": "$520K",
                        "rationale": "Sustainability targets require energy optimization",
                        "champion": "New Sustainability Officer",
                        "next_step": "Energy audit proposal",
                        "probability": "50%"
                    }
                ],
                "total_expansion_potential": "$1.29M additional ARR",
                "recommended_priority": [
                    "1. Predictive Maintenance - highest probability, strong champion",
                    "2. Cybersecurity - regulatory driver creates urgency",
                    "3. Energy-as-a-Service - largest value, needs exec sponsorship"
                ]
            },
            "ai_insight": "You can nearly double this account's ARR from $1.2M to $2.5M. Predictive Maintenance is the path of least resistance - Anna is already bought in. Use that win to open doors for Energy and Buildings."
        }, indent=2)
