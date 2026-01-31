"""
CAF Migration Advisor Agent
Purpose: Analyze existing AI agent implementations and provide migration guidance based on
Microsoft's Azure Cloud Adoption Framework for AI Agents.

This agent helps convert custom agent implementations to Microsoft's recommended patterns:
- Microsoft Foundry Agent Service (PaaS - recommended)
- Microsoft Copilot Studio (SaaS - low/no code)
- Microsoft Agent Framework SDK (code-first)

Key CAF Recommendations:
1. Technology selection based on skill level and requirements
2. Agent types: Productivity, Action, Automation
3. Core components: Model, Instructions, Retrieval, Actions/Tools, Memory
4. Architecture: Single vs Multi-agent patterns
5. Governance: Purview, Defender, Azure Policy, Entra
6. Protocols: MCP (Model Context Protocol), A2A (Agent-to-Agent)
"""

import json
import logging
import os
from datetime import datetime
from agents.basic_agent import BasicAgent
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Microsoft CAF Framework Knowledge Base
CAF_KNOWLEDGE_BASE = {
    "technology_options": {
        "foundry_agent_service": {
            "name": "Microsoft Foundry Agent Service",
            "type": "PaaS",
            "skill_level": ["pro-code", "low-code", "no-code"],
            "best_for": "Enterprise teams wanting managed infrastructure with flexibility",
            "features": [
                "Built-in agent orchestration",
                "Managed memory and state",
                "MCP (Model Context Protocol) support",
                "A2A (Agent-to-Agent) communication",
                "Workflow orchestration",
                "Built-in security and governance",
                "Azure OpenAI integration",
                "Evaluation and observability"
            ],
            "migration_effort": "medium",
            "url": "https://azure.microsoft.com/services/ai-foundry/"
        },
        "copilot_studio": {
            "name": "Microsoft Copilot Studio",
            "type": "SaaS",
            "skill_level": ["low-code", "no-code"],
            "best_for": "Business users and citizen developers",
            "features": [
                "Visual agent builder",
                "Pre-built connectors",
                "Teams/M365 integration",
                "Power Platform ecosystem",
                "Declarative agents for M365 Copilot"
            ],
            "migration_effort": "low",
            "url": "https://copilotstudio.microsoft.com"
        },
        "agent_framework_sdk": {
            "name": "Microsoft Agent Framework SDK",
            "type": "SDK",
            "skill_level": ["pro-code"],
            "best_for": "Developers wanting full control with code-first approach",
            "features": [
                "AutoGen-based multi-agent patterns",
                "Semantic Kernel integration",
                "Custom orchestration",
                "Language support: Python, C#, JavaScript",
                "Local and cloud deployment"
            ],
            "migration_effort": "medium-high",
            "url": "https://github.com/microsoft/autogen"
        }
    },
    "agent_types": {
        "productivity": {
            "description": "Retrieves information and answers questions",
            "examples": ["Knowledge Q&A", "Document search", "FAQ bots"],
            "capabilities": ["retrieval", "reasoning"],
            "complexity": "low-medium"
        },
        "action": {
            "description": "Performs specific tasks with tools",
            "examples": ["Form filling", "Booking", "API calls"],
            "capabilities": ["retrieval", "reasoning", "tool_use"],
            "complexity": "medium"
        },
        "automation": {
            "description": "Completes multi-step workflows autonomously",
            "examples": ["End-to-end processes", "Complex workflows", "Multi-agent coordination"],
            "capabilities": ["retrieval", "reasoning", "tool_use", "planning", "orchestration"],
            "complexity": "high"
        }
    },
    "core_components": {
        "model": "Generative AI model (Azure OpenAI GPT-4o, etc.)",
        "instructions": "System prompts defining agent behavior and personality",
        "retrieval": "Knowledge grounding via RAG, vector search, knowledge graphs",
        "actions": "Tools/functions the agent can invoke (MCP protocol recommended)",
        "memory": "Context persistence across conversations (short-term, long-term, shared)"
    },
    "architecture_patterns": {
        "single_agent": {
            "when_to_use": [
                "Simple, well-defined tasks",
                "Clear boundaries",
                "Low complexity tools",
                "Predictable workflows"
            ],
            "benefits": ["Simpler to build", "Easier to debug", "Lower latency"]
        },
        "multi_agent": {
            "when_to_use": [
                "Complex domain expertise needed",
                "Parallel task execution",
                "Specialized agent roles",
                "Scalability requirements"
            ],
            "patterns": ["Hierarchical", "Peer-to-peer", "Workflow-based"],
            "benefits": ["Modularity", "Specialization", "Parallel execution"]
        }
    },
    "governance": {
        "identity": "Microsoft Entra ID for authentication and authorization",
        "data_protection": "Microsoft Purview for data classification and DLP",
        "security": "Microsoft Defender for threat protection",
        "policy": "Azure Policy for compliance and guardrails",
        "observability": "Application Insights, Azure Monitor"
    },
    "protocols": {
        "mcp": {
            "name": "Model Context Protocol",
            "purpose": "Standardized tool/action interface for AI models",
            "benefits": ["Interoperability", "Reusable tools", "Consistent interface"]
        },
        "a2a": {
            "name": "Agent-to-Agent Protocol",
            "purpose": "Standardized communication between agents",
            "benefits": ["Multi-agent orchestration", "Agent discovery", "Task delegation"]
        }
    }
}


