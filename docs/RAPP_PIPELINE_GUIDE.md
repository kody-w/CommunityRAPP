# RAPP Pipeline Complete Guide

## Overview

The **RAPP (Rapid AI Agent Production Pipeline)** is a 14-step methodology for building production-ready AI agents. It enforces quality gates, prevents scope creep, and ensures successful delivery.

## Quick Start

### Option 1: Use Claude Code Agent

```bash
# In Claude Code, use the RAPP agent
/rapp
```

### Option 2: Use the API Directly

```bash
# Set your function URL and key
export FUNCTION_URL="https://YOUR-FUNCTION.azurewebsites.net/api/businessinsightbot_function"
export FUNCTION_KEY="YOUR_KEY"

# Start by creating a project
curl -X POST "${FUNCTION_URL}?code=${FUNCTION_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Use ProjectTracker with action=create, customer_name=Acme Corp, project_name=Inventory Optimizer",
    "conversation_history": []
  }'
```

### Option 3: Run the Test Script

```bash
source .venv/bin/activate
python test_rapp_pipeline_aibast.py
```

---

## The 14 Steps

### Phase 1: Discovery (Steps 1-2)

#### Step 1: Discovery Call
**Purpose**: Capture the customer's business problem.

**Key Questions to Ask**:
1. What's your biggest operational pain point?
2. How much is this problem costing you (time/money)?
3. What systems do you use today?
4. Who needs to be involved in decisions?
5. What does success look like?
6. When do you need this solved?

**Agent**: `RAPPDiscovery`
```
Use RAPPDiscovery with action=process_transcript for customer_name=CUSTOMER
with transcript: [YOUR TRANSCRIPT]
```

**Output**: Structured extraction of:
- Problem statements with severity
- Data sources with access levels
- Stakeholder map
- Success criteria
- Timeline and budget

#### Step 2: QG1 - Transcript Validation
**Purpose**: Ensure we have enough information to proceed.

**Scoring Criteria** (1-10 each):
| Criterion | Description |
|-----------|-------------|
| Problem Clarity | Is the problem specific and quantified? |
| Data Availability | Are systems accessible? |
| Stakeholder Alignment | Are decision-makers identified? |
| Success Criteria | Are metrics measurable? |
| Scope Boundaries | Is MVP scope reasonable? |

**Decisions**:
- **PASS** (≥7 average): Proceed to MVP
- **CLARIFY** (5-7): Need specific clarifications
- **FAIL** (<5): Requires another discovery call

**Agent**: `RAPPQualityGate`
```
Use RAPPQualityGate with gate=QG1 for customer_name=CUSTOMER
project_name=PROJECT with input_data=[discovery data]
```

---

### Phase 2: Design (Steps 3-4)

#### Step 3: Generate MVP Poke Document
**Purpose**: Create customer-facing proposal document.

**Document Structure**:
1. Executive Summary
2. Problem Statement
   - Current State
   - Business Impact
   - Root Cause
3. Proposed Solution
   - Agent Name
   - Core Capability
   - How It Works
4. MVP Features (Priority Table)
5. Out of Scope
6. Data Requirements
7. Success Metrics
8. Timeline & Milestones
9. Risks & Mitigations
10. Investment Summary
11. Approval Section

**Agent**: `RAPPMVPGenerator`
```
Use RAPPMVPGenerator with action=generate_full_document
for customer_name=CUSTOMER project_name=PROJECT
problem_statement="..." discovery_data=[data]
```

#### Step 4: QG2 - Customer Validation
**Purpose**: Get explicit sign-off. **SCOPE LOCKS HERE**.

**What Gets Approved**:
- Feature list
- Timeline
- Success metrics
- Out-of-scope items
- Integration points

**After QG2 PROCEED**:
- No new features without change request
- "Nice to haves" go to Phase 2
- Timeline is committed

---

### Phase 3: Build (Steps 5-6)

#### Step 5: Generate Agent Code
**Purpose**: Create production-ready Python code.

**Code Requirements**:
```python
from agents.basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyAgent'
        self.metadata = {
            "name": self.name,
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        try:
            # Business logic
            return json.dumps({"status": "success", ...})
        except Exception as e:
            return json.dumps({"status": "error", "error": str(e)})
```

**Agent**: `RAPPCodeGenerator`
```
Use RAPPCodeGenerator with action=generate_agent
agent_name=MyAgent agent_description="..."
features=["Feature 1", "Feature 2"]
data_sources=[{"name": "System", "type": "API"}]
customer_name=CUSTOMER
```

#### Step 6: QG3 - Code Quality Review
**Purpose**: Validate security and quality.

**Review Categories**:
| Category | Checks |
|----------|--------|
| Pattern Validation | BasicAgent pattern, metadata schema |
| Security Audit | No hardcoded creds, input validation |
| Logic Correctness | Error handling, edge cases |
| Integration | Azure patterns, API usage |
| Code Quality | Naming, logging, complexity |

**Decisions**:
- **PASS**: Ready for deployment
- **FIX_REQUIRED**: Issues with specific fixes
- **FAIL**: Critical issues, regenerate

---

### Phase 4: Prototype (Steps 7-8)

#### Step 7: Deploy Prototype
**Actions**:
1. Deploy Azure Function App
2. Upload agent to Azure File Storage
3. Configure environment variables
4. Set up M365 Copilot declarative agent
5. Test endpoint connectivity

