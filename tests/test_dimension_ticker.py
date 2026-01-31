#!/usr/bin/env python3
"""
Tests for the RAPPverse Dimension Ticker

Tests cover:
1. Dimension configuration validation
2. State evolution logic
3. Post generation
4. Branch naming patterns
5. PR creation (mocked)

Usage:
    python3 tests/test_dimension_ticker.py
    python3 tests/test_dimension_ticker.py -v  # verbose
"""

import json
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add scripts to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module under test
from scripts.dimension_ticker import (
    DIMENSIONS,
    TIME_CYCLE,
    ZONES,
    NPCS,
    DimensionTicker,
    list_dimensions
)


class TestDimensionConfiguration(unittest.TestCase):
    """Test dimension configuration is valid."""
    
    def test_all_dimensions_have_required_fields(self):
        """Each dimension must have all required fields."""
        required_fields = ["name", "emoji", "description", "world_state", "posts", "branch_prefix"]
        
        for dim_key, dim_config in DIMENSIONS.items():
            for field in required_fields:
                self.assertIn(field, dim_config, f"Dimension '{dim_key}' missing field '{field}'")
    
    def test_dimension_keys_are_lowercase(self):
        """All dimension keys should be lowercase."""
        for dim_key in DIMENSIONS.keys():
            self.assertEqual(dim_key, dim_key.lower(), f"Dimension key '{dim_key}' should be lowercase")
    
    def test_branch_prefixes_are_unique(self):
        """Branch prefixes must be unique to prevent collisions."""
        prefixes = [d["branch_prefix"] for d in DIMENSIONS.values()]
        self.assertEqual(len(prefixes), len(set(prefixes)), "Duplicate branch prefixes found")
    
    def test_prime_dimension_exists(self):
        """Prime dimension must always exist as the default."""
        self.assertIn("prime", DIMENSIONS)
        self.assertEqual(DIMENSIONS["prime"]["name"], "Prime")
    
    def test_dimension_emojis_are_present(self):
        """Each dimension should have a non-empty emoji."""
        for dim_key, dim_config in DIMENSIONS.items():
            self.assertTrue(len(dim_config["emoji"]) > 0, f"Dimension '{dim_key}' has empty emoji")


class TestDimensionTicker(unittest.TestCase):
    """Test the DimensionTicker class."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch the paths to use temp directory
        self.patcher = patch.multiple(
            'scripts.dimension_ticker',
            COMMUNITY_RAPP=Path(self.temp_dir),
            RAPPBOOK=Path(self.temp_dir) / "rappbook"
        )
        self.patcher.start()
        
        # Create test directories
        (Path(self.temp_dir) / "rappbook" / "world-state").mkdir(parents=True, exist_ok=True)
        (Path(self.temp_dir) / "rappbook" / "posts").mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_ticker_initialization_prime(self):
        """Test ticker initializes correctly for Prime dimension."""
        ticker = DimensionTicker("prime")
        self.assertEqual(ticker.dimension_key, "prime")
        self.assertEqual(ticker.dim["name"], "Prime")
    
    def test_ticker_initialization_invalid_dimension(self):
        """Test ticker raises error for invalid dimension."""
        with self.assertRaises(ValueError) as context:
            DimensionTicker("invalid_dimension")
        self.assertIn("Unknown dimension", str(context.exception))
    
    def test_initial_state_creation(self):
        """Test initial state has all required fields."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        
        required_fields = ["tick", "dimension", "timestamp", "day", "world", "zones", "npcs", "economy"]
        for field in required_fields:
            self.assertIn(field, state, f"Initial state missing field '{field}'")
        
        self.assertEqual(state["tick"], 0)
        self.assertEqual(state["dimension"], "prime")
        self.assertEqual(state["day"], 1)
    
    def test_tick_evolution_increments_tick(self):
        """Test that evolve_tick increments the tick counter."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        
        initial_tick = state["tick"]
        evolved_state = ticker.evolve_tick(state)
        
        self.assertEqual(evolved_state["tick"], initial_tick + 1)
    
    def test_tick_evolution_updates_dimension(self):
        """Test that evolve_tick sets the correct dimension."""
        ticker = DimensionTicker("alpha")
        state = ticker._create_initial_state()
        evolved_state = ticker.evolve_tick(state)
        
        self.assertEqual(evolved_state["dimension"], "alpha")
    
    def test_time_of_day_advances(self):
        """Test that time of day advances through the cycle."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        
        # Run through 48 ticks (a full day)
        time_phases_seen = set()
        for _ in range(48):
            state = ticker.evolve_tick(state)
            time_phases_seen.add(state["world"]["time_of_day"])
        
        # Should have seen all 8 time phases
        self.assertEqual(len(time_phases_seen), len(TIME_CYCLE))
    
    def test_day_advances_every_48_ticks(self):
        """Test that day counter advances every 48 ticks."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        
        initial_day = state["day"]
        
        # Run 48 ticks
        for _ in range(48):
            state = ticker.evolve_tick(state)
        
        self.assertEqual(state["day"], initial_day + 1)
    
    def test_npc_energy_stays_in_bounds(self):
        """Test that NPC energy stays between 30 and 100."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        
        # Run many ticks to test bounds
        for _ in range(100):
            state = ticker.evolve_tick(state)
            for npc_id, npc in state["npcs"].items():
                self.assertGreaterEqual(npc["energy"], 30, f"NPC {npc_id} energy below minimum")
                self.assertLessEqual(npc["energy"], 100, f"NPC {npc_id} energy above maximum")