def parse_llm_json_response(response_text: str, fallback_key: str = "raw_response") -> dict:
    """Parse JSON from LLM response, handling markdown code blocks."""
    try:
        text = response_text
        if '```json' in text:
            text = text.split('```json')[-1].split('```')[0]
        elif '```' in text:
            parts = text.split('```')
            if len(parts) >= 2:
                text = parts[1]
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(text[json_start:json_end])
        else:
            return {fallback_key: response_text}
    except json.JSONDecodeError:
        return {fallback_key: response_text}


class CAFMigrationAdvisorAgent(BasicAgent):
    """
    CAF Migration Advisor Agent for analyzing and converting AI agent implementations
    to Microsoft's recommended Cloud Adoption Framework patterns.

    Capabilities:
    - Analyze existing agent code against CAF best practices
    - Recommend target platform (Foundry, Copilot Studio, Agent Framework SDK)
    - Generate migration plans and code conversion suggestions
    - Identify governance and security gaps
    - Provide MCP tool conversion guidance
    """

    def __init__(self):
        self.name = 'CAFMigrationAdvisor'
        self.metadata = {
            "name": self.name,
            "description": "Analyzes AI agent implementations against Microsoft's Cloud Adoption Framework and provides migration guidance to recommended platforms (Foundry Agent Service, Copilot Studio, Agent Framework SDK). Use for architecture assessment, migration planning, and code conversion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The analysis or migration action to perform",
                        "enum": [
                            "analyze_agent",
                            "analyze_architecture",
                            "recommend_platform",
                            "generate_migration_plan",
                            "convert_to_mcp",
                            "assess_governance",
                            "full_assessment"
                        ]
                    },
                    "agent_code": {
                        "type": "string",
                        "description": "Python source code of the agent to analyze"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent being analyzed"
                    },
                    "architecture_description": {
                        "type": "string",
                        "description": "Description of current agent architecture"
                    },
                    "requirements": {
                        "type": "object",
                        "description": "Project requirements for platform recommendation",
                        "properties": {
                            "skill_level": {
                                "type": "string",
                                "enum": ["pro-code", "low-code", "no-code"]
                            },
                            "agent_type": {
                                "type": "string",
                                "enum": ["productivity", "action", "automation"]
                            },
                            "multi_agent_needed": {"type": "boolean"},
                            "m365_integration": {"type": "boolean"},
                            "custom_orchestration": {"type": "boolean"}
                        }
                    },
                    "target_platform": {
                        "type": "string",
                        "description": "Target platform for migration",
                        "enum": ["foundry", "copilot_studio", "agent_framework"]
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def _get_openai_client(self):
        """Initialize Azure OpenAI client with Entra ID authentication."""
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        return AzureOpenAI(
            azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
            azure_ad_token_provider=token_provider,
            api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
        )

    def perform(self, **kwargs):
        """Execute CAF migration advisory operations."""
        action = kwargs.get('action')

        if not action:
            return json.dumps({
                "status": "error",
                "error": "Action is required. Choose from: analyze_agent, analyze_architecture, recommend_platform, generate_migration_plan, convert_to_mcp, assess_governance, full_assessment"
            })

        try:
            if action == 'analyze_agent':
                return self._analyze_agent(kwargs)
            elif action == 'analyze_architecture':
                return self._analyze_architecture(kwargs)
            elif action == 'recommend_platform':
                return self._recommend_platform(kwargs)
            elif action == 'generate_migration_plan':
                return self._generate_migration_plan(kwargs)
            elif action == 'convert_to_mcp':
                return self._convert_to_mcp(kwargs)
            elif action == 'assess_governance':
                return self._assess_governance(kwargs)
            elif action == 'full_assessment':
                return self._full_assessment(kwargs)
            else:
                return json.dumps({
                    "status": "error",
                    "error": f"Unknown action: {action}"
                })

        except Exception as e:
            logger.error(f"Error in CAFMigrationAdvisor: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "agent": self.name
            })

    def _analyze_agent(self, kwargs):
        """Analyze a single agent against CAF best practices."""
        agent_code = kwargs.get('agent_code', '')
        agent_name = kwargs.get('agent_name', 'Unknown Agent')

        if not agent_code:
            return json.dumps({
                "status": "error",
                "error": "agent_code is required for analysis"
            })

        client = self._get_openai_client()

        prompt = f"""You are a Microsoft Cloud Adoption Framework (CAF) expert for AI Agents.
Analyze this agent implementation against CAF best practices.

AGENT NAME: {agent_name}

AGENT CODE:
```python
{agent_code}
```

MICROSOFT CAF FRAMEWORK REFERENCE:
{json.dumps(CAF_KNOWLEDGE_BASE, indent=2)}

Analyze and return JSON:
{{
  "agentName": "{agent_name}",
  "cafAssessment": {{
    "agentType": "productivity|action|automation",
    "agentTypeRationale": "why this classification",
    "coreComponents": {{
      "model": {{"present": true|false, "implementation": "description", "cafCompliance": "compliant|partial|non-compliant"}},
      "instructions": {{"present": true|false, "implementation": "description", "cafCompliance": "compliant|partial|non-compliant"}},
      "retrieval": {{"present": true|false, "implementation": "description", "cafCompliance": "compliant|partial|non-compliant"}},
      "actions": {{"present": true|false, "implementation": "description", "cafCompliance": "compliant|partial|non-compliant"}},
      "memory": {{"present": true|false, "implementation": "description", "cafCompliance": "compliant|partial|non-compliant"}}
    }},
    "overallCompliance": "high|medium|low",
    "complianceScore": 0-100
  }},
  "currentPatterns": {{
    "toolDefinition": "how tools/functions are defined",
    "orchestration": "how agent is orchestrated",
    "stateManagement": "how state/memory is managed",
    "errorHandling": "error handling approach"
  }},
  "gaps": [
    {{
      "area": "specific gap area",
      "currentState": "what exists now",
      "cafRecommendation": "what CAF recommends",
      "impact": "HIGH|MEDIUM|LOW",
      "migrationEffort": "HIGH|MEDIUM|LOW"
    }}
  ],
  "strengths": ["list of things already aligned with CAF"],
  "recommendations": [
    {{
      "priority": 1,
      "recommendation": "specific recommendation",
      "rationale": "why this matters",
      "effort": "HIGH|MEDIUM|LOW"
    }}
  ],
  "suggestedPlatform": "foundry|copilot_studio|agent_framework",
  "platformRationale": "why this platform"
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        analysis = parse_llm_json_response(result, "raw_analysis")

        return json.dumps({
            "status": "success",
            "action": "analyze_agent",
            "agent_name": agent_name,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        })

    def _analyze_architecture(self, kwargs):
        """Analyze overall agent architecture against CAF patterns."""
        architecture_description = kwargs.get('architecture_description', '')
        agent_code = kwargs.get('agent_code', '')

        if not architecture_description and not agent_code:
            return json.dumps({
                "status": "error",
                "error": "Either architecture_description or agent_code is required"
            })

        client = self._get_openai_client()

        prompt = f"""You are a Microsoft CAF expert for AI Agent architecture.