**Agent**: `RAPPCodeGenerator`
```
Use RAPPCodeGenerator with action=generate_deployment
agent_name=MyAgent customer_name=CUSTOMER
```

#### Step 8: QG4 - Demo Review
**The Waiter Pattern Test**:
> "Would you hire this agent as a waiter?"
> - Does it understand the order correctly?
> - Does it respond in reasonable time?
> - Does it handle special requests?
> - Does it escalate appropriately?

**Decisions**:
- **PASS**: Ready for video demo
- **POLISH**: Minor issues to fix
- **FAIL**: Major issues, iterate

---

### Phase 5: Demo (Steps 9-10)

#### Step 9: Create Video Demo
**Requirements**:
- 60-90 seconds total
- 6-10 demo steps
- Specific business metrics
- Industry-appropriate language
- Clear call-to-action

**Output**: AutoVideos-compatible JSON

#### Step 10: QG5 - Final Demo Review
**Evaluation**:
- Opening hook effectiveness
- Problem illustration
- Solution "wow moment"
- Metrics specificity
- Industry accuracy
- Closing and CTA

---

### Phase 6: Iteration (Step 11)

#### Step 11: Iteration Loop
**Feedback Classification**:
| Type | Action |
|------|--------|
| Bug | Fix immediately |
| Polish | Fix in current iteration |
| Feature | If in scope, add to iteration |
| Scope Creep | Document for Phase 2 |

**Rules**:
- Maximum 3 iterations
- Scope creep goes to Phase 2
- Each iteration requires QG4/QG5 revalidation

---

### Phase 7: Production (Steps 12-14)

#### Step 12: Production Deployment
**Checklist**:
- [ ] Security hardening
- [ ] Key Vault for secrets
- [ ] Monitoring and alerts
- [ ] Documentation
- [ ] Runbooks
- [ ] Customer handoff

#### Step 13: QG6 - Post-Deployment Audit
**Metrics to Collect**:
- System health (uptime, latency, errors)
- Usage patterns (adoption, frequency)
- Business value (ROI, time saved)
- Customer feedback

#### Step 14: Scale & Maintain
**Activities**:
- Optimization backlog
- Template extraction
- Phase 2 planning
- Lessons learned

---

## Project Tracking

### Create Project
```
Use ProjectTracker with action=create
customer_name=CUSTOMER project_name=PROJECT
```

### Update Progress
```
Use ProjectTracker with action=update project_id=ID
current_step=N completed_steps=[1,2,...]
step_notes={"1": "Discovery done", "2": "QG1 passed 8.5/10"}
step_decisions={"1": "COMPLETE", "2": "PASS"}
```

### Get Project Details
```
Use ProjectTracker with action=get project_id=ID
```

### List All Projects
```
Use ProjectTracker with action=list
```

### Export Project
```
Use ProjectTracker with action=export project_id=ID
```

---

## Common Pitfalls

### 1. Skipping Discovery
**Problem**: Building without understanding the problem
**Solution**: Always complete Step 1 and pass QG1

### 2. Scope Creep
**Problem**: Adding features after QG2
**Solution**: All new requests go to Phase 2 backlog

### 3. Ignoring Quality Gates
**Problem**: Rushing past failures
**Solution**: Gates exist to prevent rework - address concerns

### 4. Not Tracking Progress
**Problem**: Losing project state
**Solution**: Update ProjectTracker after every step

### 5. Hardcoded Credentials
**Problem**: Security vulnerabilities
**Solution**: QG3 catches this - use environment variables

---

## API Reference

### RAPPDiscovery Agent
```json
{
  "action": "process_transcript | validate_discovery | generate_summary",
  "customer_name": "string",
  "transcript": "string",
  "existing_context": {}
}
```

### RAPPQualityGate Agent
```json
{
  "gate": "QG1 | QG2 | QG3 | QG4 | QG5 | QG6",
  "customer_name": "string",
  "project_name": "string",
  "input_data": {}
}
```

### RAPPMVPGenerator Agent
```json
{
  "action": "generate_full_document | generate_executive_summary | ...",
  "customer_name": "string",
  "project_name": "string",
  "problem_statement": "string",
  "discovery_data": {}
}
```

### RAPPCodeGenerator Agent
```json
{
  "action": "generate_agent | generate_metadata | generate_tests | generate_deployment",
  "agent_name": "string",
  "agent_description": "string",
  "features": ["string"],
  "data_sources": [{}],
  "customer_name": "string"
}
```

### ProjectTracker Agent
```json
{
  "action": "create | update | list | get | delete | export",
  "project_id": "string",
  "customer_name": "string",
  "project_name": "string",
  "current_step": 1-14,
  "completed_steps": [1,2,...],
  "step_notes": {"1": "note"},
  "step_checklists": {"1": {"item": true}},
  "step_decisions": {"1": "PASS"}
}
```

---

## Success Stories

### Example: Video Production Automation
- **Problem**: Manual video production taking days per video
- **Solution**: Automated storyboard and script generation
- **Result**: QG1 passed 8.6/10, pipeline in progress

### Example: Enterprise Discovery Project
- **Problem**: [Your problem statement here]
- **Status**: Step 1 of 14

---

## Getting Help

- **Claude Code Agent**: `/rapp` to start the guide
- **Step-by-step**: `/rapp-step N` for specific step guidance
- **Documentation**: This file
- **Test Script**: `python test_rapp_pipeline_aibast.py`
