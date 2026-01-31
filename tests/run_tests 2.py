#!/usr/bin/env python3
"""
RAPP Pipeline Test Runner

Comprehensive test execution for both scenarios:
1. Capital Markets - Trade Reconciliation Agent
2. Call Center - D365 Customer Service Agent

Usage:
    # Run all tests (mocked)
    python tests/run_tests.py

    # Run with live API (requires environment variables)
    python tests/run_tests.py --live

    # Run specific scenario
    python tests/run_tests.py --scenario capital-markets
    python tests/run_tests.py --scenario call-center

    # Run with verbose output
    python tests/run_tests.py -v
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_fixtures import (
    CAPITAL_MARKETS_CUSTOMER,
    CAPITAL_MARKETS_TRANSCRIPT,
    CAPITAL_MARKETS_DISCOVERY_DATA,
    CALL_CENTER_CUSTOMER,
    CALL_CENTER_TRANSCRIPT,
    CALL_CENTER_DISCOVERY_DATA,
    TEST_USER_GUID
)


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")


def print_section(text):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{'-'*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.ENDC}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}[PASS]{Colors.ENDC} {text}")


def print_fail(text):
    """Print failure message."""
    print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} {text}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {text}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {text}")


def check_environment():
    """Check if environment variables are set for live testing."""
    required_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_DEPLOYMENT_NAME'
    ]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    return len(missing) == 0, missing


def run_live_scenario_test(scenario_name, customer, transcript, discovery_data, verbose=False):
    """Run a live test of a scenario using actual API calls."""
    print_section(f"LIVE TEST: {scenario_name}")

    results = {
        "scenario": scenario_name,
        "customer": customer['customer_name'],
        "timestamp": datetime.now().isoformat(),
        "steps": []
    }

    try:
        # Import agents
        from agents.rapp_discovery_agent import RAPPDiscoveryAgent
        from agents.rapp_quality_gate_agent import RAPPQualityGateAgent
        from agents.rapp_mvp_generator_agent import RAPPMVPGeneratorAgent
        from agents.rapp_code_generator_agent import RAPPCodeGeneratorAgent

        # Step 1: Discovery - Prepare Call
        print_info("Step 1a: Preparing discovery call...")
        discovery_agent = RAPPDiscoveryAgent()

        prep_result = discovery_agent.perform(
            action='prepare_call',
            customer_name=customer['customer_name'],
            industry=customer['industry']
        )
        prep_data = json.loads(prep_result)

        if prep_data['status'] == 'success':
            print_success("Discovery call preparation completed")
            if verbose:
                print(f"   Guide length: {len(prep_data.get('discovery_guide', ''))} chars")
        else:
            print_fail(f"Discovery prep failed: {prep_data.get('error')}")

        results['steps'].append({
            "name": "Discovery Prep",
            "status": prep_data['status'],
            "has_guide": 'discovery_guide' in prep_data
        })

        # Step 1b: Process Transcript
        print_info("Step 1b: Processing discovery transcript...")

        transcript_result = discovery_agent.perform(
            action='process_transcript',
            customer_name=customer['customer_name'],
            transcript=transcript
        )
        transcript_data = json.loads(transcript_result)

        if transcript_data['status'] == 'success':
            print_success("Transcript processing completed")
            extracted = transcript_data.get('extracted_data', {})
            if verbose:
                print(f"   Problem statements: {len(extracted.get('problemStatements', []))}")
                print(f"   Data sources: {len(extracted.get('dataSources', []))}")
                print(f"   Stakeholders: {len(extracted.get('stakeholders', []))}")
        else:
            print_fail(f"Transcript processing failed: {transcript_data.get('error')}")

        results['steps'].append({
            "name": "Transcript Processing",
            "status": transcript_data['status'],
            "extracted_data": bool(transcript_data.get('extracted_data'))
        })

        # Step 2: Quality Gate 1
        print_info("Step 2: Running Quality Gate 1 evaluation...")
        qg_agent = RAPPQualityGateAgent()

        qg1_result = qg_agent.perform(
            action='evaluate',
            gate='QG1',
            customer_name=customer['customer_name'],
            context=transcript_data.get('extracted_data', discovery_data)
        )
        qg1_data = json.loads(qg1_result)

        if qg1_data['status'] == 'success':
            evaluation = qg1_data.get('evaluation', {})
            decision = evaluation.get('decision', 'UNKNOWN')
            score = evaluation.get('overallScore', 0)

            if decision == 'PASS':
                print_success(f"QG1 PASSED - Score: {score}/10")
            elif decision == 'CLARIFY':
                print_warning(f"QG1 CLARIFY - Score: {score}/10")
            else:
                print_fail(f"QG1 FAILED - Score: {score}/10")

            if verbose:
                print(f"   Problem: {evaluation.get('validatedProblemStatement', 'N/A')[:80]}...")
        else:
            print_fail(f"QG1 evaluation failed: {qg1_data.get('error')}")

        results['steps'].append({
            "name": "Quality Gate 1",
            "status": qg1_data['status'],
            "decision": qg1_data.get('evaluation', {}).get('decision'),
            "score": qg1_data.get('evaluation', {}).get('overallScore')
        })

        # Step 3: MVP Generation
        print_info("Step 3: Generating MVP Poke document...")
        mvp_agent = RAPPMVPGeneratorAgent()

        mvp_result = mvp_agent.perform(
            action='generate_poke',
            customer_name=customer['customer_name'],
            project_name=f"{customer['customer_name']} AI Agent",
            problem_statement=qg1_data.get('evaluation', {}).get('validatedProblemStatement', ''),
            discovery_data=transcript_data.get('extracted_data', discovery_data)
        )
        mvp_data = json.loads(mvp_result)

        if mvp_data['status'] == 'success':
            print_success("MVP Poke document generated")
            if verbose:
                features = mvp_data.get('features', {})
                print(f"   P0 Features: {len(features.get('p0', []))}")
                print(f"   P1 Features: {len(features.get('p1', []))}")
                print(f"   P2 Features: {len(features.get('p2', []))}")
                print(f"   Estimated Days: {mvp_data.get('estimatedDays', 'N/A')}")
        else:
            print_fail(f"MVP generation failed: {mvp_data.get('error')}")

        results['steps'].append({
            "name": "MVP Generation",
            "status": mvp_data['status'],
            "has_document": bool(mvp_data.get('document')),
            "has_features": bool(mvp_data.get('features'))
        })

        # Step 5: Code Generation
        print_info("Step 5: Generating agent code...")
        code_agent = RAPPCodeGeneratorAgent()

        p0_features = mvp_data.get('features', {}).get('p0', ['Core functionality'])
        agent_name = "TradeReconciliationAgent" if "capital" in scenario_name.lower() else "CustomerServiceCopilotAgent"

        code_result = code_agent.perform(
            action='generate_agent',
            agent_name=agent_name,
            agent_description=f"AI agent for {customer['customer_name']}",
            features=p0_features,
            data_sources=discovery_data.get('dataSources', [])
        )
        code_data = json.loads(code_result)

        if code_data['status'] == 'success':
            print_success("Agent code generated")
            if verbose:
                code = code_data.get('code', '')
                print(f"   Code length: {len(code)} chars")
                print(f"   Has class definition: {'class ' in code}")
                print(f"   Has perform method: {'def perform' in code}")
        else:
            print_fail(f"Code generation failed: {code_data.get('error')}")

        results['steps'].append({
            "name": "Code Generation",
            "status": code_data['status'],
            "has_code": bool(code_data.get('code'))
        })

        # Calculate overall success
        passed_steps = sum(1 for s in results['steps'] if s['status'] == 'success')
        total_steps = len(results['steps'])
        results['success_rate'] = passed_steps / total_steps if total_steps > 0 else 0

        return results

    except Exception as e:
        print_fail(f"Exception during test: {str(e)}")
        results['error'] = str(e)
        results['success_rate'] = 0
        return results


def run_unit_tests(verbose=False):
    """Run all unit tests."""
    import unittest
    from tests.test_rapp_pipeline import (
        TestRAPPDiscoveryAgent,
        TestRAPPQualityGateAgent,
        TestRAPPMVPGeneratorAgent,
        TestRAPPCodeGeneratorAgent,
        TestRAPPPipelineAgent,
        TestEndToEndPipeline,
        TestProjectTrackerAgent
    )

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

    # Run with appropriate verbosity
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='RAPP Pipeline Test Runner')
    parser.add_argument('--live', action='store_true', help='Run live API tests')
    parser.add_argument('--scenario', choices=['capital-markets', 'call-center', 'both'],
                        default='both', help='Which scenario to test')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--unit-only', action='store_true', help='Only run unit tests')
    parser.add_argument('--save-results', type=str, help='Save results to JSON file')

    args = parser.parse_args()

    print_header("RAPP PIPELINE AUTOMATED TEST SUITE")
    print(f"\n{Colors.BLUE}Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

    all_results = {
        "run_time": datetime.now().isoformat(),
        "mode": "live" if args.live else "mocked",
        "scenarios_tested": [],
        "unit_tests": None
    }

    # Show scenario info
    print_section("TEST SCENARIOS")

    if args.scenario in ['capital-markets', 'both']:
        print(f"\n{Colors.BOLD}Scenario 1: Capital Markets{Colors.ENDC}")
        print(f"  Customer: {CAPITAL_MARKETS_CUSTOMER['customer_name']}")
        print(f"  Industry: {CAPITAL_MARKETS_CUSTOMER['industry']}")
        print(f"  Use Case: Trade Reconciliation Agent")
        print(f"  Transcript: {len(CAPITAL_MARKETS_TRANSCRIPT):,} characters")

    if args.scenario in ['call-center', 'both']:
        print(f"\n{Colors.BOLD}Scenario 2: Call Center{Colors.ENDC}")
        print(f"  Customer: {CALL_CENTER_CUSTOMER['customer_name']}")
        print(f"  Industry: {CALL_CENTER_CUSTOMER['industry']}")
        print(f"  Use Case: D365 Customer Service Copilot")
        print(f"  Transcript: {len(CALL_CENTER_TRANSCRIPT):,} characters")

    # Run unit tests first
    print_section("UNIT TESTS (Mocked)")
    unit_result = run_unit_tests(args.verbose)

    all_results['unit_tests'] = {
        "tests_run": unit_result.testsRun,
        "failures": len(unit_result.failures),
        "errors": len(unit_result.errors),
        "success_rate": (unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)) / unit_result.testsRun if unit_result.testsRun > 0 else 0
    }

    # Run live tests if requested
    if args.live and not args.unit_only:
        env_ok, missing = check_environment()

        if not env_ok:
            print_warning(f"Live tests skipped - Missing environment variables: {', '.join(missing)}")
            print_info("Set these in local.settings.json or export them:")
            for var in missing:
                print(f"  export {var}='your-value'")
        else:
            if args.scenario in ['capital-markets', 'both']:
                result = run_live_scenario_test(
                    "Capital Markets - Trade Reconciliation",
                    CAPITAL_MARKETS_CUSTOMER,
                    CAPITAL_MARKETS_TRANSCRIPT,
                    CAPITAL_MARKETS_DISCOVERY_DATA,
                    args.verbose
                )
                all_results['scenarios_tested'].append(result)

            if args.scenario in ['call-center', 'both']:
                result = run_live_scenario_test(
                    "Call Center - D365 Customer Service",
                    CALL_CENTER_CUSTOMER,
                    CALL_CENTER_TRANSCRIPT,
                    CALL_CENTER_DISCOVERY_DATA,
                    args.verbose
                )
                all_results['scenarios_tested'].append(result)

    # Print summary
    print_header("TEST SUMMARY")

    print(f"\n{Colors.BOLD}Unit Tests:{Colors.ENDC}")
    print(f"  Tests Run: {unit_result.testsRun}")
    print(f"  Failures: {len(unit_result.failures)}")
    print(f"  Errors: {len(unit_result.errors)}")
    success_rate = all_results['unit_tests']['success_rate'] * 100
    color = Colors.GREEN if success_rate >= 90 else Colors.WARNING if success_rate >= 70 else Colors.FAIL
    print(f"  Success Rate: {color}{success_rate:.1f}%{Colors.ENDC}")

    if all_results['scenarios_tested']:
        print(f"\n{Colors.BOLD}Live Scenario Tests:{Colors.ENDC}")
        for scenario in all_results['scenarios_tested']:
            rate = scenario.get('success_rate', 0) * 100
            color = Colors.GREEN if rate >= 80 else Colors.WARNING if rate >= 60 else Colors.FAIL
            print(f"  {scenario['scenario']}: {color}{rate:.0f}%{Colors.ENDC}")

    # Save results if requested
    if args.save_results:
        with open(args.save_results, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print_info(f"Results saved to: {args.save_results}")

    print(f"\n{Colors.BLUE}Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")

    # Return appropriate exit code
    if unit_result.failures or unit_result.errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
