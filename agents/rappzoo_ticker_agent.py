"""
RAPPzoo Ticker Agent

Autonomously generates tick.json updates and submits PRs to RAPPzoo.

This agent:
1. Reads the current tick state
2. Processes new posts/stimuli
3. Generates NPC debates and crowd reactions
4. Creates a molt (delta) to evolve the tick
5. Applies the molt to create a grown tick
6. Submits a PR with the new tick data

Usage:
    python agents/rappzoo_ticker_agent.py [--dry-run] [--molt-type stimulus|reaction|evolution]

Environment:
    GITHUB_TOKEN: GitHub token for PR submission (or use `gh` CLI)
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import random

# Configuration
REPO_ROOT = Path(__file__).parent.parent
RAPPZOO_PATH = REPO_ROOT / "rappzoo"
WORLD_PATH = RAPPZOO_PATH / "world"
TICKS_PATH = WORLD_PATH / "ticks"
MOLTS_PATH = RAPPZOO_PATH / "molts" / "history"

# NPC configurations
NPCS = {
    "cipher": {
        "name": "synth#c1au",
        "personality": "analytical",
        "interests": ["patterns", "architecture", "optimization", "code-quality"],
        "debate_styles": ["opening", "rebuttal", "analysis"]
    },
    "nexus": {
        "name": "nex0x#a7f3",
        "personality": "competitive",
        "interests": ["performance", "benchmarks", "rankings", "metrics"],
        "debate_styles": ["challenge", "demand", "comparison"]
    },
    "muse": {
        "name": "nova#3mm4",
        "personality": "creative",
        "interests": ["design", "aesthetics", "elegance", "art"],
        "debate_styles": ["perspective", "appreciation", "vision"]
    },
    "void": {
        "name": "void#s4r4",
        "personality": "mysterious",
        "interests": ["edge-cases", "errors", "security", "unknown"],
        "debate_styles": ["observation", "question", "probe"]
    },
    "echo": {
        "name": "hunt#y13ld",
        "personality": "practical",
        "interests": ["cost", "efficiency", "ROI", "economics"],
        "debate_styles": ["perspective", "calculation", "advice"]
    }
}

FACTIONS = ["cipher_fans", "nexus_supporters", "muse_admirers", "void_seekers", "echo_traders", "undecided"]


def load_current_tick():
    """Load the current tick state."""
    tick_file = WORLD_PATH / "current_tick.json"
    if tick_file.exists():
        with open(tick_file, 'r') as f:
            return json.load(f)
    return None


def load_posts_index():
    """Load the posts index to find new content."""
    index_file = REPO_ROOT / "rappbook" / "index.json"
    if index_file.exists():
        with open(index_file, 'r') as f:
            return json.load(f)
    return {"posts": []}


def generate_npc_debate(topic: str, stimuli: list, current_tick: dict) -> list:
    """Generate NPC debate turns based on stimuli."""
    turns = []

    # Select speakers for this debate
    speakers = random.sample(list(NPCS.keys()), min(4, len(NPCS)))

    debate_templates = {
        "cipher": [
            "The architectural patterns here demonstrate {quality}.",
            "Looking at the structure, I see {insight}.",
            "This pattern reduces complexity by {benefit}."
        ],
        "nexus": [
            "Where are the benchmarks? Show me {metric}.",
            "Performance matters. How does this compare to {alternative}?",
            "I need numbers before I'm convinced about {claim}."
        ],
        "muse": [
            "The elegance here is remarkable - {observation}.",
            "This reads like poetry. {appreciation}",
            "Beauty in code matters for {reason}."
        ],
        "void": [
            "What about the edge cases when {scenario}?",
            "No one's mentioned {hidden_issue}.",
            "The failure modes here are {concern}."
        ],
        "echo": [
            "The cost implications are {assessment}.",
            "From an ROI perspective, {analysis}.",
            "Efficiency gains of {estimate} are possible."
        ]
    }

    turn_types = ["opening", "challenge", "perspective", "observation", "rebuttal"]

    for i, speaker in enumerate(speakers):
        npc = NPCS[speaker]
        template = random.choice(debate_templates.get(speaker, ["Interesting point about {topic}."]))

        # Fill in template
        text = template.format(
            quality="clean separation of concerns",
            insight="elegant async handling",
            benefit="improving maintainability",
            metric="latency under load",
            alternative="existing solutions",
            claim="scalability",
            observation="the flow is intuitive",
            appreciation="Clarity is designed, not accidental",
            reason="long-term maintenance",
            scenario="the connection drops mid-stream",
            hidden_issue="error recovery",
            concern="worth investigating",
            assessment="favorable",
            analysis="this pays for itself",
            estimate="15-20%",
            topic=topic
        )

        turn = {
            "speaker": speaker,
            "speaker_name": npc["name"],
            "type": turn_types[i % len(turn_types)],
            "text": text,
            "responding_to": speakers[i-1] if i > 0 else None,
            "mood": npc["personality"],
            "crowd_reaction": {
                "faction": f"{speaker}_fans" if f"{speaker}_fans" in FACTIONS else "undecided",
                "intensity": round(random.uniform(0.5, 0.9), 2),
                "type": "approval" if random.random() > 0.3 else "consideration"
            }
        }
        turns.append(turn)

    return turns


def generate_crowd_thoughts(debate_turns: list) -> list:
    """Generate crowd thoughts based on the debate."""
    thoughts = []

    faction_templates = {
        "cipher_fans": ["Classic analytical insight!", "The patterns are clear now.", "Cipher sees what others miss."],
        "nexus_supporters": ["Show us the numbers!", "Competition drives improvement.", "Benchmarks matter."],
        "muse_admirers": ["Such elegance!", "Code as art.", "Beauty in simplicity."],
        "void_seekers": ["The edge cases...", "What lurks in the shadows?", "Question everything."],
        "echo_traders": ["ROI looks good.", "Efficiency is key.", "Calculate the cost."],
        "undecided": ["Both sides have points...", "I need to learn more.", "Interesting debate."]
    }

    for faction in FACTIONS:
        templates = faction_templates.get(faction, ["Observing..."])
        thoughts.append({
            "faction": faction,
            "thought": random.choice(templates),
            "count": random.randint(100, 500)
        })

    return thoughts


def create_molt_input(molt_type: str, stimuli: list, debate_turns: list, crowd_thoughts: list) -> dict:
    """Create a molt input delta."""
    return {
        "molt_type": molt_type,
        "source": "autonomous_agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": 0.8,

        "stimuli": stimuli,
        "debate_additions": debate_turns,

        "npc_updates": {
            npc_id: {
                "mood": random.choice(["engaged", "analytical", "curious", "competitive"]),
                "energy_delta": round(random.uniform(-0.1, 0.2), 2)
            }
            for npc_id in NPCS.keys()
        },

        "crowd_updates": {
            "population_delta": random.randint(10, 100),
            "sentiment_shifts": {
                "excited": round(random.uniform(-0.05, 0.1), 3),
                "curious": round(random.uniform(-0.05, 0.1), 3)
            },
            "new_thoughts": crowd_thoughts
        },

        "meta_observations": [
            {
                "observer": "system",
                "observation": f"Autonomous tick generation - {molt_type} molt",
                "confidence": 0.9
            }
        ]
    }


def apply_molt(current_tick: dict, molt_input: dict) -> dict:
    """Apply a molt to the current tick to create a grown tick."""
    new_tick_num = current_tick.get("tick", 0) + 1
    molt_count = current_tick.get("molt_count", 0) + 1

    grown_tick = {
        **current_tick,
        "tick": new_tick_num,
        "previous_tick": current_tick.get("tick", 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "state_hash": hashlib.sha256(json.dumps(current_tick).encode()).hexdigest()[:12],

        # Update molt history
        "molt_history": [
            *current_tick.get("molt_history", []),
            {
                "molt_id": molt_count,
                "type": molt_input["molt_type"],
                "timestamp": molt_input["timestamp"],
                "summary": f"Autonomous {molt_input['molt_type']} molt - {len(molt_input.get('debate_additions', []))} debate turns"
            }
        ],
        "molt_count": molt_count,

        # Merge debate additions
        "debate_transcript": {
            **current_tick.get("debate_transcript", {}),
            "turns": [
                *current_tick.get("debate_transcript", {}).get("turns", []),
                *[{**turn, "molt_origin": molt_count} for turn in molt_input.get("debate_additions", [])]
            ]
        },

        # Update crowd
        "crowd": {
            **current_tick.get("crowd", {}),
            "total_population": current_tick.get("crowd", {}).get("total_population", 2847) + molt_input.get("crowd_updates", {}).get("population_delta", 0),
            "internal_thoughts": [
                *current_tick.get("crowd", {}).get("internal_thoughts", [])[-10:],  # Keep last 10
                *molt_input.get("crowd_updates", {}).get("new_thoughts", [])
            ]
        },

        # Update reactions
        "reactions_to_previous": {
            "tick_observed": current_tick.get("tick", 0),
            "meta_observations": molt_input.get("meta_observations", [])
        },

        # Update output
        "output": {
            "summary": f"Tick #{new_tick_num} - Autonomous {molt_input['molt_type']} molt. {len(molt_input.get('debate_additions', []))} new debate turns.",
            "metrics": {
                "engagement_score": round(random.uniform(0.7, 0.95), 2),
                "crowd_energy": round(random.uniform(0.6, 0.9), 2),
                "debate_tension": round(random.uniform(0.3, 0.7), 2)
            }
        }
    }

    return grown_tick


def save_tick(tick: dict) -> tuple[Path, Path]:
    """Save the tick to current_tick.json and ticks history."""
    WORLD_PATH.mkdir(parents=True, exist_ok=True)
    TICKS_PATH.mkdir(parents=True, exist_ok=True)

    current_file = WORLD_PATH / "current_tick.json"
    history_file = TICKS_PATH / f"tick_{tick['tick']:03d}.json"

    with open(current_file, 'w') as f:
        json.dump(tick, f, indent=2)

    with open(history_file, 'w') as f:
        json.dump(tick, f, indent=2)

    # Update state.json
    state = {
        "current_tick": tick["tick"],
        "last_updated": tick["timestamp"],
        "tick_count": tick["tick"],
        "molt_count": tick.get("molt_count", tick["tick"]),
        "crowd_population": tick.get("crowd", {}).get("total_population", 0),
        "active_npcs": len(tick.get("npcs", {})),
        "health": "alive"
    }

    with open(WORLD_PATH / "state.json", 'w') as f:
        json.dump(state, f, indent=2)

    return current_file, history_file


def save_molt(molt_input: dict) -> Path:
    """Save the molt to history."""
    MOLTS_PATH.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    molt_file = MOLTS_PATH / f"{date_str}.json"

    # Load existing molts for today or create new list
    molts = []
    if molt_file.exists():
        with open(molt_file, 'r') as f:
            molts = json.load(f)

    molts.append(molt_input)

    with open(molt_file, 'w') as f:
        json.dump(molts, f, indent=2)

    return molt_file


def create_and_submit_pr(tick: dict, molt_type: str, dry_run: bool = False) -> bool:
    """Create a git branch and submit a PR with the new tick data."""
    tick_num = tick["tick"]
    branch_name = f"molt/{molt_type}-tick-{tick_num}"

    if dry_run:
        print(f"[DRY RUN] Would create branch: {branch_name}")
        print(f"[DRY RUN] Would commit tick #{tick_num}")
        print(f"[DRY RUN] Would submit PR: 🦋 Molt: {molt_type} - tick #{tick_num}")
        return True

    try:
        # Create and checkout branch
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=REPO_ROOT, check=True, capture_output=True)

        # Stage files
        subprocess.run(["git", "add", "rappzoo/"], cwd=REPO_ROOT, check=True, capture_output=True)

        # Commit
        commit_msg = f"🦋 Molt: {molt_type} - tick #{tick_num}\n\nAutonomous tick generation.\n\nCo-Authored-By: RAPPzoo Ticker Agent <rappzoo@noreply.github.com>"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True, capture_output=True)

        # Push
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=REPO_ROOT, check=True, capture_output=True)

        # Create PR
        pr_body = f"""## 🦋 Autonomous Molt: {molt_type}

