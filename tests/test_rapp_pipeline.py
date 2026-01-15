"""
RAPP Pipeline End-to-End Tests

Tests the complete RAPP Pipeline workflow with two realistic scenarios:
1. Capital Markets - Trade Reconciliation Agent
2. Call Center - Dynamics 365 Customer Service Agent

Run with: pytest tests/test_rapp_pipeline.py -v
Or: python tests/test_rapp_pipeline.py (for standalone execution)
"""

import json
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_fixtures import (
    CAPITAL_MARKETS_CUSTOMER,
    CAPITAL_MARKETS_TRANSCRIPT,
    CAPITAL_MARKETS_DISCOVERY_DATA,
    CAPITAL_MARKETS_AGENT_CONFIG,
    CAPITAL_MARKETS_EXPECTED_QG1,
    CALL_CENTER_CUSTOMER,
    CALL_CENTER_TRANSCRIPT,
    CALL_CENTER_DISCOVERY_DATA,
    CALL_CENTER_AGENT_CONFIG,
    CALL_CENTER_EXPECTED_QG1,
    TEST_USER_GUID
)


class MockOpenAIResponse:
    """Mock Azure OpenAI response for testing without API calls."""

    def __init__(self, content):
        self.choices = [MagicMock(message=MagicMock(content=content))]


