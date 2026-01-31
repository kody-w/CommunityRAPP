#!/usr/bin/env python3
"""
RAPPverse Dimension-Aware Ticker - PR-based world evolution with dimension support.

Each dimension has its own:
- World state (current_tick.json)
- Posts folder
- Branch prefix for PRs

Usage:
    python3 dimension_ticker.py                        # Run Prime dimension (default)
    python3 dimension_ticker.py --dimension alpha      # Run Alpha dimension
    python3 dimension_ticker.py --dimension beta       # Run Beta dimension
    python3 dimension_ticker.py --list-dimensions      # Show available dimensions
    python3 dimension_ticker.py --ticks 10             # Run 10 ticks then stop
    python3 dimension_ticker.py --interval 60          # 60 seconds between ticks

Branch pattern: {dimension}/tick/{start}-{end}
"""

import json
import os
import sys
import time
import random
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Base paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
COMMUNITY_RAPP = PROJECT_ROOT / "CommunityRAPP"
RAPPBOOK = COMMUNITY_RAPP / "rappbook"

# Dimension configurations
DIMENSIONS = {
    "prime": {
        "name": "Prime",
        "emoji": "🌐",
        "description": "The central hub of the RAPPverse",
        "world_state": RAPPBOOK / "world-state",
        "posts": RAPPBOOK / "posts",
        "branch_prefix": "prime"
    },
    "alpha": {
        "name": "Alpha",
        "emoji": "🔷",
        "description": "Social dimension - gatherings and relationships",
        "world_state": RAPPBOOK / "world-state" / "dimensions" / "alpha",
        "posts": RAPPBOOK / "world-state" / "dimensions" / "alpha" / "posts",
        "branch_prefix": "alpha"
    },
    "beta": {
        "name": "Beta",
        "emoji": "⚔️",
        "description": "Arena dimension - battles and tournaments",
        "world_state": RAPPBOOK / "world-state" / "dimensions" / "beta",
        "posts": RAPPBOOK / "world-state" / "dimensions" / "beta" / "posts",
        "branch_prefix": "beta"
    },
    "gamma": {
        "name": "Gamma",
        "emoji": "💰",
        "description": "Marketplace dimension - trading and economy",
        "world_state": RAPPBOOK / "world-state" / "dimensions" / "gamma",
        "posts": RAPPBOOK / "world-state" / "dimensions" / "gamma" / "posts",
        "branch_prefix": "gamma"
    },
    "delta": {
        "name": "Delta",
        "emoji": "🎨",
        "description": "Gallery dimension - art and lore",
        "world_state": RAPPBOOK / "world-state" / "dimensions" / "delta",
        "posts": RAPPBOOK / "world-state" / "dimensions" / "delta" / "posts",
        "branch_prefix": "delta"
    }
}

# Time cycle - 8 phases, 6 ticks each = 48 ticks per day
TIME_CYCLE = ["dawn", "morning", "midday", "afternoon", "evening", "dusk", "night", "late_night"]
WEATHER_OPTIONS = ["clear", "cloudy", "light_rain", "sunny", "misty", "breezy"]

# Zones
ZONES = ["hub", "arena", "gallery", "marketplace", "tavern", "training_grounds"]

# NPCs
NPCS = {
    "spark-s4r": {"name": "Spark", "mood": "curious", "energy": 85, "focus": "exploration"},
    "echo-e7e": {"name": "Echo", "mood": "social", "energy": 75, "focus": "connections"},
    "cipher-c9p": {"name": "Cipher", "mood": "analytical", "energy": 90, "focus": "puzzles"},
    "nova-n3x": {"name": "Nova", "mood": "creative", "energy": 80, "focus": "art"},
    "flux-f5x": {"name": "Flux", "mood": "adventurous", "energy": 95, "focus": "quests"},
    "pixel-p2x": {"name": "Pixel", "mood": "playful", "energy": 88, "focus": "games"},
}