Analyze this agent system architecture against CAF patterns.

ARCHITECTURE DESCRIPTION:
{architecture_description}

{f"SAMPLE CODE: ```python\n{agent_code}\n```" if agent_code else ""}

MICROSOFT CAF ARCHITECTURE PATTERNS:
{json.dumps(CAF_KNOWLEDGE_BASE['architecture_patterns'], indent=2)}

Analyze and return JSON:
{{
  "currentArchitecture": {{
    "pattern": "single_agent|multi_agent|hybrid",
    "description": "description of current architecture",
    "components": ["list of architectural components"]
  }},
  "cafAlignment": {{
    "pattern": "recommended CAF pattern",
    "rationale": "why this pattern is recommended",
    "currentGaps": ["gaps in current architecture"]
  }},
  "singleVsMultiAgent": {{
    "recommendation": "single|multi",
    "reasons": ["list of reasons"],
    "considerations": ["things to consider"]
  }},
  "orchestrationAnalysis": {{
    "currentApproach": "description",
    "cafRecommendation": "Foundry Workflows|Semantic Kernel|AutoGen|Custom",
    "migrationPath": "steps to migrate"
  }},
  "scalabilityAssessment": {{
    "currentScore": 1-10,
    "bottlenecks": ["identified bottlenecks"],
    "improvements": ["suggested improvements"]
  }},
  "recommendations": [
    {{
      "area": "architecture area",
      "recommendation": "specific recommendation",
      "priority": "HIGH|MEDIUM|LOW",
      "effort": "HIGH|MEDIUM|LOW"
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        analysis = parse_llm_json_response(result, "raw_analysis")

        return json.dumps({
            "status": "success",
            "action": "analyze_architecture",
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        })

    def _recommend_platform(self, kwargs):
        """Recommend target Microsoft platform based on requirements."""
        requirements = kwargs.get('requirements', {})

        # Default requirements if not provided
        skill_level = requirements.get('skill_level', 'pro-code')
        agent_type = requirements.get('agent_type', 'action')
        multi_agent_needed = requirements.get('multi_agent_needed', False)
        m365_integration = requirements.get('m365_integration', False)
        custom_orchestration = requirements.get('custom_orchestration', False)

        client = self._get_openai_client()

        prompt = f"""You are a Microsoft platform advisor for AI agents.
Based on these requirements, recommend the best Microsoft platform.

REQUIREMENTS:
- Skill Level: {skill_level}
- Agent Type: {agent_type}
- Multi-Agent Needed: {multi_agent_needed}
- M365 Integration: {m365_integration}
- Custom Orchestration: {custom_orchestration}

AVAILABLE PLATFORMS:
{json.dumps(CAF_KNOWLEDGE_BASE['technology_options'], indent=2)}

Provide recommendation in JSON:
{{
  "primaryRecommendation": {{
    "platform": "foundry_agent_service|copilot_studio|agent_framework_sdk",
    "confidence": 1-100,
    "rationale": "detailed rationale",
    "keyBenefits": ["list of benefits for this use case"],
    "limitations": ["limitations to consider"],
    "migrationEffort": "LOW|MEDIUM|HIGH"
  }},
  "alternativeOptions": [
    {{
      "platform": "alternative platform",
      "whenToConsider": "scenarios when this might be better",
      "tradeoffs": ["tradeoffs vs primary recommendation"]
    }}
  ],
  "hybridApproach": {{
    "recommended": true|false,
    "description": "if hybrid, describe the approach",
    "components": {{"platform1": "what it handles", "platform2": "what it handles"}}
  }},
  "implementationPath": {{
    "phase1": "initial setup steps",
    "phase2": "core development",
    "phase3": "deployment and integration"
  }},
  "costConsiderations": {{
    "model": "consumption|subscription|per-seat",
    "estimatedRange": "rough cost guidance",
    "optimizationTips": ["cost optimization suggestions"]
  }}
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        recommendation = parse_llm_json_response(result, "raw_recommendation")

        return json.dumps({
            "status": "success",
            "action": "recommend_platform",
            "requirements": requirements,
            "recommendation": recommendation,
            "caf_reference": CAF_KNOWLEDGE_BASE['technology_options'],
            "generated_at": datetime.now().isoformat()
        })

    def _generate_migration_plan(self, kwargs):
        """Generate detailed migration plan to target platform."""
        agent_code = kwargs.get('agent_code', '')
        agent_name = kwargs.get('agent_name', 'Agent')
        target_platform = kwargs.get('target_platform', 'foundry')

        if not agent_code:
            return json.dumps({
                "status": "error",
                "error": "agent_code is required for migration planning"
            })

        platform_info = CAF_KNOWLEDGE_BASE['technology_options'].get(
            f"{target_platform}_agent_service" if target_platform == 'foundry' else target_platform,
            CAF_KNOWLEDGE_BASE['technology_options']['foundry_agent_service']
        )

        client = self._get_openai_client()

        prompt = f"""You are a Microsoft migration expert. Generate a detailed migration plan.

CURRENT AGENT: {agent_name}
```python
{agent_code}
```

TARGET PLATFORM: {target_platform}
{json.dumps(platform_info, indent=2)}

CAF BEST PRACTICES:
{json.dumps(CAF_KNOWLEDGE_BASE['core_components'], indent=2)}

Generate a comprehensive migration plan in JSON:
{{
  "migrationPlan": {{
    "summary": "One paragraph summary",
    "totalEffort": "LOW|MEDIUM|HIGH",
    "estimatedComplexity": 1-10,
    "riskLevel": "LOW|MEDIUM|HIGH"
  }},
  "preRequisites": [
    {{
      "item": "prerequisite",
      "description": "why needed",
      "documentation": "relevant doc link or resource"
    }}
  ],
  "migrationPhases": [
    {{
      "phase": 1,
      "name": "phase name",
      "description": "what happens in this phase",
      "tasks": [
        {{
          "task": "specific task",
          "details": "how to do it",
          "codeChanges": "required code changes if any"
        }}
      ],
      "deliverables": ["list of deliverables"],
      "validationCriteria": ["how to validate completion"]
    }}
  ],
  "codeConversions": [
    {{
      "component": "component name",
      "currentImplementation": "current code pattern",
      "targetImplementation": "target code pattern",
      "conversionGuide": "step by step guide",
      "sampleCode": "example converted code"
    }}
  ],
  "dataAndStateMigration": {{
    "currentStorage": "current storage approach",
    "targetStorage": "target storage in new platform",
    "migrationStrategy": "how to migrate data"
  }},
  "testingStrategy": {{
    "unitTests": "unit testing approach",
    "integrationTests": "integration testing approach",
    "validationChecklist": ["items to validate"]
  }},
  "rollbackPlan": {{
    "triggers": ["when to rollback"],
    "steps": ["rollback steps"]
  }},
  "postMigration": {{
    "monitoring": "monitoring setup",
    "optimization": "optimization opportunities",
    "documentation": "documentation to update"
  }}
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        plan = parse_llm_json_response(result, "raw_plan")

        return json.dumps({
            "status": "success",
            "action": "generate_migration_plan",
            "agent_name": agent_name,
            "target_platform": target_platform,
            "migration_plan": plan,
            "generated_at": datetime.now().isoformat()
        })

    def _convert_to_mcp(self, kwargs):
        """Convert existing tool/function definitions to MCP format."""
        agent_code = kwargs.get('agent_code', '')
        agent_name = kwargs.get('agent_name', 'Agent')

        if not agent_code:
            return json.dumps({
                "status": "error",
                "error": "agent_code is required for MCP conversion"
            })

        client = self._get_openai_client()

        prompt = f"""You are an MCP (Model Context Protocol) expert.
Convert this agent's tools/functions to MCP-compliant format.

CURRENT AGENT: {agent_name}
```python
{agent_code}
```

MCP PROTOCOL INFO:
{json.dumps(CAF_KNOWLEDGE_BASE['protocols']['mcp'], indent=2)}

Generate MCP conversion in JSON:
{{
  "mcpConversion": {{
    "agentName": "{agent_name}",
    "currentToolFormat": "description of current format",
    "conversionNeeded": true|false
  }},
  "tools": [
    {{
      "name": "tool_name",
      "currentDefinition": "current JSON schema or function signature",
      "mcpDefinition": {{
        "name": "mcp_tool_name",
        "description": "tool description",
        "inputSchema": {{
          "type": "object",
          "properties": {{}},
          "required": []
        }},
        "annotations": {{
          "title": "Human readable title",
          "readOnly": false,
          "destructive": false
        }}
      }},
      "implementationChanges": "required code changes"
    }}
  ],
  "mcpServerSetup": {{
    "serverType": "stdio|http|websocket",
    "configurationSample": "sample MCP server configuration",
    "connectionGuide": "how to connect to the MCP server"
  }},
  "integrationCode": {{
    "pythonExample": "Python code to integrate MCP tools",
    "configExample": "Configuration file example"
  }},
  "benefits": ["benefits of MCP conversion"],
  "considerations": ["things to consider during conversion"]
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        conversion = parse_llm_json_response(result, "raw_conversion")

        return json.dumps({
            "status": "success",
            "action": "convert_to_mcp",
            "agent_name": agent_name,
            "mcp_conversion": conversion,
            "generated_at": datetime.now().isoformat()
        })

    def _assess_governance(self, kwargs):
        """Assess governance and security posture against CAF recommendations."""
        architecture_description = kwargs.get('architecture_description', '')
        agent_code = kwargs.get('agent_code', '')

        client = self._get_openai_client()

        prompt = f"""You are a Microsoft security and governance expert.
Assess this agent implementation against CAF governance requirements.

ARCHITECTURE:
{architecture_description if architecture_description else "Not provided - analyze from code"}

{f"CODE: ```python\n{agent_code}\n```" if agent_code else ""}

CAF GOVERNANCE FRAMEWORK:
{json.dumps(CAF_KNOWLEDGE_BASE['governance'], indent=2)}

Provide governance assessment in JSON:
{{
  "governanceAssessment": {{
    "overallScore": 1-100,
    "maturityLevel": "initial|developing|defined|managed|optimizing",
    "criticalGaps": ["list of critical gaps"]
  }},
  "identityAndAccess": {{
    "score": 1-10,
    "currentState": "current IAM approach",
    "cafRequirement": "Entra ID integration",
    "gaps": ["specific gaps"],
    "recommendations": ["specific recommendations"]
  }},
  "dataProtection": {{
    "score": 1-10,
    "currentState": "current data protection",
    "cafRequirement": "Purview integration",
    "gaps": ["specific gaps"],
    "recommendations": ["specific recommendations"]
  }},
  "security": {{
    "score": 1-10,
    "currentState": "current security posture",
    "cafRequirement": "Defender integration",
    "gaps": ["specific gaps"],
    "recommendations": ["specific recommendations"]
  }},
  "compliance": {{
    "score": 1-10,
    "currentState": "current compliance approach",
    "cafRequirement": "Azure Policy guardrails",
    "gaps": ["specific gaps"],
    "recommendations": ["specific recommendations"]
  }},
  "observability": {{
    "score": 1-10,
    "currentState": "current monitoring",
    "cafRequirement": "Application Insights, Azure Monitor",
    "gaps": ["specific gaps"],
    "recommendations": ["specific recommendations"]
  }},
  "implementationRoadmap": [
    {{
      "priority": 1,
      "area": "governance area",
      "action": "specific action",
      "azureService": "recommended Azure service",
      "effort": "LOW|MEDIUM|HIGH"
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        assessment = parse_llm_json_response(result, "raw_assessment")

        return json.dumps({
            "status": "success",
            "action": "assess_governance",
            "assessment": assessment,
            "caf_reference": CAF_KNOWLEDGE_BASE['governance'],
            "assessed_at": datetime.now().isoformat()
        })

    def _full_assessment(self, kwargs):
        """Perform comprehensive CAF assessment combining all analyses."""
        agent_code = kwargs.get('agent_code', '')
        agent_name = kwargs.get('agent_name', 'Agent System')
        architecture_description = kwargs.get('architecture_description', '')
        requirements = kwargs.get('requirements', {})

        if not agent_code:
            return json.dumps({
                "status": "error",
                "error": "agent_code is required for full assessment"
            })

        client = self._get_openai_client()

        prompt = f"""You are a senior Microsoft Cloud Adoption Framework consultant.
Perform a comprehensive assessment of this AI agent implementation.

AGENT/SYSTEM NAME: {agent_name}

ARCHITECTURE DESCRIPTION:
{architecture_description if architecture_description else "Infer from code analysis"}

CODE:
```python
{agent_code}
```

REQUIREMENTS:
{json.dumps(requirements, indent=2) if requirements else "Not specified - provide general guidance"}

COMPLETE CAF REFERENCE:
{json.dumps(CAF_KNOWLEDGE_BASE, indent=2)}

Provide comprehensive assessment in JSON:
{{
  "executiveSummary": {{
    "overview": "2-3 sentence overview",
    "currentMaturity": "initial|developing|defined|managed|optimizing",
    "recommendedPath": "primary recommendation",
    "keyFindings": ["top 3 findings"]
  }},
  "cafComplianceScorecard": {{
    "overall": 1-100,
    "byCategory": {{
      "architecture": {{"score": 1-100, "status": "compliant|partial|non-compliant"}},
      "components": {{"score": 1-100, "status": "compliant|partial|non-compliant"}},
      "governance": {{"score": 1-100, "status": "compliant|partial|non-compliant"}},
      "protocols": {{"score": 1-100, "status": "compliant|partial|non-compliant"}},
      "observability": {{"score": 1-100, "status": "compliant|partial|non-compliant"}}
    }}
  }},
  "agentClassification": {{
    "type": "productivity|action|automation",
    "complexity": "low|medium|high",
    "multiAgentRequired": true|false,
    "rationale": "explanation"
  }},
  "platformRecommendation": {{
    "primary": "foundry|copilot_studio|agent_framework",
    "confidence": 1-100,
    "rationale": "why this platform",
    "alternativeIf": "conditions for considering alternative"
  }},
  "gapAnalysis": {{
    "critical": ["critical gaps requiring immediate attention"],
    "important": ["important gaps to address"],
    "nice_to_have": ["improvements for future consideration"]
  }},
  "migrationRoadmap": {{
    "phase1_foundation": {{
      "focus": "what to focus on",
      "deliverables": ["deliverables"],
      "effort": "LOW|MEDIUM|HIGH"
    }},
    "phase2_migration": {{
      "focus": "what to focus on",
      "deliverables": ["deliverables"],
      "effort": "LOW|MEDIUM|HIGH"
    }},
    "phase3_optimization": {{
      "focus": "what to focus on",
      "deliverables": ["deliverables"],
      "effort": "LOW|MEDIUM|HIGH"
    }}
  }},
  "quickWins": [
    {{
      "action": "quick win action",
      "impact": "expected impact",
      "effort": "LOW"
    }}
  ],
  "riskAssessment": {{
    "migrationRisks": ["risks of migrating"],
    "stayingRisks": ["risks of not migrating"],
    "mitigations": ["risk mitigation strategies"]
  }},
  "nextSteps": [
    {{
      "step": 1,
      "action": "specific action",
      "owner": "suggested owner role",
      "dependencies": ["dependencies"]
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model=os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o'),
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.choices[0].message.content
        assessment = parse_llm_json_response(result, "raw_assessment")

        return json.dumps({
            "status": "success",
            "action": "full_assessment",
            "agent_name": agent_name,
            "full_assessment": assessment,
            "caf_knowledge_base_version": "Azure CAF for AI Agents - 2025",
            "assessed_at": datetime.now().isoformat()
        })


# Usage example
if __name__ == "__main__":
    agent = CAFMigrationAdvisorAgent()

    # Test with sample agent code
    sample_code = '''
class SampleAgent(BasicAgent):
    def __init__(self):
        self.name = 'Sample'
        self.metadata = {
            "name": self.name,
            "description": "A sample agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }

    def perform(self, **kwargs):
        return "Result"
'''

    result = agent.perform(
        action="analyze_agent",
        agent_code=sample_code,
        agent_name="SampleAgent"
    )
    print("Analysis Result:", json.loads(result)["status"])