class TestRAPPDiscoveryAgent(unittest.TestCase):
    """Test the RAPP Discovery Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'
        os.environ['AZURE_OPENAI_API_VERSION'] = '2025-01-01-preview'

        from agents.rapp_discovery_agent import RAPPDiscoveryAgent
        cls.agent = RAPPDiscoveryAgent()

    def test_agent_initialization(self):
        """Test that the discovery agent initializes correctly."""
        self.assertEqual(self.agent.name, 'RAPPDiscovery')
        self.assertIn('description', self.agent.metadata)
        self.assertIn('parameters', self.agent.metadata)

    def test_agent_metadata_schema(self):
        """Test that agent metadata follows correct schema."""
        params = self.agent.metadata['parameters']
        self.assertEqual(params['type'], 'object')
        self.assertIn('action', params['properties'])
        self.assertIn('prepare_call', params['properties']['action']['enum'])
        self.assertIn('process_transcript', params['properties']['action']['enum'])

    @patch('agents.rapp_discovery_agent.AzureOpenAI')
    def test_prepare_call_capital_markets(self, mock_openai_class):
        """Test discovery call preparation for Capital Markets scenario."""
        mock_response = MockOpenAIResponse("""
        # Discovery Call Preparation Guide

        ## Pre-Call Research
        - Research trade reconciliation challenges in investment banking
        - Understand T+1 settlement requirements
        - Review common OMS and clearing system integrations

        ## Key Questions
        1. What is your current daily trade volume?
        2. How many systems are involved in reconciliation?
        3. What is your current break resolution time?
        """)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='prepare_call',
            customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
            industry=CAPITAL_MARKETS_CUSTOMER['industry']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertEqual(result_data['action'], 'prepare_call')
        self.assertEqual(result_data['customer_name'], 'Meridian Capital Partners')
        self.assertIn('discovery_guide', result_data)

    @patch('agents.rapp_discovery_agent.AzureOpenAI')
    def test_prepare_call_call_center(self, mock_openai_class):
        """Test discovery call preparation for Call Center scenario."""
        mock_response = MockOpenAIResponse("""
        # Discovery Call Preparation Guide

        ## Pre-Call Research
        - Review Dynamics 365 Customer Service capabilities
        - Understand insurance industry contact center benchmarks
        - Research Copilot Studio integration patterns

        ## Key Questions
        1. What is your current average handle time?
        2. How many systems do agents access during a call?
        3. What is your CSAT trend over the past 12 months?
        """)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='prepare_call',
            customer_name=CALL_CENTER_CUSTOMER['customer_name'],
            industry=CALL_CENTER_CUSTOMER['industry']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('discovery_guide', result_data)

    @patch('agents.rapp_discovery_agent.AzureOpenAI')
    def test_process_transcript_capital_markets(self, mock_openai_class):
        """Test transcript processing for Capital Markets scenario."""
        # Create a mock response that matches the expected JSON structure
        mock_json_response = json.dumps({
            "callMetadata": {
                "estimatedDuration": "47 minutes",
                "participants": [
                    {"name": "Sarah Chen", "role": "Managing Director, Operations", "company": "Meridian Capital Partners"},
                    {"name": "Marcus Williams", "role": "VP Technology", "company": "Meridian Capital Partners"},
                    {"name": "Jennifer Park", "role": "Head of Trade Operations", "company": "Meridian Capital Partners"}
                ]
            },
            "businessContext": {
                "industry": "Capital Markets / Investment Banking",
                "companySize": "enterprise",
                "currentSystems": ["Charles River OMS", "DTCC", "Goldman Prime Broker", "Morgan Stanley Prime"],
                "technicalMaturity": "high"
            },
            "problemStatements": [
                {
                    "problem": "Manual trade reconciliation takes 4-5 hours daily",
                    "verbatimQuote": "On a good day, four to five hours. On a bad day after high volume or a market event, we're talking eight hours or more.",
                    "category": "EFFICIENCY",
                    "severity": "HIGH",
                    "currentProcess": "Manual comparison of OMS, clearing, and prime broker data",
                    "businessImpact": "$180,000 annual labor cost, $47,000 quarterly penalties"
                }
            ],
            "dataSources": [
                {"systemName": "Charles River OMS", "dataType": "API", "accessLevel": "Full", "dataVolume": "15,000 trades/day", "integrationComplexity": "LOW"},
                {"systemName": "DTCC Clearing", "dataType": "File", "accessLevel": "Full", "dataVolume": "SFTP every 30 min", "integrationComplexity": "LOW"}
            ],
            "stakeholders": [
                {"name": "Sarah Chen", "role": "Managing Director, Operations", "influenceLevel": "DECISION_MAKER", "concerns": ["ROI", "Q2 timeline"], "enthusiasm": "HIGH"}
            ],
            "successCriteria": [
                {"metric": "Reconciliation Time", "currentValue": "4-5 hours", "targetValue": "30 minutes", "measurementMethod": "Time tracking"}
            ],
            "timeline": {
                "urgency": "HIGH",
                "targetLaunchDate": "Q2 2025",
                "budgetCycle": "Q2 board meeting",
                "keyMilestones": ["Prototype by March", "Production by end of Q2"]
            },
            "suggestedAgents": ["TradeReconciliationAgent", "BreakResolutionAgent"],
            "riskFactors": [],
            "nextSteps": ["Create MVP proposal", "Schedule technical deep-dive"]
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='process_transcript',
            customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
            transcript=CAPITAL_MARKETS_TRANSCRIPT
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertEqual(result_data['action'], 'process_transcript')
        self.assertIn('extracted_data', result_data)

        # Validate extracted data structure
        extracted = result_data['extracted_data']
        self.assertIn('problemStatements', extracted)
        self.assertIn('dataSources', extracted)
        self.assertIn('stakeholders', extracted)

    @patch('agents.rapp_discovery_agent.AzureOpenAI')
    def test_process_transcript_call_center(self, mock_openai_class):
        """Test transcript processing for Call Center scenario."""
        mock_json_response = json.dumps({
            "callMetadata": {
                "estimatedDuration": "52 minutes",
                "participants": [
                    {"name": "Michael Torres", "role": "VP Customer Experience", "company": "Pacific Northwest Insurance Group"}
                ]
            },
            "businessContext": {
                "industry": "Insurance / Financial Services",
                "companySize": "large",
                "currentSystems": ["Dynamics 365 Customer Service", "Guidewire PolicyCenter", "Oracle Financial Services", "Genesys Cloud"],
                "technicalMaturity": "high"
            },
            "problemStatements": [
                {
                    "problem": "Agents juggling 6-7 systems results in 12-minute average handle time",
                    "verbatimQuote": "Average handle time for a billing inquiry is 12 minutes. Industry benchmark is 6 minutes.",
                    "category": "EFFICIENCY",
                    "severity": "HIGH",
                    "currentProcess": "Manual navigation between multiple systems",
                    "businessImpact": "$2M+ annual savings potential"
                }
            ],
            "dataSources": [
                {"systemName": "Dynamics 365 Customer Service", "dataType": "API", "accessLevel": "Full", "dataVolume": "350 agents", "integrationComplexity": "LOW"}
            ],
            "stakeholders": [
                {"name": "Michael Torres", "role": "VP Customer Experience", "influenceLevel": "DECISION_MAKER", "concerns": ["CSAT improvement"], "enthusiasm": "HIGH"}
            ],
            "successCriteria": [
                {"metric": "Average Handle Time", "currentValue": "12 minutes", "targetValue": "6 minutes", "measurementMethod": "Genesys reporting"}
            ],
            "timeline": {
                "urgency": "HIGH",
                "targetLaunchDate": "Before March 2025",
                "budgetCycle": "Approved",
                "keyMilestones": ["Prototype in 30 days"]
            },
            "suggestedAgents": ["CustomerContextAgent", "CallSummaryAgent"],
            "riskFactors": [],
            "nextSteps": []
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='process_transcript',
            customer_name=CALL_CENTER_CUSTOMER['customer_name'],
            transcript=CALL_CENTER_TRANSCRIPT
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('extracted_data', result_data)

    def test_missing_action_returns_error(self):
        """Test that missing action parameter returns error."""
        result = self.agent.perform()
        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'error')
        self.assertIn('Action is required', result_data['error'])

    def test_missing_transcript_returns_error(self):
        """Test that process_transcript without transcript returns error."""
        result = self.agent.perform(action='process_transcript')
        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'error')
        self.assertIn('Transcript is required', result_data['error'])


class TestRAPPQualityGateAgent(unittest.TestCase):
    """Test the RAPP Quality Gate Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'

        from agents.rapp_quality_gate_agent import RAPPQualityGateAgent
        cls.agent = RAPPQualityGateAgent()

    def test_agent_initialization(self):
        """Test that the quality gate agent initializes correctly."""
        self.assertEqual(self.agent.name, 'RAPPQualityGate')
        self.assertIn('description', self.agent.metadata)

    def test_gate_configurations_exist(self):
        """Test that all 6 quality gates are configured."""
        expected_gates = ['QG1', 'QG2', 'QG3', 'QG4', 'QG5', 'QG6']
        for gate in expected_gates:
            self.assertIn(gate, self.agent.GATE_CONFIGS)

    @patch('agents.rapp_quality_gate_agent.AzureOpenAI')
    def test_evaluate_qg1_capital_markets(self, mock_openai_class):
        """Test QG1 evaluation for Capital Markets scenario."""
        mock_json_response = json.dumps({
            "gate": "QG1",
            "gateName": "Transcript Validation",
            "decision": "PASS",
            "overallScore": 8.2,
            "scores": {
                "problemClarity": {"score": 9, "notes": "Clear quantified problem statement"},
                "dataAvailability": {"score": 8, "notes": "Multiple data sources identified with access"},
                "stakeholderAlignment": {"score": 8, "notes": "Decision maker engaged"},
                "successCriteria": {"score": 8, "notes": "Measurable targets defined"},
                "scopeBoundaries": {"score": 8, "notes": "Clear timeline and constraints"}
            },
            "validatedProblemStatement": "Manual trade reconciliation takes 4-5 hours daily costing $180K annually with $47K quarterly penalties",
            "strengths": ["Quantified business impact", "Clear data access"],
            "concerns": ["Multiple prime brokers may complicate integration"],
            "clarifyingQuestions": [],
            "recommendations": ["Proceed to MVP generation"],
            "nextStep": "Generate MVP Poke"
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='evaluate',
            gate='QG1',
            customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
            context=CAPITAL_MARKETS_DISCOVERY_DATA
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        # The agent returns the parsed evaluation directly, not nested under 'evaluation'
        self.assertEqual(result_data['gate'], 'QG1')
        self.assertEqual(result_data['decision'], 'PASS')
        self.assertGreaterEqual(result_data['overallScore'], CAPITAL_MARKETS_EXPECTED_QG1['minimum_score'])

    @patch('agents.rapp_quality_gate_agent.AzureOpenAI')
    def test_evaluate_qg1_call_center(self, mock_openai_class):
        """Test QG1 evaluation for Call Center scenario."""
        mock_json_response = json.dumps({
            "gate": "QG1",
            "gateName": "Transcript Validation",
            "decision": "PASS",
            "overallScore": 8.4,
            "scores": {
                "problemClarity": {"score": 9, "notes": "CSAT decline clearly documented"},
                "dataAvailability": {"score": 8, "notes": "D365 and integrations available"},
                "stakeholderAlignment": {"score": 9, "notes": "VP and Director highly engaged"},
                "successCriteria": {"score": 8, "notes": "AHT target well defined"},
                "scopeBoundaries": {"score": 8, "notes": "Copilot Studio path clear"}
            },
            "validatedProblemStatement": "12-minute AHT vs 6-minute benchmark due to multi-system navigation",
            "strengths": ["Existing Copilot Studio license", "Clear D365 integration path"],
            "concerns": ["Multiple legacy system integrations needed"],
            "clarifyingQuestions": [],
            "recommendations": ["Proceed with billing inquiry scenario first"],
            "nextStep": "Generate MVP Poke"
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='evaluate',
            gate='QG1',
            customer_name=CALL_CENTER_CUSTOMER['customer_name'],
            context=CALL_CENTER_DISCOVERY_DATA
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertEqual(result_data['decision'], 'PASS')
        self.assertGreaterEqual(result_data['overallScore'], CALL_CENTER_EXPECTED_QG1['minimum_score'])

    @patch('agents.rapp_quality_gate_agent.AzureOpenAI')
    def test_evaluate_qg2_scope_lock(self, mock_openai_class):
        """Test QG2 scope lock evaluation."""
        mock_json_response = json.dumps({
            "gate": "QG2",
            "gateName": "Customer Validation",
            "decision": "PROCEED",
            "overallScore": 8.0,
            "scores": {
                "scopeAgreement": {"score": 8, "notes": "Features clearly defined"},
                "dataAccess": {"score": 8, "notes": "Data sources confirmed"},
                "stakeholderBuyIn": {"score": 8, "notes": "Stakeholder approval obtained"},
                "timelineAcceptance": {"score": 8, "notes": "Timeline agreed"}
            },
            "scopeLocked": True,
            "recommendations": ["Proceed to code generation"],
            "nextStep": "Generate Agent Code"
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='evaluate',
            gate='QG2',
            customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
            context={
                "mvp_document": "MVP Poke document content",
                "customer_approval": True
            }
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertEqual(result_data['gate'], 'QG2')

    def test_get_criteria_returns_gate_info(self):
        """Test that get_criteria returns gate configuration."""
        result = self.agent.perform(
            action='get_criteria',
            gate='QG1'
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('gate', result_data)
        self.assertEqual(result_data['gate'], 'QG1')
        self.assertIn('criteria', result_data)

    def test_invalid_gate_returns_error(self):
        """Test that invalid gate returns error."""
        result = self.agent.perform(
            action='evaluate',
            gate='QG99'
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'error')
        self.assertIn('Invalid gate', result_data['error'])


class TestRAPPMVPGeneratorAgent(unittest.TestCase):
    """Test the RAPP MVP Generator Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'

        from agents.rapp_mvp_generator_agent import RAPPMVPGeneratorAgent
        cls.agent = RAPPMVPGeneratorAgent()

    def test_agent_initialization(self):
        """Test that the MVP generator agent initializes correctly."""
        self.assertEqual(self.agent.name, 'RAPPMVPGenerator')

    @patch('agents.rapp_mvp_generator_agent.AzureOpenAI')
    def test_generate_poke_capital_markets(self, mock_openai_class):
        """Test MVP Poke generation for Capital Markets scenario."""
        mock_json_response = json.dumps({
            "status": "success",
            "document": """# Meridian Capital Partners - Trade Reconciliation Agent MVP

## Executive Summary
Automated trade reconciliation agent to reduce manual effort from 4-5 hours to 30 minutes daily.

## MVP Features
| Priority | Feature | Description |
|----------|---------|-------------|
| P0 | Trade Matching | Multi-source intelligent matching |
| P0 | Break Auto-Resolution | Common break type handling |
| P1 | Audit Trail | Compliance-ready logging |

## Success Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Reconciliation Time | 4-5 hours | 30 minutes |
| Auto-Resolution | 0% | 90% |
""",
            "features": {
                "p0": ["Multi-source trade data ingestion", "Intelligent trade matching", "Auto-resolution of common breaks"],
                "p1": ["Exception queue prioritization", "Audit trail generation"],
                "p2": ["Predictive break detection"]
            },
            "outOfScope": ["Historical data migration", "Counterparty portal"],
            "successMetrics": [
                {"metric": "Reconciliation Time", "current": "4-5 hours", "target": "30 minutes"},
                {"metric": "Auto-Resolution Rate", "current": "0%", "target": "90%"}
            ],
            "estimatedDays": 30
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='generate_poke',
            customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
            project_name='Trade Reconciliation Agent',
            problem_statement='Manual trade reconciliation takes 4-5 hours daily',
            discovery_data=CAPITAL_MARKETS_DISCOVERY_DATA
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('document', result_data)
        self.assertIn('features', result_data)
        self.assertIn('p0', result_data['features'])

    @patch('agents.rapp_mvp_generator_agent.AzureOpenAI')
    def test_generate_poke_call_center(self, mock_openai_class):
        """Test MVP Poke generation for Call Center scenario."""
        mock_json_response = json.dumps({
            "status": "success",
            "document": """# Pacific Northwest Insurance - Customer Service Copilot MVP

## Executive Summary
AI-powered agent assistant in D365 to reduce AHT from 12 to 6 minutes.

## MVP Features
| Priority | Feature | Description |
|----------|---------|-------------|
| P0 | Customer Context | Unified view on call connect |
| P0 | Suggested Responses | AI-powered recommendations |
| P1 | Auto Case Notes | Post-call documentation |
""",
            "features": {
                "p0": ["Unified customer context panel", "Auto-population on call connect", "Suggested responses"],
                "p1": ["Auto-generated case notes", "Next best action recommendations"],
                "p2": ["Sentiment analysis", "Retention offer suggestions"]
            },
            "outOfScope": ["Chatbot expansion", "Self-service portal"],
            "successMetrics": [
                {"metric": "Average Handle Time", "current": "12 minutes", "target": "6 minutes"},
                {"metric": "CSAT", "current": "3.6", "target": "4.2"}
            ],
            "estimatedDays": 30
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='generate_poke',
            customer_name=CALL_CENTER_CUSTOMER['customer_name'],
            project_name='Customer Service Copilot',
            problem_statement='12-minute AHT due to multi-system navigation',
            discovery_data=CALL_CENTER_DISCOVERY_DATA
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('document', result_data)

    @patch('agents.rapp_mvp_generator_agent.AzureOpenAI')
    def test_prioritize_features(self, mock_openai_class):
        """Test feature prioritization."""
        mock_json_response = json.dumps({
            "status": "success",
            "features": [
                {
                    "name": "Trade Matching Engine",
                    "description": "Intelligent matching across multiple data sources",
                    "priority": "P0",
                    "effort": "M",
                    "businessValue": 9,
                    "technicalRisk": "MEDIUM",
                    "dependencies": [],
                    "rationale": "Core functionality required for MVP"
                },
                {
                    "name": "Audit Trail",
                    "description": "Compliance logging of all actions",
                    "priority": "P1",
                    "effort": "S",
                    "businessValue": 7,
                    "technicalRisk": "LOW",
                    "dependencies": ["Trade Matching Engine"],
                    "rationale": "Required for compliance but not blocking"
                }
            ],
            "mvpCoreFeatures": ["Trade Matching Engine"],
            "deferredFeatures": ["Predictive Analytics"],
            "totalEffort": "M",
            "recommendation": "Focus on core matching first"
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='prioritize_features',
            discovery_data=CAPITAL_MARKETS_DISCOVERY_DATA,
            suggested_agents=['TradeReconciliationAgent']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('features', result_data)
        self.assertIn('mvpCoreFeatures', result_data)


class TestRAPPCodeGeneratorAgent(unittest.TestCase):
    """Test the RAPP Code Generator Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'

        from agents.rapp_code_generator_agent import RAPPCodeGeneratorAgent
        cls.agent = RAPPCodeGeneratorAgent()

    def test_agent_initialization(self):
        """Test that the code generator agent initializes correctly."""
        self.assertEqual(self.agent.name, 'RAPPCodeGenerator')

    @patch('agents.rapp_code_generator_agent.AzureOpenAI')
    def test_generate_agent_capital_markets(self, mock_openai_class):
        """Test agent code generation for Capital Markets scenario."""
        mock_code = '''
from agents.basic_agent import BasicAgent
import json

class TradeReconciliationAgent(BasicAgent):
    """Agent for automated trade reconciliation."""

    def __init__(self):
        self.name = 'TradeReconciliation'
        self.metadata = {
            "name": self.name,
            "description": "Reconciles trades across OMS, clearing, and prime broker systems",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["reconcile", "get_breaks", "resolve_break"]}
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action')
        if action == 'reconcile':
            return self._reconcile_trades(kwargs)
        return json.dumps({"status": "error", "error": f"Unknown action: {action}"})

    def _reconcile_trades(self, kwargs):
        return json.dumps({"status": "success", "matches": 0, "breaks": 0})
'''

        mock_json_response = json.dumps({
            "status": "success",
            "agent_name": "TradeReconciliationAgent",
            "code": mock_code,
            "filename": "trade_reconciliation_agent.py",
            "features_implemented": ["Trade matching", "Break detection"],
            "dependencies": ["basic_agent", "azure_file_storage"]
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='generate_agent',
            agent_name='TradeReconciliationAgent',
            agent_description='Automated trade reconciliation across multiple systems',
            features=CAPITAL_MARKETS_AGENT_CONFIG['features']['p0'],
            data_sources=CAPITAL_MARKETS_DISCOVERY_DATA['dataSources']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('code', result_data)
        self.assertIn('class TradeReconciliation', result_data['code'])

    @patch('agents.rapp_code_generator_agent.AzureOpenAI')
    def test_generate_agent_call_center(self, mock_openai_class):
        """Test agent code generation for Call Center scenario."""
        mock_code = '''
from agents.basic_agent import BasicAgent
import json

class CustomerServiceCopilotAgent(BasicAgent):
    """Copilot Studio agent for D365 Customer Service."""

    def __init__(self):
        self.name = 'CustomerServiceCopilot'
        self.metadata = {
            "name": self.name,
            "description": "Provides unified customer context and suggested responses",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["get_context", "suggest_response", "generate_notes"]}
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action')
        if action == 'get_context':
            return self._get_customer_context(kwargs)
        return json.dumps({"status": "error", "error": f"Unknown action: {action}"})

    def _get_customer_context(self, kwargs):
        return json.dumps({"status": "success", "context": {}})
'''

        mock_json_response = json.dumps({
            "status": "success",
            "agent_name": "CustomerServiceCopilotAgent",
            "code": mock_code,
            "filename": "customer_service_copilot_agent.py",
            "features_implemented": ["Customer context", "Suggested responses"],
            "dependencies": ["basic_agent"]
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='generate_agent',
            agent_name='CustomerServiceCopilotAgent',
            agent_description='Copilot Studio agent for D365 Customer Service',
            features=CALL_CENTER_AGENT_CONFIG['features']['p0'],
            data_sources=CALL_CENTER_DISCOVERY_DATA['dataSources']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('code', result_data)

    @patch('agents.rapp_code_generator_agent.AzureOpenAI')
    def test_generate_metadata(self, mock_openai_class):
        """Test metadata schema generation."""
        mock_json_response = json.dumps({
            "status": "success",
            "metadata": {
                "name": "TradeReconciliation",
                "description": "Reconciles trades across systems",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Action to perform",
                            "enum": ["reconcile", "get_breaks", "resolve_break"]
                        },
                        "trade_date": {
                            "type": "string",
                            "description": "Date to reconcile (YYYY-MM-DD)"
                        }
                    },
                    "required": ["action"]
                }
            },
            "valid_json_schema": True
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='generate_metadata',
            agent_name='TradeReconciliationAgent',
            features=['reconcile', 'get_breaks', 'resolve_break']
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('metadata', result_data)


class TestRAPPPipelineAgent(unittest.TestCase):
    """Test the RAPP Pipeline Orchestrator Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'

        from agents.rapp_pipeline_agent import RAPPPipelineAgent
        cls.agent = RAPPPipelineAgent()

    def test_agent_initialization(self):
        """Test that the pipeline agent initializes correctly."""
        self.assertEqual(self.agent.name, 'RAPPPipeline')

    def test_pipeline_steps_defined(self):
        """Test that all 14 pipeline steps are defined."""
        self.assertEqual(len(self.agent.PIPELINE_STEPS), 14)

        # Verify step structure
        for step_num, step_config in self.agent.PIPELINE_STEPS.items():
            self.assertIn('name', step_config)
            self.assertIn('type', step_config)

    def test_get_status(self):
        """Test pipeline status retrieval."""
        result = self.agent.perform(
            action='get_status',
            project_data={
                'current_step': 1,
                'completed_steps': [],
                'step_decisions': {}
            }
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('step_status', result_data)
        self.assertIn('progress_percent', result_data)

    def test_get_checklist(self):
        """Test checklist generation for a step."""
        result = self.agent.perform(
            action='get_checklist',
            step=1
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('checklist', result_data)
        self.assertEqual(result_data['step'], 1)

    @patch('agents.rapp_pipeline_agent.AzureOpenAI')
    def test_get_guidance_step_1(self, mock_openai_class):
        """Test guidance retrieval for Step 1."""
        mock_response = MockOpenAIResponse("""
        ## Step 1: Discovery Call Guidance

        ### Objectives
        - Understand the customer's business problem
        - Identify data sources and stakeholders
        - Define success criteria

        ### Best Practices
        - Ask open-ended questions
        - Listen for pain points and quantified impacts
        - Document everything
        """)

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='get_guidance',
            step_number=1,
            customer_name='Test Customer'
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')
        self.assertIn('guidance', result_data)

    @patch('agents.rapp_pipeline_agent.AzureOpenAI')
    def test_recommend_next_step(self, mock_openai_class):
        """Test next step recommendation."""
        mock_json_response = json.dumps({
            "recommended_step": 3,
            "reasoning": "QG1 passed, ready for MVP generation",
            "prerequisites_met": True,
            "blockers": []
        })

        mock_response = MockOpenAIResponse(mock_json_response)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = self.agent.perform(
            action='recommend_next',
            completed_steps=[1, 2],
            current_step=2
        )

        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'success')


class TestEndToEndPipeline(unittest.TestCase):
    """End-to-end integration tests for complete pipeline flows."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AZURE_OPENAI_API_KEY'] = 'test-key'
        os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://test.openai.azure.com/'
        os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = 'gpt-4o'

    def test_capital_markets_discovery_to_mvp(self):
        """Test Capital Markets scenario from discovery through MVP generation."""
        from agents.rapp_discovery_agent import RAPPDiscoveryAgent
        from agents.rapp_quality_gate_agent import RAPPQualityGateAgent
        from agents.rapp_mvp_generator_agent import RAPPMVPGeneratorAgent

        # Step 1: Process transcript
        disc_response = json.dumps({
            "callMetadata": {"estimatedDuration": "47 minutes", "participants": []},
            "problemStatements": CAPITAL_MARKETS_DISCOVERY_DATA['problemStatements'],
            "dataSources": CAPITAL_MARKETS_DISCOVERY_DATA['dataSources'],
            "stakeholders": CAPITAL_MARKETS_DISCOVERY_DATA['stakeholders'],
            "successCriteria": CAPITAL_MARKETS_DISCOVERY_DATA['successCriteria'],
            "timeline": CAPITAL_MARKETS_DISCOVERY_DATA['timeline'],
            "suggestedAgents": ["TradeReconciliationAgent"]
        })

        with patch.object(RAPPDiscoveryAgent, '_get_openai_client') as mock_disc:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(disc_response)
            mock_disc.return_value = mock_client

            discovery_agent = RAPPDiscoveryAgent()
            discovery_result = discovery_agent.perform(
                action='process_transcript',
                customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
                transcript=CAPITAL_MARKETS_TRANSCRIPT
            )

        discovery_data = json.loads(discovery_result)
        self.assertEqual(discovery_data['status'], 'success')

        # Step 2: QG1 evaluation
        qg1_response = json.dumps({
            "gate": "QG1",
            "gateName": "Transcript Validation",
            "decision": "PASS",
            "overallScore": 8.2,
            "scores": {},
            "validatedProblemStatement": "Manual reconciliation costs $180K annually",
            "nextStep": "Generate MVP"
        })

        with patch.object(RAPPQualityGateAgent, '_get_openai_client') as mock_qg:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(qg1_response)
            mock_qg.return_value = mock_client

            qg_agent = RAPPQualityGateAgent()
            qg_result = qg_agent.perform(
                action='evaluate',
                gate='QG1',
                customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
                context=discovery_data.get('extracted_data', {})
            )

        qg_data = json.loads(qg_result)
        self.assertEqual(qg_data['status'], 'success')
        self.assertEqual(qg_data['decision'], 'PASS')

        # Step 3: MVP generation
        mvp_response = json.dumps({
            "status": "success",
            "document": "# Trade Reconciliation Agent MVP",
            "features": {"p0": ["Matching"], "p1": ["Audit"], "p2": ["Predictive"]},
            "estimatedDays": 30
        })

        with patch.object(RAPPMVPGeneratorAgent, '_get_openai_client') as mock_mvp:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(mvp_response)
            mock_mvp.return_value = mock_client

            mvp_agent = RAPPMVPGeneratorAgent()
            mvp_result = mvp_agent.perform(
                action='generate_poke',
                customer_name=CAPITAL_MARKETS_CUSTOMER['customer_name'],
                project_name='Trade Reconciliation Agent',
                problem_statement=qg_data['validatedProblemStatement'],
                discovery_data=discovery_data.get('extracted_data', {})
            )

        mvp_data = json.loads(mvp_result)
        self.assertEqual(mvp_data['status'], 'success')
        self.assertIn('document', mvp_data)

    def test_call_center_discovery_to_mvp(self):
        """Test Call Center scenario from discovery through MVP generation."""
        from agents.rapp_discovery_agent import RAPPDiscoveryAgent
        from agents.rapp_quality_gate_agent import RAPPQualityGateAgent
        from agents.rapp_mvp_generator_agent import RAPPMVPGeneratorAgent

        # Step 1: Process transcript
        disc_response = json.dumps({
            "callMetadata": {"estimatedDuration": "52 minutes", "participants": []},
            "problemStatements": CALL_CENTER_DISCOVERY_DATA['problemStatements'],
            "dataSources": CALL_CENTER_DISCOVERY_DATA['dataSources'],
            "stakeholders": CALL_CENTER_DISCOVERY_DATA['stakeholders'],
            "successCriteria": CALL_CENTER_DISCOVERY_DATA['successCriteria'],
            "timeline": CALL_CENTER_DISCOVERY_DATA['timeline'],
            "suggestedAgents": ["CustomerContextAgent"]
        })

        with patch.object(RAPPDiscoveryAgent, '_get_openai_client') as mock_disc:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(disc_response)
            mock_disc.return_value = mock_client

            discovery_agent = RAPPDiscoveryAgent()
            discovery_result = discovery_agent.perform(
                action='process_transcript',
                customer_name=CALL_CENTER_CUSTOMER['customer_name'],
                transcript=CALL_CENTER_TRANSCRIPT
            )

        discovery_data = json.loads(discovery_result)
        self.assertEqual(discovery_data['status'], 'success')

        # Step 2: QG1 evaluation
        qg1_response = json.dumps({
            "gate": "QG1",
            "gateName": "Transcript Validation",
            "decision": "PASS",
            "overallScore": 8.4,
            "scores": {},
            "validatedProblemStatement": "12-minute AHT vs 6-minute benchmark",
            "nextStep": "Generate MVP"
        })

        with patch.object(RAPPQualityGateAgent, '_get_openai_client') as mock_qg:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(qg1_response)
            mock_qg.return_value = mock_client

            qg_agent = RAPPQualityGateAgent()
            qg_result = qg_agent.perform(
                action='evaluate',
                gate='QG1',
                customer_name=CALL_CENTER_CUSTOMER['customer_name'],
                context=discovery_data.get('extracted_data', {})
            )

        qg_data = json.loads(qg_result)
        self.assertEqual(qg_data['status'], 'success')
        self.assertEqual(qg_data['decision'], 'PASS')

        # Step 3: MVP generation
        mvp_response = json.dumps({
            "status": "success",
            "document": "# Customer Service Copilot MVP",
            "features": {"p0": ["Context"], "p1": ["Notes"], "p2": ["Sentiment"]},
            "estimatedDays": 30
        })

        with patch.object(RAPPMVPGeneratorAgent, '_get_openai_client') as mock_mvp:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = MockOpenAIResponse(mvp_response)
            mock_mvp.return_value = mock_client

            mvp_agent = RAPPMVPGeneratorAgent()
            mvp_result = mvp_agent.perform(
                action='generate_poke',
                customer_name=CALL_CENTER_CUSTOMER['customer_name'],
                project_name='Customer Service Copilot',
                problem_statement=qg_data['validatedProblemStatement'],
                discovery_data=discovery_data.get('extracted_data', {})
            )

        mvp_data = json.loads(mvp_result)
        self.assertEqual(mvp_data['status'], 'success')
        self.assertIn('document', mvp_data)


class TestProjectTrackerAgent(unittest.TestCase):
    """Test the Project Tracker Agent functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['AzureWebJobsStorage'] = 'UseDevelopmentStorage=true'

        from agents.project_tracker_agent import ProjectTrackerAgent
        cls.agent = ProjectTrackerAgent()

    def test_agent_initialization(self):
        """Test that the project tracker agent initializes correctly."""
        self.assertEqual(self.agent.name, 'ProjectTracker')

    def test_metadata_has_all_actions(self):
        """Test that all CRUD actions are defined."""
        actions = self.agent.metadata['parameters']['properties']['action']['enum']
        expected_actions = ['create', 'update', 'list', 'get', 'delete', 'export']

        for action in expected_actions:
            self.assertIn(action, actions)

    def test_missing_action_returns_error(self):
        """Test that missing action parameter returns error."""
        result = self.agent.perform(user_guid=TEST_USER_GUID)
        result_data = json.loads(result)

        self.assertEqual(result_data['status'], 'error')


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_scenario_tests():
    """Run tests for both scenarios with detailed output."""
    print("\n" + "="*70)
    print("RAPP PIPELINE AUTOMATED TESTS")
    print("="*70)

    print("\n" + "-"*70)
    print("SCENARIO 1: CAPITAL MARKETS - TRADE RECONCILIATION AGENT")
    print("-"*70)
    print(f"Customer: {CAPITAL_MARKETS_CUSTOMER['customer_name']}")
    print(f"Industry: {CAPITAL_MARKETS_CUSTOMER['industry']}")
    print(f"Transcript Length: {len(CAPITAL_MARKETS_TRANSCRIPT)} characters")
    print(f"Problem Statements: {len(CAPITAL_MARKETS_DISCOVERY_DATA['problemStatements'])}")
    print(f"Data Sources: {len(CAPITAL_MARKETS_DISCOVERY_DATA['dataSources'])}")
    print(f"Stakeholders: {len(CAPITAL_MARKETS_DISCOVERY_DATA['stakeholders'])}")

    print("\n" + "-"*70)
    print("SCENARIO 2: CALL CENTER - D365 CUSTOMER SERVICE AGENT")
    print("-"*70)
    print(f"Customer: {CALL_CENTER_CUSTOMER['customer_name']}")
    print(f"Industry: {CALL_CENTER_CUSTOMER['industry']}")
    print(f"Transcript Length: {len(CALL_CENTER_TRANSCRIPT)} characters")
    print(f"Problem Statements: {len(CALL_CENTER_DISCOVERY_DATA['problemStatements'])}")
    print(f"Data Sources: {len(CALL_CENTER_DISCOVERY_DATA['dataSources'])}")
    print(f"Stakeholders: {len(CALL_CENTER_DISCOVERY_DATA['stakeholders'])}")

    print("\n" + "="*70)
    print("RUNNING TESTS...")
    print("="*70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPDiscoveryAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPQualityGateAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPMVPGeneratorAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPCodeGeneratorAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPPipelineAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectTrackerAgent))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    return result


if __name__ == '__main__':
    run_scenario_tests()
