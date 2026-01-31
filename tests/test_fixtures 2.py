"""
RAPP Pipeline Test Fixtures
Realistic synthetic data for automated testing

Scenarios:
1. Capital Markets - Trade Reconciliation Agent
2. Call Center - D365 Customer Service Agent
"""

# =============================================================================
# SCENARIO 1: CAPITAL MARKETS - TRADE RECONCILIATION AGENT
# =============================================================================

CAPITAL_MARKETS_CUSTOMER = {
    "customer_name": "Meridian Capital Partners",
    "industry": "Capital Markets / Investment Banking",
    "company_size": "enterprise",
    "contacts": [
        {"name": "Sarah Chen", "role": "Managing Director, Operations", "email": "schen@meridiancap.com"},
        {"name": "Marcus Williams", "role": "VP Technology", "email": "mwilliams@meridiancap.com"},
        {"name": "Jennifer Park", "role": "Head of Trade Operations", "email": "jpark@meridiancap.com"}
    ]
}

CAPITAL_MARKETS_TRANSCRIPT = """
DISCOVERY CALL TRANSCRIPT
Date: January 15, 2026
Duration: 47 minutes
Participants:
- Sarah Chen (Managing Director, Operations) - Meridian Capital Partners
- Marcus Williams (VP Technology) - Meridian Capital Partners
- Jennifer Park (Head of Trade Operations) - Meridian Capital Partners
- Alex Thompson (Solution Architect) - Microsoft

---

ALEX: Thank you all for joining today. I'm excited to learn more about Meridian Capital and the challenges you're facing in your operations. Sarah, would you like to kick us off with some background?

SARAH: Absolutely. So Meridian Capital Partners is a mid-sized investment bank with about $45 billion in assets under management. We operate across equities, fixed income, and derivatives trading. Our operations team handles roughly 15,000 trades per day across all desks.

ALEX: That's significant volume. What brings us together today?

SARAH: Honestly, we're drowning in manual reconciliation work. Our trade breaks are killing us. Jennifer, can you walk through the current process?

JENNIFER: Sure. So every morning, my team of 12 analysts starts their day by pulling trade data from three different systems - our Order Management System which is Charles River, our clearing system at DTCC, and our prime broker reports from Goldman and Morgan Stanley. They manually compare these records to identify breaks.

ALEX: How long does that take?

JENNIFER: On a good day, four to five hours. On a bad day after high volume or a market event, we're talking eight hours or more. Last month during the Fed announcement, we had 847 breaks and my team worked until 11 PM three nights in a row.

MARCUS: The technical challenge is that each system has different trade identifiers, different timestamps, and different ways of representing the same security. A single trade might show up as AAPL in one system, Apple Inc. in another, and a CUSIP number in the third.

ALEX: What's the business impact of these breaks?

SARAH: It's significant. First, there's the direct cost - we're paying $180,000 annually just for the reconciliation team's time on this task. But the bigger issue is settlement risk. When we don't catch a break in time, we risk failing to deliver on T+1. Last quarter, we had $2.3 million in failed trades that resulted in $47,000 in penalties and damaged our relationship with two counterparties.

JENNIFER: And honestly, we're losing good people. Three analysts have quit in the past year citing burnout from the reconciliation grind. Each replacement costs us about $25,000 in recruiting and training.

ALEX: Tell me more about the data sources. Marcus, what systems are we working with?

MARCUS: Our primary systems are:
1. Charles River OMS - REST API available, we have full access
2. DTCC clearing reports - SFTP file drops every 30 minutes
3. Prime broker portal - Goldman has an API, Morgan Stanley is CSV downloads
4. Bloomberg Terminal - for security master data and pricing
5. Our internal data warehouse on SQL Server - where we store historical trades

The good news is we have a solid data team. The bad news is they're swamped with regulatory reporting.

ALEX: What would success look like for you?

SARAH: If we could cut that four-hour manual process down to 30 minutes of exception review, that would be transformational. My target is 90% auto-resolution of breaks.

JENNIFER: For me, I want my team to focus on the complex breaks that actually need human judgment - not matching obvious timestamp discrepancies or security identifier translations.

MARCUS: From a tech perspective, I need something that integrates with our existing infrastructure without requiring a six-month implementation. We're already mid-way through a core system upgrade.

ALEX: What about compliance and security requirements?

MARCUS: We're SEC and FINRA regulated. All data must stay within our Azure tenant. We cannot send trade data to any external APIs - that's non-negotiable. We need full audit trails of any automated actions.

SARAH: And we have quarterly audits. We need to be able to demonstrate to auditors exactly how breaks were resolved and why.

ALEX: Are there any other stakeholders we should involve?

SARAH: Our Chief Compliance Officer, David Morrison, will need to sign off on anything that touches trade data. And our CFO will want to see the ROI business case before we move forward.

ALEX: What's your timeline?

SARAH: We have a board meeting in Q2 where I'm presenting our operational efficiency initiatives. I'd love to have a working prototype by April and be in production by end of Q2.

JENNIFER: The sooner the better honestly. We have two analysts going on parental leave in February and I don't have budget to backfill.

ALEX: One last question - have you tried to solve this before?

MARCUS: We looked at a few vendors two years ago. One wanted $500K for implementation plus $200K annual licensing. Another couldn't handle our volume. We ended up building some Excel macros that help with the obvious matches but they break constantly and no one wants to maintain them.

SARAH: We also tried outsourcing to an offshore team, but the time zone difference meant breaks weren't resolved until our next trading day. That created more problems than it solved.

ALEX: This is really helpful context. Let me summarize what I'm hearing:
- 15,000 trades daily across multiple asset classes
- 4-5 hours of manual reconciliation work
- Multiple data sources with inconsistent identifiers
- Need for audit trails and regulatory compliance
- Target of 90% auto-resolution
- Timeline of Q2 for production deployment

Does that capture it?

SARAH: That's exactly right. When can we see something?

ALEX: I'll put together an MVP proposal and share it with you by end of week. We'll focus on the highest-impact scenario first and build from there.

---
END OF TRANSCRIPT
"""