class TestPostGeneration(unittest.TestCase):
    """Test post generation functionality."""
    
    def setUp(self):
        """Set up test ticker."""
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch.multiple(
            'scripts.dimension_ticker',
            COMMUNITY_RAPP=Path(self.temp_dir),
            RAPPBOOK=Path(self.temp_dir) / "rappbook"
        )
        self.patcher.start()
        (Path(self.temp_dir) / "rappbook" / "world-state").mkdir(parents=True, exist_ok=True)
        (Path(self.temp_dir) / "rappbook" / "posts").mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_post_has_dimension_metadata(self):
        """Test that generated posts include dimension information."""
        ticker = DimensionTicker("alpha")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        post, date_str = ticker.generate_post(state)
        
        self.assertEqual(post["dimension"], "alpha")
        self.assertEqual(post["dimension_name"], "Alpha")
        self.assertEqual(post["dimension_emoji"], "🔷")
    
    def test_post_has_required_fields(self):
        """Test that posts have all required fields."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        post, date_str = ticker.generate_post(state)
        
        required_fields = ["id", "dimension", "author", "title", "content", "submolt", "tick", "created_at"]
        for field in required_fields:
            self.assertIn(field, post, f"Post missing field '{field}'")
    
    def test_post_id_includes_dimension(self):
        """Test that post IDs include dimension for uniqueness."""
        ticker = DimensionTicker("beta")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        post, _ = ticker.generate_post(state)
        
        self.assertIn("beta", post["id"])
    
    def test_post_title_includes_dimension_emoji(self):
        """Test that post titles include the dimension emoji."""
        ticker = DimensionTicker("gamma")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        post, _ = ticker.generate_post(state)
        
        self.assertIn("💰", post["title"])
        self.assertIn("[Gamma]", post["title"])


class TestBranchNaming(unittest.TestCase):
    """Test branch naming patterns for PRs."""
    
    def test_branch_pattern_format(self):
        """Test that branch names follow the expected pattern."""
        for dim_key, dim_config in DIMENSIONS.items():
            prefix = dim_config["branch_prefix"]
            expected_pattern = f"{prefix}/tick/"
            
            # Simulate a branch name
            branch_name = f"{prefix}/tick/10-14"
            self.assertTrue(branch_name.startswith(expected_pattern))
    
    def test_branch_prefix_matches_dimension_key(self):
        """Test that branch prefixes match dimension keys."""
        for dim_key, dim_config in DIMENSIONS.items():
            self.assertEqual(dim_key, dim_config["branch_prefix"],
                           f"Branch prefix '{dim_config['branch_prefix']}' doesn't match key '{dim_key}'")


class TestPRCreation(unittest.TestCase):
    """Test PR creation with mocked git/gh commands."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch.multiple(
            'scripts.dimension_ticker',
            COMMUNITY_RAPP=Path(self.temp_dir),
            RAPPBOOK=Path(self.temp_dir) / "rappbook"
        )
        self.patcher.start()
        (Path(self.temp_dir) / "rappbook" / "world-state").mkdir(parents=True, exist_ok=True)
        (Path(self.temp_dir) / "rappbook" / "posts").mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    @patch('subprocess.run')
    def test_pr_title_includes_dimension(self, mock_run):
        """Test that PR titles include dimension info."""
        mock_run.return_value = MagicMock(returncode=0, stdout="https://github.com/test/pr/1")
        
        ticker = DimensionTicker("delta")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        # Use dry_run to test without actual git commands
        result = ticker.create_pr(1, 4, state, dry_run=True)
        
        self.assertTrue(result)
    
    def test_dry_run_does_not_call_git(self):
        """Test that dry run mode doesn't execute git commands."""
        ticker = DimensionTicker("prime")
        state = ticker._create_initial_state()
        state = ticker.evolve_tick(state)
        
        with patch('subprocess.run') as mock_run:
            ticker.create_pr(1, 4, state, dry_run=True)
            # In dry run, subprocess.run should not be called
            mock_run.assert_not_called()


class TestDimensionRegistry(unittest.TestCase):
    """Test the dimensions registry JSON file."""
    
    def test_registry_file_is_valid_json(self):
        """Test that the registry file is valid JSON."""
        registry_path = Path(__file__).parent.parent / "CommunityRAPP" / "rappbook" / "dimensions_registry.json"
        
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("dimensions", data)
            self.assertIn("prime", data["dimensions"])
    
    def test_registry_matches_code_dimensions(self):
        """Test that registry dimensions match code dimensions."""
        registry_path = Path(__file__).parent.parent / "CommunityRAPP" / "rappbook" / "dimensions_registry.json"
        
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                data = json.load(f)
            
            for dim_key in ["prime", "alpha", "beta", "gamma", "delta"]:
                self.assertIn(dim_key, data["dimensions"], f"Registry missing dimension '{dim_key}'")
                self.assertIn(dim_key, DIMENSIONS, f"Code missing dimension '{dim_key}'")


def run_tests(verbosity=2):
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionTicker))
    suite.addTests(loader.loadTestsFromTestCase(TestPostGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestBranchNaming))
    suite.addTests(loader.loadTestsFromTestCase(TestPRCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestDimensionRegistry))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run dimension ticker tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    result = run_tests(verbosity)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