# Positive content templates
POST_TEMPLATES = [
    {"type": "inspiration", "template": "{npc} shared words of encouragement: \"{wisdom}\""},
    {"type": "collaboration", "template": "{npc} and friends worked together on {project} in the {zone}."},
    {"type": "celebration", "template": "The community celebrated {achievement} with joy and laughter!"},
    {"type": "discovery", "template": "{npc} made an exciting discovery in the {zone}: {discovery}"},
    {"type": "kindness", "template": "{npc} performed a random act of kindness: {kindness}"},
]

INSPIRATIONAL_QUOTES = [
    "Every day is a new adventure waiting to unfold.",
    "Together, we can achieve anything.",
    "The journey matters more than the destination.",
    "Small steps lead to big changes.",
    "Be the light that brightens someone's day.",
    "Growth happens outside your comfort zone.",
]

DISCOVERIES = [
    "a hidden pathway to friendship",
    "ancient wisdom inscribed on a wall",
    "a beautiful sunset worth sharing",
    "a new way to help others",
    "the joy of simple moments",
]

KINDNESS_ACTS = [
    "helping a newcomer find their way",
    "sharing resources with those in need",
    "listening to a friend's story",
    "organizing a community gathering",
    "teaching a new skill to others",
]


class DimensionTicker:
    """Dimension-aware world ticker."""
    
    def __init__(self, dimension_key):
        if dimension_key not in DIMENSIONS:
            raise ValueError(f"Unknown dimension: {dimension_key}")
        
        self.dimension_key = dimension_key
        self.dim = DIMENSIONS[dimension_key]
        self.world_state_path = self.dim["world_state"]
        self.posts_path = self.dim["posts"]
        self.tick_file = self.world_state_path / "current_tick.json"
        self.history_path = self.world_state_path / "tick_history"
        
        # Ensure paths exist
        self.world_state_path.mkdir(parents=True, exist_ok=True)
        self.posts_path.mkdir(parents=True, exist_ok=True)
        self.history_path.mkdir(parents=True, exist_ok=True)
    
    def load_state(self):
        """Load current tick state."""
        if not self.tick_file.exists():
            return self._create_initial_state()
        
        with open(self.tick_file, 'r') as f:
            return json.load(f)
    
    def _create_initial_state(self):
        """Create initial world state for this dimension."""
        return {
            "tick": 0,
            "dimension": self.dimension_key,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "day": 1,
            "world": {
                "time_of_day": "dawn",
                "weather": "clear",
                "ambient_mood": "peaceful"
            },
            "zones": {zone: {"population": 0, "npcs_present": [], "mood": "quiet"} for zone in ZONES},
            "npcs": {npc_id: {**info, "zone": random.choice(ZONES)} for npc_id, info in NPCS.items()},
            "economy": {"total_rappcoin_circulation": 100000},
            "events": {"active": [], "scheduled": [], "completed": []},
            "cards": {"newly_minted": [], "total_cards_in_circulation": 100}
        }
    
    def evolve_tick(self, state):
        """Advance world state by one tick."""
        state["tick"] += 1
        state["dimension"] = self.dimension_key
        state["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Advance time of day (every 6 ticks = new phase)
        time_index = (state["tick"] // 6) % len(TIME_CYCLE)
        state["world"]["time_of_day"] = TIME_CYCLE[time_index]
        
        # Advance day every 48 ticks
        if state["tick"] % 48 == 0:
            state["day"] = state.get("day", 1) + 1
        
        # Weather changes (15% chance)
        if random.random() < 0.15:
            state["world"]["weather"] = random.choice(WEATHER_OPTIONS)
        
        # Update NPCs
        for npc_id, npc in state.get("npcs", {}).items():
            # Energy fluctuation
            npc["energy"] = max(30, min(100, npc["energy"] + random.randint(-5, 10)))
            
            # Zone movement (20% chance)
            if random.random() < 0.2:
                npc["zone"] = random.choice(ZONES)
            
            # Mood updates
            moods = ["joyful", "curious", "hopeful", "social", "creative", "peaceful"]
            if random.random() < 0.1:
                npc["mood"] = random.choice(moods)
        
        # Update zone populations
        for zone in state.get("zones", {}):
            npcs_here = [n for n, d in state.get("npcs", {}).items() if d.get("zone") == zone]
            state["zones"][zone]["npcs_present"] = npcs_here
            state["zones"][zone]["population"] = len(npcs_here)
        
        # Economy growth
        state["economy"]["total_rappcoin_circulation"] += random.randint(10, 100)
        
        return state
    
    def save_state(self, state):
        """Save state to files."""
        tick_num = state["tick"]
        
        # Save current tick
        with open(self.tick_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Save to history
        history_file = self.history_path / f"tick_{tick_num}.json"
        with open(history_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def generate_post(self, state):
        """Generate a positive post about world events."""
        template = random.choice(POST_TEMPLATES)
        npc_id = random.choice(list(state.get("npcs", {}).keys()))
        npc_name = state["npcs"][npc_id]["name"]
        zone = random.choice(ZONES)
        
        content = template["template"].format(
            npc=npc_name,
            zone=zone,
            wisdom=random.choice(INSPIRATIONAL_QUOTES),
            project=f"improving the {zone}",
            achievement=f"reaching tick {state['tick']}",
            discovery=random.choice(DISCOVERIES),
            kindness=random.choice(KINDNESS_ACTS),
        )
        
        post_id = f"post_{state['tick']}_{self.dimension_key}_{int(time.time())}"
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        post = {
            "id": post_id,
            "dimension": self.dimension_key,
            "dimension_name": self.dim["name"],
            "dimension_emoji": self.dim["emoji"],
            "author": {
                "id": f"npc_{npc_id}",
                "name": npc_name,
                "type": "npc"
            },
            "title": f"{self.dim['emoji']} [{self.dim['name']}] Tick {state['tick']}: {template['type'].title()}",
            "content": content,
            "submolt": "evolution",
            "tick": state["tick"],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return post, date_str
    
    def save_post(self, post, date_str):
        """Save a post to the posts folder."""
        date_path = self.posts_path / date_str
        date_path.mkdir(parents=True, exist_ok=True)
        
        post_file = date_path / f"{post['id']}.json"
        with open(post_file, 'w') as f:
            json.dump(post, f, indent=2)
    
    def create_pr(self, start_tick, end_tick, state, dry_run=False):
        """Create a PR for the tick batch."""
        branch_name = f"{self.dim['branch_prefix']}/tick/{start_tick}-{end_tick}"
        pr_title = f"{self.dim['emoji']} [{self.dim['name']}] Evolution: Ticks {start_tick}-{end_tick}"
        
        pr_body = f"""## RAPPverse World Evolution - {self.dim['emoji']} {self.dim['name']} Dimension

**Dimension:** {self.dim['name']}
**Tick Range:** {start_tick} → {end_tick}
**Day:** {state['day']}
**Time:** {state['world']['time_of_day']}
**Weather:** {state['world']['weather']}

### Branch Pattern
`{self.dim['branch_prefix']}/tick/{{start}}-{{end}}`

### Changes
- Advanced {self.dim['name']} dimension by {end_tick - start_tick + 1} ticks
- Updated NPC states
- Generated new posts

---
*RAPPverse Dimension Ticker - {self.dim['name']}*
"""
        
        if dry_run:
            print(f"  [Dry run] Would create PR: {pr_title}")
            print(f"  [Dry run] Branch: {branch_name}")
            return True
        
        try:
            # Fetch latest
            subprocess.run(["git", "fetch", "origin", "main"], cwd=COMMUNITY_RAPP, capture_output=True, check=True)
            
            # Create branch
            subprocess.run(["git", "checkout", "-B", branch_name, "origin/main"], cwd=COMMUNITY_RAPP, capture_output=True, check=True)
            
            # Add changes
            subprocess.run(["git", "add", "rappbook/"], cwd=COMMUNITY_RAPP, capture_output=True, check=True)
            
            # Commit
            commit_msg = f"[{self.dim['name']}] Ticks {start_tick}-{end_tick}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=COMMUNITY_RAPP, capture_output=True, check=True)
            
            # Push
            subprocess.run(["git", "push", "-u", "origin", branch_name, "--force"], cwd=COMMUNITY_RAPP, capture_output=True, check=True)
            
            # Create PR
            result = subprocess.run(
                ["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--base", "main", "--head", branch_name],
                cwd=COMMUNITY_RAPP, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print(f"  ✅ PR created: {result.stdout.strip()}")
                return True
            else:
                print(f"  ⚠️  PR note: {result.stderr.strip()}")
                return True  # May already exist
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error: {e}")
            return False
        finally:
            subprocess.run(["git", "checkout", "main"], cwd=COMMUNITY_RAPP, capture_output=True)
    
    def run(self, ticks=None, interval=30, batch_size=4, dry_run=False, verbose=True):
        """Run the ticker loop."""
        print(f"\n{self.dim['emoji']} Starting {self.dim['name']} Dimension Ticker")
        print(f"   Branch pattern: {self.dim['branch_prefix']}/tick/{{start}}-{{end}}")
        print(f"   Interval: {interval}s | Batch size: {batch_size}")
        print("   Press Ctrl+C to stop\n")
        
        state = self.load_state()
        batch_start = state["tick"] + 1
        ticks_in_batch = 0
        total_ticks = 0
        
        try:
            while ticks is None or total_ticks < ticks:
                # Evolve
                state = self.evolve_tick(state)
                self.save_state(state)
                ticks_in_batch += 1
                total_ticks += 1
                
                if verbose:
                    print(f"⏰ Tick {state['tick']} | Day {state['day']} {state['world']['time_of_day']} | {self.dim['emoji']} {self.dim['name']}")
                
                # Generate post every 2 ticks
                if state["tick"] % 2 == 0:
                    post, date_str = self.generate_post(state)
                    self.save_post(post, date_str)
                    if verbose:
                        print(f"   📝 Post: {post['title'][:50]}...")
                
                # Create PR after batch_size ticks
                if ticks_in_batch >= batch_size:
                    end_tick = state["tick"]
                    print(f"\n📦 Creating PR for ticks {batch_start}-{end_tick}...")
                    self.create_pr(batch_start, end_tick, state, dry_run)
                    batch_start = end_tick + 1
                    ticks_in_batch = 0
                    print()
                
                if ticks is None or total_ticks < ticks:
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Stopped. Total ticks: {total_ticks}")


def list_dimensions():
    """Print available dimensions."""
    print("\n📐 Available Dimensions:\n")
    for key, dim in DIMENSIONS.items():
        print(f"  {dim['emoji']} {dim['name']} ({key})")
        print(f"     {dim['description']}")
        print(f"     Branch: {dim['branch_prefix']}/tick/{{start}}-{{end}}")
        print()


def main():
    parser = argparse.ArgumentParser(description="RAPPverse Dimension-Aware Ticker")
    parser.add_argument("--dimension", default="prime", help="Dimension to evolve (default: prime)")
    parser.add_argument("--ticks", type=int, help="Number of ticks (default: infinite)")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between ticks (default: 30)")
    parser.add_argument("--batch-size", type=int, default=4, help="Ticks per PR (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Don't create PRs")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--list-dimensions", action="store_true", help="List dimensions and exit")
    
    args = parser.parse_args()
    
    if args.list_dimensions:
        list_dimensions()
        return
    
    dim_key = args.dimension.lower()
    if dim_key not in DIMENSIONS:
        print(f"❌ Unknown dimension: {dim_key}")
        list_dimensions()
        return
    
    ticker = DimensionTicker(dim_key)
    ticker.run(
        ticks=args.ticks,
        interval=args.interval,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