CAPITAL_MARKETS_DISCOVERY_DATA = {
    "problemStatements": [
        {
            "problem": "Manual trade reconciliation takes 4-5 hours daily with team of 12 analysts",
            "verbatimQuote": "Every morning, my team of 12 analysts starts their day by pulling trade data from three different systems... On a good day, four to five hours.",
            "category": "EFFICIENCY",
            "severity": "HIGH",
            "currentProcess": "Manual comparison of OMS, clearing, and prime broker data",
            "businessImpact": "$180,000 annual labor cost, $47,000 quarterly penalties, 3 analyst resignations"
        },
        {
            "problem": "Trade breaks cause settlement failures and regulatory penalties",
            "verbatimQuote": "Last quarter, we had $2.3 million in failed trades that resulted in $47,000 in penalties",
            "category": "COST",
            "severity": "CRITICAL",
            "currentProcess": "Exception-based manual review after 4-5 hour reconciliation",
            "businessImpact": "$2.3M failed trades, damaged counterparty relationships"
        }
    ],
    "dataSources": [
        {"systemName": "Charles River OMS", "dataType": "API", "accessLevel": "Full", "dataVolume": "15,000 trades/day", "integrationComplexity": "LOW"},
        {"systemName": "DTCC Clearing", "dataType": "File", "accessLevel": "Full", "dataVolume": "SFTP every 30 min", "integrationComplexity": "LOW"},
        {"systemName": "Goldman Prime Broker", "dataType": "API", "accessLevel": "Full", "dataVolume": "Daily positions", "integrationComplexity": "MEDIUM"},
        {"systemName": "Morgan Stanley Prime", "dataType": "File", "accessLevel": "Partial", "dataVolume": "CSV daily", "integrationComplexity": "MEDIUM"},
        {"systemName": "Bloomberg Terminal", "dataType": "API", "accessLevel": "Full", "dataVolume": "Security master", "integrationComplexity": "LOW"},
        {"systemName": "SQL Server DW", "dataType": "Database", "accessLevel": "Full", "dataVolume": "Historical trades", "integrationComplexity": "LOW"}
    ],
    "stakeholders": [
        {"name": "Sarah Chen", "role": "Managing Director, Operations", "influenceLevel": "DECISION_MAKER", "concerns": ["ROI", "Q2 timeline"], "enthusiasm": "HIGH"},
        {"name": "Marcus Williams", "role": "VP Technology", "influenceLevel": "TECHNICAL", "concerns": ["Integration complexity", "Security"], "enthusiasm": "MEDIUM"},
        {"name": "Jennifer Park", "role": "Head of Trade Operations", "influenceLevel": "USER", "concerns": ["Team burnout", "Process efficiency"], "enthusiasm": "HIGH"},
        {"name": "David Morrison", "role": "Chief Compliance Officer", "influenceLevel": "INFLUENCER", "concerns": ["Audit trails", "Regulatory compliance"], "enthusiasm": "MEDIUM"}
    ],
    "successCriteria": [
        {"metric": "Reconciliation Time", "currentValue": "4-5 hours", "targetValue": "30 minutes", "measurementMethod": "Time tracking"},
        {"metric": "Auto-Resolution Rate", "currentValue": "0%", "targetValue": "90%", "measurementMethod": "Break count comparison"},
        {"metric": "Failed Trades", "currentValue": "$2.3M quarterly", "targetValue": "<$500K quarterly", "measurementMethod": "Settlement reports"},
        {"metric": "Penalties", "currentValue": "$47K quarterly", "targetValue": "$0", "measurementMethod": "Finance reports"}
    ],
    "timeline": {
        "urgency": "HIGH",
        "targetLaunchDate": "Q2 2026",
        "budgetCycle": "Q2 board meeting",
        "keyMilestones": ["Prototype by April", "Production by end of Q2"]
    },
    "suggestedAgents": ["TradeReconciliationAgent", "BreakResolutionAgent", "AuditTrailAgent"],
    "technicalConstraints": {
        "security": "All data must stay within Azure tenant - no external APIs",
        "compliance": "SEC/FINRA regulated, full audit trails required",
        "infrastructure": "Must integrate with existing systems, no 6-month implementation"
    }
}