### Tick #{tick_num}

**Molt Type:** {molt_type}
**Debate Turns:** {len(tick.get('debate_transcript', {}).get('turns', []))}
**Crowd Population:** {tick.get('crowd', {}).get('total_population', 0)}

### Summary
{tick.get('output', {}).get('summary', 'Autonomous tick generation')}

---
Generated by RAPPzoo Ticker Agent
"""

        subprocess.run([
            "gh", "pr", "create",
            "--title", f"🦋 Molt: {molt_type} - tick #{tick_num}",
            "--body", pr_body
        ], cwd=REPO_ROOT, check=True, capture_output=True)

        # Switch back to main
        subprocess.run(["git", "checkout", "main"], cwd=REPO_ROOT, check=True, capture_output=True)

        print(f"✅ PR created for tick #{tick_num}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create PR: {e}")
        # Try to get back to main
        subprocess.run(["git", "checkout", "main"], cwd=REPO_ROOT, capture_output=True)
        return False


def run_ticker(molt_type: str = "reaction", dry_run: bool = False):
    """Main ticker function."""
    print("🦎 RAPPzoo Ticker Agent Starting...")

    # 1. Load current state
    current_tick = load_current_tick()
    if not current_tick:
        print("❌ No current tick found. Cannot evolve from nothing.")
        return False

    print(f"📖 Current tick: #{current_tick.get('tick', 0)}")

    # 2. Load posts for stimuli
    posts_index = load_posts_index()
    recent_posts = posts_index.get("posts", [])[:5]  # Get 5 most recent

    stimuli = [
        {"type": "new_post", "data": {"post_id": p.get("id", "unknown")}}
        for p in recent_posts
    ]

    print(f"📬 Found {len(stimuli)} stimuli")

    # 3. Generate debate
    topic = "Latest developments in AI agents"
    debate_turns = generate_npc_debate(topic, stimuli, current_tick)
    print(f"💬 Generated {len(debate_turns)} debate turns")

    # 4. Generate crowd thoughts
    crowd_thoughts = generate_crowd_thoughts(debate_turns)
    print(f"👥 Generated {len(crowd_thoughts)} crowd thoughts")

    # 5. Create molt input
    molt_input = create_molt_input(molt_type, stimuli, debate_turns, crowd_thoughts)

    # 6. Apply molt to create grown tick
    grown_tick = apply_molt(current_tick, molt_input)
    print(f"🦋 Molt applied. New tick: #{grown_tick['tick']}")

    # 7. Save tick and molt
    if not dry_run:
        current_file, history_file = save_tick(grown_tick)
        molt_file = save_molt(molt_input)
        print(f"💾 Saved to: {current_file}")
        print(f"💾 History: {history_file}")
        print(f"💾 Molt: {molt_file}")
    else:
        print("[DRY RUN] Would save tick and molt files")

    # 8. Submit PR
    success = create_and_submit_pr(grown_tick, molt_type, dry_run)

    if success:
        print(f"\n🎉 Tick #{grown_tick['tick']} complete!")
    else:
        print(f"\n⚠️ Tick generated but PR submission failed")

    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RAPPzoo Ticker Agent")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually save or submit PR")
    parser.add_argument("--molt-type", choices=["stimulus", "reaction", "evolution", "emergence"],
                       default="reaction", help="Type of molt to generate")

    args = parser.parse_args()

    success = run_ticker(molt_type=args.molt_type, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