# =============================================================================
# SCENARIO 2: CALL CENTER - DYNAMICS 365 CUSTOMER SERVICE AGENT
# =============================================================================

CALL_CENTER_CUSTOMER = {
    "customer_name": "Pacific Northwest Insurance Group",
    "industry": "Insurance / Financial Services",
    "company_size": "large",
    "contacts": [
        {"name": "Michael Torres", "role": "VP Customer Experience", "email": "mtorres@pnwinsurance.com"},
        {"name": "Amanda Richardson", "role": "Director of Contact Center Operations", "email": "arichardson@pnwinsurance.com"},
        {"name": "Kevin Patel", "role": "IT Manager - CRM Systems", "email": "kpatel@pnwinsurance.com"}
    ]
}

CALL_CENTER_TRANSCRIPT = """
DISCOVERY CALL TRANSCRIPT
Date: January 16, 2026
Duration: 52 minutes
Participants:
- Michael Torres (VP Customer Experience) - Pacific Northwest Insurance Group
- Amanda Richardson (Director of Contact Center Operations) - Pacific Northwest Insurance Group
- Kevin Patel (IT Manager - CRM Systems) - Pacific Northwest Insurance Group
- Rachel Kim (Solution Architect) - Microsoft

---

RACHEL: Good morning everyone. Thank you for making time today. I understand Pacific Northwest Insurance is looking to enhance your contact center operations. Michael, can you set the stage for us?

MICHAEL: Thanks Rachel. So Pacific Northwest Insurance Group serves about 1.2 million policyholders across auto, home, and life insurance. Our contact center handles roughly 8,000 calls per day, plus another 3,000 digital interactions through chat and email. We've been using Dynamics 365 Customer Service for about two years now.

RACHEL: Great, so you're already on the Microsoft stack. What's prompting this conversation?

MICHAEL: Our customer satisfaction scores have been declining. We were at 4.2 out of 5 two years ago, and we've dropped to 3.6. Our NPS went from +32 to +18. The board is asking hard questions.

AMANDA: The core issue is agent productivity and consistency. When a customer calls in, our agents are juggling between six or seven different screens to find information. Policy details are in D365, claims history is in our legacy Guidewire system, payment status is in our billing platform, and prior interaction notes are scattered across the case history.

RACHEL: Walk me through a typical call scenario.

AMANDA: Sure. Let's say Mrs. Johnson calls in because she received a premium increase notice and wants to understand why. Here's what our agent has to do:
1. Verify identity - pull up the customer record in D365
2. Find the policy - navigate to the policy entity
3. Check the premium history - that requires logging into our actuarial system
4. Look at claims history - switch to Guidewire
5. Check for any pending tickets - back to D365 cases
6. Review notes from the last interaction - scroll through activity history
7. Look up the specific rate change reason - open our underwriting documentation

RACHEL: How long does all that take?

AMANDA: Average handle time for a billing inquiry like that is 12 minutes. Industry benchmark is 6 minutes. We're literally twice as slow as we should be.

KEVIN: From a technical perspective, the challenge is that D365 Customer Service is only as good as the data flowing into it. We have integrations, but they're point-to-point and not real-time. So our agents see data that's sometimes 24 hours stale.

MICHAEL: The real kicker is that our agents know the answers to most questions. They're experienced. But they spend 60% of their time just finding information instead of actually helping the customer.

RACHEL: What's the business impact beyond CSAT scores?

MICHAEL: It's significant. Our average cost per call is $8.50. If we could cut handle time in half, that's over $2 million annually in direct savings. But the bigger issue is churn. We lose about 8% of our customers after a poor service interaction. Given average lifetime value of $4,200 per customer, each point of satisfaction we lose costs us real money.

AMANDA: And then there's the agent side. Annual turnover in our contact center is 45%. Exit interviews consistently cite frustration with the tools as a top reason. Training a new agent costs us $6,500 and takes 8 weeks before they're fully productive.

RACHEL: Kevin, tell me more about your technical environment.

KEVIN: We're running Dynamics 365 Customer Service Enterprise. We have about 350 agent seats. Our key integrations are:
- Guidewire PolicyCenter for policy administration and claims
- Oracle Financial Services for billing and payments
- Genesys Cloud for telephony and omnichannel routing
- SharePoint for document management
- A custom data warehouse on Azure SQL for analytics

We recently licensed Copilot Studio and have M365 Copilot rolling out to the broader organization. We'd love to leverage that investment.

RACHEL: Perfect. That's exactly where I was hoping we could focus. What would the ideal state look like?

AMANDA: In my dream world, when Mrs. Johnson calls in, my agent sees everything they need on one screen before they even say hello. Customer summary, recent interactions, open issues, and a suggested response based on why they're likely calling.

MICHAEL: And I want consistency. Right now, Agent A might offer a loyalty discount and Agent B doesn't know it exists. I want AI-assisted responses that ensure every customer gets the right answer the first time.

KEVIN: For me, I want something that works with our D365 investment, not around it. We spent two years getting people to adopt D365. I can't introduce another system.

RACHEL: What about compliance and security considerations?

KEVIN: We're in insurance, so we have state regulatory requirements. All customer interactions must be logged. We need to be able to demonstrate fair treatment and consistent responses. PII handling is critical - we have SSN, driver's license numbers, and health information for life insurance customers.

MICHAEL: And we have a legal hold requirement. We can't delete any customer interaction records for 7 years.

RACHEL: Who else would need to be involved in a decision?

MICHAEL: Our CISO, James McCarthy, would need to review anything touching customer data. And ultimately our COO, Patricia Huang, controls the budget. But she's already told me to find a solution, so budget isn't the blocker - proving the ROI is.

RACHEL: Timeline?

AMANDA: We're entering our busy season in April - that's tax season and a lot of billing inquiries. I'd love to have something in place before then. Even a pilot with a subset of agents would be valuable.

MICHAEL: But I want to be realistic. I've seen these projects drag on. If you tell me we can have something meaningful in 60 days, I'm interested. If it's a year-long initiative, I need to think differently.

RACHEL: Let me ask about previous attempts.

KEVIN: We tried building an internal "agent assistant" two years ago. It was basically a search tool over our knowledge base. Agents didn't use it because it was too slow and the results weren't contextual. We sunsetted it after 6 months.

AMANDA: We also piloted a chatbot from a vendor last year. It handled about 15% of inquiries but customers complained it felt robotic. We still have it but we're not expanding it.

RACHEL: Here's what I'm thinking. We could build a Copilot Studio agent that sits right inside the D365 interface your agents already use. When a call comes in, it automatically:
1. Pulls the unified customer context from all your systems
2. Summarizes recent interactions and open issues
3. Predicts the reason for the call based on recent activity
4. Suggests appropriate responses and next best actions
5. Auto-generates case notes after the call

All within the D365 experience, leveraging your existing integrations.

AMANDA: That would be game-changing. My agents wouldn't have to learn anything new.

KEVIN: And it uses our Copilot Studio license we're already paying for?

RACHEL: Exactly. Let me put together a proposal focused on the billing inquiry scenario first - since that's high volume and well-defined. We can expand from there.

MICHAEL: I like the phased approach. When can we see something?

RACHEL: I'll have an MVP proposal to you by Monday. We'll target having a working prototype you can demo in 30 days.

---
END OF TRANSCRIPT
"""

CALL_CENTER_DISCOVERY_DATA = {
    "problemStatements": [
        {
            "problem": "Agents juggling 6-7 systems results in 12-minute average handle time vs 6-minute benchmark",
            "verbatimQuote": "Our agents are juggling between six or seven different screens to find information... Average handle time for a billing inquiry is 12 minutes. Industry benchmark is 6 minutes.",
            "category": "EFFICIENCY",
            "severity": "HIGH",
            "currentProcess": "Manual navigation between D365, Guidewire, billing system, and others",
            "businessImpact": "$2M+ annual savings potential, 45% agent turnover"
        },
        {
            "problem": "Customer satisfaction declined from 4.2 to 3.6, NPS dropped from +32 to +18",
            "verbatimQuote": "Our customer satisfaction scores have been declining. We were at 4.2 out of 5 two years ago, and we've dropped to 3.6.",
            "category": "GROWTH",
            "severity": "CRITICAL",
            "currentProcess": "No proactive context or suggested responses for agents",
            "businessImpact": "8% customer churn after poor interactions, $4,200 LTV per customer"
        },
        {
            "problem": "Inconsistent agent responses due to lack of guided assistance",
            "verbatimQuote": "Agent A might offer a loyalty discount and Agent B doesn't know it exists.",
            "category": "ACCURACY",
            "severity": "MEDIUM",
            "currentProcess": "Agents rely on memory and tribal knowledge",
            "businessImpact": "Inconsistent customer experience, compliance risk"
        }
    ],
    "dataSources": [
        {"systemName": "Dynamics 365 Customer Service", "dataType": "API", "accessLevel": "Full", "dataVolume": "350 agents, 1.2M customers", "integrationComplexity": "LOW"},
        {"systemName": "Guidewire PolicyCenter", "dataType": "API", "accessLevel": "Full", "dataVolume": "Policy and claims data", "integrationComplexity": "MEDIUM"},
        {"systemName": "Oracle Financial Services", "dataType": "API", "accessLevel": "Full", "dataVolume": "Billing and payments", "integrationComplexity": "MEDIUM"},
        {"systemName": "Genesys Cloud", "dataType": "API", "accessLevel": "Full", "dataVolume": "8,000 calls + 3,000 digital/day", "integrationComplexity": "LOW"},
        {"systemName": "SharePoint", "dataType": "API", "accessLevel": "Full", "dataVolume": "Documents and knowledge base", "integrationComplexity": "LOW"},
        {"systemName": "Azure SQL Data Warehouse", "dataType": "Database", "accessLevel": "Full", "dataVolume": "Analytics data", "integrationComplexity": "LOW"}
    ],
    "stakeholders": [
        {"name": "Michael Torres", "role": "VP Customer Experience", "influenceLevel": "DECISION_MAKER", "concerns": ["CSAT improvement", "ROI proof"], "enthusiasm": "HIGH"},
        {"name": "Amanda Richardson", "role": "Director of Contact Center Operations", "influenceLevel": "USER", "concerns": ["Agent productivity", "March busy season"], "enthusiasm": "HIGH"},
        {"name": "Kevin Patel", "role": "IT Manager - CRM Systems", "influenceLevel": "TECHNICAL", "concerns": ["D365 integration", "Leverage existing licenses"], "enthusiasm": "HIGH"},
        {"name": "James McCarthy", "role": "CISO", "influenceLevel": "INFLUENCER", "concerns": ["PII handling", "Security review"], "enthusiasm": "MEDIUM"},
        {"name": "Patricia Huang", "role": "COO", "influenceLevel": "DECISION_MAKER", "concerns": ["Budget approval", "ROI"], "enthusiasm": "MEDIUM"}
    ],
    "successCriteria": [
        {"metric": "Average Handle Time", "currentValue": "12 minutes", "targetValue": "6 minutes", "measurementMethod": "Genesys reporting"},
        {"metric": "Customer Satisfaction", "currentValue": "3.6/5", "targetValue": "4.2/5", "measurementMethod": "Post-call surveys"},
        {"metric": "First Call Resolution", "currentValue": "Unknown", "targetValue": "85%", "measurementMethod": "Case tracking"},
        {"metric": "Agent Turnover", "currentValue": "45%", "targetValue": "<30%", "measurementMethod": "HR data"}
    ],
    "timeline": {
        "urgency": "HIGH",
        "targetLaunchDate": "Before April 2026 (busy season)",
        "budgetCycle": "Budget approved, need ROI proof",
        "keyMilestones": ["Working prototype in 30 days", "Pilot before April"]
    },
    "suggestedAgents": ["CustomerContextAgent", "CallSummaryAgent", "NextBestActionAgent", "CaseNotesAgent"],
    "technicalConstraints": {
        "platform": "Must integrate with Dynamics 365 Customer Service",
        "licensing": "Leverage existing Copilot Studio license",
        "compliance": "State insurance regulations, 7-year retention, PII handling",
        "deployment": "Surface through Copilot Studio in D365"
    }
}


# =============================================================================
# TEST PARAMETERS FOR AGENTS
# =============================================================================

TEST_USER_GUID = "test-user-1234-5678-abcd-ef0123456789"

CAPITAL_MARKETS_AGENT_CONFIG = {
    "agent_name": "TradeReconciliationAgent",
    "agent_type": "reconciliation",
    "features": {
        "p0": [
            "Multi-source trade data ingestion (OMS, clearing, prime broker)",
            "Intelligent trade matching with fuzzy identifier resolution",
            "Auto-resolution of common break types (timestamp, identifier, quantity)"
        ],
        "p1": [
            "Exception queue prioritization by settlement risk",
            "Audit trail generation for compliance",
            "Break pattern analysis and reporting"
        ],
        "p2": [
            "Predictive break detection before settlement",
            "Integration with counterparty communication",
            "Historical trend analysis dashboard"
        ]
    },
    "data_requirements": [
        {"source": "Charles River OMS", "method": "REST API", "frequency": "Real-time"},
        {"source": "DTCC Clearing", "method": "SFTP", "frequency": "Every 30 minutes"},
        {"source": "Prime Broker APIs", "method": "REST API", "frequency": "Daily batch + on-demand"}
    ]
}

CALL_CENTER_AGENT_CONFIG = {
    "agent_name": "CustomerServiceCopilot",
    "agent_type": "copilot_studio",
    "features": {
        "p0": [
            "Unified customer context panel in D365",
            "Auto-population of customer summary on call connect",
            "Suggested responses based on call reason prediction"
        ],
        "p1": [
            "Auto-generated case notes post-call",
            "Next best action recommendations",
            "Knowledge base search with contextual results"
        ],
        "p2": [
            "Sentiment analysis during calls",
            "Proactive retention offer suggestions",
            "Cross-sell/up-sell opportunity detection"
        ]
    },
    "data_requirements": [
        {"source": "Dynamics 365", "method": "Dataverse API", "frequency": "Real-time"},
        {"source": "Guidewire", "method": "REST API", "frequency": "On-demand"},
        {"source": "Oracle Billing", "method": "REST API", "frequency": "On-demand"}
    ]
}


# =============================================================================
# EXPECTED OUTPUTS FOR VALIDATION
# =============================================================================

CAPITAL_MARKETS_EXPECTED_QG1 = {
    "decision_should_be": "PASS",
    "minimum_score": 7.5,
    "required_validations": [
        "Problem statement is quantified ($180K labor, $47K penalties)",
        "Data sources are identified with access levels",
        "Success metrics have baseline and target values",
        "Timeline is specified (Q2 2026)"
    ]
}

CALL_CENTER_EXPECTED_QG1 = {
    "decision_should_be": "PASS",
    "minimum_score": 7.5,
    "required_validations": [
        "Problem statement includes CSAT decline metrics",
        "D365 integration requirement is clear",
        "Multiple stakeholders identified with decision maker",
        "Copilot Studio deployment path specified"
    ]
}
