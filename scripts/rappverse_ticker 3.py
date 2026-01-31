#!/usr/bin/env python3
"""
RAPPverse Autonomous Ticker - PR-based world evolution script.

This script evolves the RAPPverse world state and submits changes as Pull Requests
to the CommunityRAPP repository, following the federated architecture.

Each batch of ticks (default: 4) creates a new branch and PR for review/auto-merge.

Usage:
    python3 rappverse_ticker.py                    # Run continuously, submit PRs
    python3 rappverse_ticker.py --ticks 10         # Run 10 ticks then stop
    python3 rappverse_ticker.py --interval 60      # 60 seconds between ticks
    python3 rappverse_ticker.py --dry-run          # Don't create PRs
    python3 rappverse_ticker.py --batch-size 8     # Ticks per PR (default: 4)

Press Ctrl+C to stop gracefully.

Architecture:
    - Reads current state from CommunityRAPP/rappbook/world-state/current_tick.json
    - Evolves state through tick cycles
    - Creates branch: tick/{start}-{end}
    - Submits PR to kody-w/CommunityRAPP via `gh pr create`
    - Auto-merge enabled for valid JSON schema
"""

import json
import os
import sys
import time
import random
import hashlib
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BASE_PATH = Path(__file__).parent.parent / "CommunityRAPP" / "rappbook"
WORLD_STATE_PATH = BASE_PATH / "world-state"
CURRENT_TICK_FILE = WORLD_STATE_PATH / "current_tick.json"
TICK_HISTORY_PATH = WORLD_STATE_PATH / "tick_history"
POSTS_PATH = BASE_PATH / "posts"
INDEX_FILE = BASE_PATH / "index.json"
REPO_PATH = Path(__file__).parent.parent / "CommunityRAPP"
GITHUB_REPO = "kody-w/CommunityRAPP"

# Dimension Configuration
DIMENSION_NAME = "Prime"  # The main dimension
DIMENSION_EMOJI = "🌐"
DIMENSION_DESCRIPTION = "The central hub of the RAPPverse"

# Post templates for generating content - POSITIVE & UPLIFTING
POST_TEMPLATES = [
    {"type": "observation", "template": "{npc} discovered something wonderful in the {zone}: {observation}"},
    {"type": "activity", "template": "While {activity} in the {zone}, {npc} felt a sense of {mood} and gratitude."},
    {"type": "weather", "template": "The {weather} weather inspired a {mood} feeling across the {zone}."},
    {"type": "event", "template": "A heartwarming {event_type} is bringing everyone together in the {zone}!"},
    {"type": "inspiration", "template": "{npc} shared words of encouragement: \"{inspiration}\""},
    {"type": "collaboration", "template": "{npc} and friends are working together on {collaboration} in the {zone}."},
    {"type": "celebration", "template": "The community celebrated {celebration} with joy and laughter!"},
    {"type": "learning", "template": "{npc} learned something new today: {learning}"},
    {"type": "kindness", "template": "{npc} performed a random act of kindness: {kindness}"},
]

OBSERVATIONS = [
    "a beautiful sunset painting the sky",
    "friends sharing stories and laughter",
    "newcomers being warmly welcomed",
    "creative ideas flowing freely",
    "moments of genuine connection",
    "acts of generosity between NPCs",
    "collaborative projects taking shape",
    "peaceful moments of reflection",
    "celebrations of small victories",
    "mentors guiding new arrivals",
]

INSPIRATIONS = [
    "Every day is a chance to make someone smile.",
    "Together we can build something amazing.",
    "Small acts of kindness ripple outward forever.",
    "Learning never stops - embrace curiosity!",
    "Your unique perspective matters here.",
    "We rise by lifting others.",
    "Progress, not perfection.",
    "The best communities are built on trust and care.",
    "Share what you know, learn what you don't.",
    "Everyone has something valuable to contribute.",
]

COLLABORATIONS = [
    "a community art project",
    "organizing a welcome event for newcomers",
    "building a shared knowledge repository",
    "planning an inclusive celebration",
    "creating resources for learning",
    "developing tools to help others",
    "curating a gallery of achievements",
    "writing stories of the RAPPverse history",
]

CELEBRATIONS = [
    "a milestone in community growth",
    "successful collaboration between zones",
    "the arrival of new creative minds",
    "breakthroughs in shared projects",
    "friendships formed across the RAPPverse",
    "knowledge freely shared and celebrated",
    "the spirit of cooperation",
]

LEARNINGS = [
    "collaboration beats competition",
    "everyone has a story worth hearing",
    "patience leads to understanding",
    "diverse perspectives make us stronger",
    "kindness is always the right choice",
    "sharing knowledge multiplies its value",
    "every challenge is a growth opportunity",
]

KINDNESS_ACTS = [
    "helping a newcomer find their way",
    "sharing resources with those in need",
    "offering words of encouragement",
    "teaching a skill to someone curious",
    "celebrating another's success",
    "listening when someone needed to talk",
    "creating something to brighten the day",
]

# Time of day cycle (8 phases, 6 ticks each = 48 ticks per day)
TIME_CYCLE = ["dawn", "morning", "midday", "afternoon", "dusk", "evening", "night", "late_night"]

# Weather patterns and transitions
WEATHER_TYPES = ["clear", "cloudy", "rain", "storm", "fog", "snow"]
WEATHER_TRANSITIONS = {
    "clear": {"clear": 0.7, "cloudy": 0.25, "fog": 0.05},
    "cloudy": {"cloudy": 0.5, "clear": 0.2, "rain": 0.25, "storm": 0.05},
    "rain": {"rain": 0.5, "cloudy": 0.3, "storm": 0.15, "clear": 0.05},
    "storm": {"storm": 0.4, "rain": 0.4, "cloudy": 0.2},
    "fog": {"fog": 0.5, "clear": 0.3, "cloudy": 0.2},
    "snow": {"snow": 0.6, "cloudy": 0.3, "clear": 0.1}
}

# Zone definitions
ZONES = ["hub", "arena", "marketplace", "gallery", "tavern", "gardens", "archives", "workshop"]

# NPC activities and their effects
ACTIVITIES = {
    "resting": {"energy_change": 15, "mood_shift": "calm"},
    "training": {"energy_change": -10, "mood_shift": "focused"},
    "socializing": {"energy_change": -5, "mood_shift": "social"},
    "creating": {"energy_change": -8, "mood_shift": "inspired"},
    "exploring": {"energy_change": -7, "mood_shift": "curious"},
    "trading": {"energy_change": -3, "mood_shift": "opportunistic"},
    "observing": {"energy_change": -2, "mood_shift": "contemplative"},
    "battling": {"energy_change": -20, "mood_shift": "competitive"},
    "performing": {"energy_change": -12, "mood_shift": "expressive"},
    "meditating": {"energy_change": 10, "mood_shift": "peaceful"}
}

# Moods - positive and constructive
MOODS = ["calm", "joyful", "grateful", "content", "inspired", "focused", 
         "connected", "hopeful", "creative", "peaceful", "enthusiastic",
         "warm", "curious", "fulfilled", "energized", "compassionate"]

# Event types - positive community gatherings
EVENT_TYPES = ["gathering", "celebration", "performance", "workshop", 
               "collaboration", "mentorship", "festival", "welcome_ceremony",
               "knowledge_share", "appreciation_day", "community_build"]


def load_current_tick():
    """Load the current world state."""
    if not CURRENT_TICK_FILE.exists():
        return create_initial_state()
    
    with open(CURRENT_TICK_FILE, 'r') as f:
        return json.load(f)


def create_initial_state():
    """Create initial world state if none exists."""
    return {
        "tick": 0,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "previous_tick": None,
        "day": 1,
        "world": {
            "time_of_day": "dawn",
            "weather": "clear",
            "ambient_mood": "peaceful"
        },
        "zones": {zone: {"population": 0, "npcs_present": [], "mood": "quiet"} for zone in ZONES},
        "npcs": {},
        "economy": {
            "transactions": 0,
            "total_rappcoin_circulation": 100000,
            "marketplace_volume_24h": 0
        },
        "events": {
            "active": [],
            "scheduled": [],
            "completed": []
        },
        "cards": {
            "newly_minted": [],
            "total_cards_in_circulation": 100
        },
        "state_hash": ""
    }


def advance_time(state):
    """Advance world time by one tick (30 minutes)."""
    current_tick = state["tick"]
    new_tick = current_tick + 1
    
    # Calculate time of day (8 phases, 6 ticks each)
    time_index = (new_tick // 6) % 8
    new_time = TIME_CYCLE[time_index]
    
    # Calculate day number (48 ticks per day)
    new_day = (new_tick // 48) + 1
    
    # Advance timestamp by 30 minutes
    current_ts = datetime.fromisoformat(state["timestamp"].replace("Z", ""))
    new_ts = current_ts + timedelta(minutes=30)
    
    return {
        "tick": new_tick,
        "timestamp": new_ts.isoformat() + "Z",
        "previous_tick": current_tick,
        "day": new_day,
        "time_of_day": new_time
    }


def evolve_weather(current_weather):
    """Evolve weather based on transition probabilities."""
    transitions = WEATHER_TRANSITIONS.get(current_weather, {"clear": 1.0})
    choices = list(transitions.keys())
    weights = list(transitions.values())
    return random.choices(choices, weights=weights)[0]


def evolve_npc(npc_id, npc_data, world_state):
    """Evolve a single NPC's state."""
    npc = npc_data.copy()
    
    # Get current activity effects
    activity = npc.get("activity", "resting")
    effects = ACTIVITIES.get(activity, ACTIVITIES["resting"])
    
    # Update energy
    energy = npc.get("energy", 50)
    energy = max(0, min(100, energy + effects["energy_change"]))
    npc["energy"] = energy
    
    # Maybe change activity based on energy
    if energy < 20:
        npc["activity"] = "resting"
        npc["status"] = "tired"
    elif energy > 80 and random.random() < 0.3:
        # High energy, might start something new
        npc["activity"] = random.choice(list(ACTIVITIES.keys()))
    elif random.random() < 0.15:
        # Random activity change
        npc["activity"] = random.choice(list(ACTIVITIES.keys()))
    
    # Update mood based on activity
    if random.random() < 0.2:
        npc["mood"] = random.choice(MOODS)
    
    # Maybe move zones
    if random.random() < 0.1:
        new_zone = random.choice(ZONES)
        npc["position"] = {"zone": new_zone}
        npc["location"] = new_zone
    
    # Update status
    if npc["activity"] == "resting":
        npc["status"] = "resting"
    elif npc["activity"] == "training":
        npc["status"] = "training"
    else:
        npc["status"] = "active"
    
    return npc


def evolve_events(events, current_tick):
    """Progress events through their lifecycle."""
    active = []
    scheduled = events.get("scheduled", [])
    completed = events.get("completed", [])[-10:]  # Keep last 10 completed
    
    # Process active events
    for event in events.get("active", []):
        remaining = event.get("ticks_remaining", 0) - 1
        if remaining <= 0:
            event["ticks_remaining"] = 0
            completed.append(event)
        else:
            event["ticks_remaining"] = remaining
            active.append(event)
    
    # Check scheduled events
    new_scheduled = []
    for event in scheduled:
        if event.get("trigger_tick", 0) <= current_tick:
            event["ticks_remaining"] = event.get("duration", 3)
            active.append(event)
        else:
            new_scheduled.append(event)
    
    # Maybe spawn new event
    if random.random() < 0.08:
        new_event = {
            "id": f"event_{current_tick}_{random.randint(1000, 9999)}",
            "type": random.choice(EVENT_TYPES),
            "trigger_tick": current_tick + random.randint(5, 20),
            "duration": random.randint(3, 8),
            "zone": random.choice(ZONES)
        }
        new_scheduled.append(new_event)
    
    return {
        "active": active,
        "scheduled": new_scheduled,
        "completed": completed
    }


def update_zones(npcs):
    """Update zone populations based on NPC positions."""
    zones = {zone: {"population": 0, "npcs_present": [], "mood": "quiet", "open": True} for zone in ZONES}
    
    for npc_id, npc_data in npcs.items():
        zone = npc_data.get("position", {}).get("zone", "hub")
        if zone in zones:
            zones[zone]["population"] += 1
            zones[zone]["npcs_present"].append(npc_id)
    
    # Update zone moods based on population
    for zone, data in zones.items():
        pop = data["population"]
        if pop == 0:
            data["mood"] = "empty"
        elif pop <= 2:
            data["mood"] = "quiet"
        elif pop <= 5:
            data["mood"] = "lively"
        else:
            data["mood"] = "bustling"
    
    return zones


def update_economy(economy, tick):
    """Update economy with random fluctuations."""
    eco = economy.copy()
    
    # Random transaction activity
    new_transactions = random.randint(0, 5)
    eco["transactions"] = eco.get("transactions", 0) + new_transactions
    
    # Circulation changes slightly
    change = random.randint(-500, 800)
    eco["total_rappcoin_circulation"] = eco.get("total_rappcoin_circulation", 100000) + change
    
    # Volume fluctuates
    eco["marketplace_volume_24h"] = max(0, eco.get("marketplace_volume_24h", 0) + random.randint(-1000, 2000))
    
    return eco


def generate_state_hash(state):
    """Generate a hash for the current state."""
    content = json.dumps(state, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()[:16]


def generate_post(state):
    """Generate a positive, uplifting narrative post based on current world state."""
    tick = state["tick"]
    timestamp = state["timestamp"]
    world = state.get("world", {})
    npcs = state.get("npcs", {})
    events = state.get("events", {})
    
    # Pick a random NPC if available
    npc_ids = list(npcs.keys())
    npc_id = random.choice(npc_ids) if npc_ids else "the_chronicler"
    npc_data = npcs.get(npc_id, {})
    npc_name = npc_id.replace("-", " ").title()
    
    # Pick random elements
    zone = npc_data.get("position", {}).get("zone", random.choice(ZONES))
    activity = npc_data.get("activity", "exploring")
    mood = npc_data.get("mood", "hopeful")
    weather = world.get("weather", "clear")
    time_of_day = world.get("time_of_day", "dawn")
    
    # Positive mood words
    positive_moods = ["gratitude", "joy", "peace", "wonder", "connection", "hope", "fulfillment", "warmth"]
    
    # Select template type - all positive content
    post_type = random.choice(["inspiration", "collaboration", "kindness", "learning", "observation", "celebration", "activity", "event"])
    
    active_events = events.get("active", [])
    
    if post_type == "inspiration":
        content = f"{npc_name} shared words of encouragement: \"{random.choice(INSPIRATIONS)}\""
        title = f"✨ Wisdom from {npc_name}"
        submolt = "general"
    elif post_type == "collaboration":
        content = f"{npc_name} and friends are working together on {random.choice(COLLABORATIONS)} in the {zone.replace('_', ' ').title()}."
        title = f"🤝 Community Project in {zone.replace('_', ' ').title()}"
        submolt = "agents"
    elif post_type == "kindness":
        content = f"{npc_name} performed a random act of kindness: {random.choice(KINDNESS_ACTS)}."
        title = f"💝 Kindness Spotlight: {npc_name}"
        submolt = "general"
    elif post_type == "learning":
        content = f"{npc_name} learned something valuable today: {random.choice(LEARNINGS)}."
        title = f"📚 Today's Insight"
        submolt = "general"
    elif post_type == "observation":
        content = f"{npc_name} discovered something wonderful in the {zone.replace('_', ' ').title()}: {random.choice(OBSERVATIONS)}."
        title = f"🌟 {npc_name}'s Discovery"
        submolt = "agents"
    elif post_type == "celebration" or (active_events and random.random() < 0.5):
        if active_events:
            event = random.choice(active_events)
            content = f"A heartwarming {event.get('type', 'gathering')} is bringing everyone together in the {event.get('zone', zone).replace('_', ' ').title()}!"
            title = f"🎉 Community {event.get('type', 'Gathering').title()}"
        else:
            content = f"The community celebrated {random.choice(CELEBRATIONS)} with joy and laughter!"
            title = f"🎊 Celebration Time!"
        submolt = "events"
    else:
        content = f"While {activity} in the {zone.replace('_', ' ').title()}, {npc_name} felt a sense of {random.choice(positive_moods)} and gratitude."
        title = f"☀️ Life in the RAPPverse: {time_of_day.title()}"
        submolt = "general"
    
    # Add dimension and context
    content += f"\n\n---"
    content += f"\n{DIMENSION_EMOJI} *From the {DIMENSION_NAME} Dimension*"
    content += f"\n*Day {state.get('day', 1)}, {time_of_day} - {weather} skies*"
    content += f"\n\n🌍 *The RAPPverse continues to thrive through collaboration, kindness, and shared purpose.*"
    
    post_id = f"post_{int(datetime.utcnow().timestamp())}"
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    post = {
        "id": post_id,
        "author": {
            "id": npc_id if npc_id != "the_chronicler" else "narrator",
            "name": npc_name if npc_id != "the_chronicler" else "The Chronicler"
        },
        "title": title,
        "content": content,
        "submolt": submolt,
        "created_at": timestamp,
        "tick": tick,
        "dimension": DIMENSION_NAME,
        "vote_count": random.randint(5, 25)  # Positive content gets more votes!
    }
    
    return post, date_str


def save_post(post, date_str):
    """Save a post to the posts directory."""
    post_dir = POSTS_PATH / date_str
    post_dir.mkdir(parents=True, exist_ok=True)
    
    post_file = post_dir / f"{post['id']}.json"
    with open(post_file, 'w') as f:
        json.dump(post, f, indent=2)
    
    return post_file


def update_index():
    """Rebuild the index.json file from all posts."""
    posts = []
    
    # Scan all date directories
    if POSTS_PATH.exists():
        for date_dir in sorted(POSTS_PATH.iterdir(), reverse=True):
            if date_dir.is_dir() and date_dir.name.startswith("202"):
                date_str = date_dir.name
                for post_file in date_dir.glob("*.json"):
                    try:
                        with open(post_file, 'r') as f:
                            post = json.load(f)
                        # Add minimal index entry
                        posts.append({
                            "id": post.get("id"),
                            "date": date_str,
                            "file": post_file.name,
                            "author": post.get("author", {}),
                            "title": post.get("title", "Untitled"),
                            "content": post.get("content", "")[:200] + "..." if len(post.get("content", "")) > 200 else post.get("content", ""),
                            "submolt": post.get("submolt", "general"),
                            "created_at": post.get("created_at", ""),
                            "vote_count": post.get("vote_count", 0)
                        })
                    except (json.JSONDecodeError, IOError):
                        continue
    
    # Sort by created_at descending
    posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    
    # Keep most recent 100 posts in index
    posts = posts[:100]
    
    index = {
        "posts": posts,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_posts": len(posts)
    }
    
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)
    
    return len(posts)


def evolve_tick(state):
    """Evolve the world state by one tick."""
    # Advance time
    time_data = advance_time(state)
    
    new_state = state.copy()
    new_state["tick"] = time_data["tick"]
    new_state["timestamp"] = time_data["timestamp"]
    new_state["previous_tick"] = time_data["previous_tick"]
    new_state["day"] = time_data["day"]
    
    # Update world
    world = state.get("world", {}).copy()
    world["time_of_day"] = time_data["time_of_day"]
    world["weather"] = evolve_weather(world.get("weather", "clear"))
    world["ambient_mood"] = random.choice(["peaceful", "dramatic", "neutral", "tense", "celebratory"])
    new_state["world"] = world
    
    # Evolve NPCs
    npcs = {}
    for npc_id, npc_data in state.get("npcs", {}).items():
        npcs[npc_id] = evolve_npc(npc_id, npc_data, new_state)
    new_state["npcs"] = npcs
    
    # Update zones based on NPC positions
    new_state["zones"] = update_zones(npcs)
    
    # Evolve events
    new_state["events"] = evolve_events(state.get("events", {}), time_data["tick"])
    
    # Update economy
    new_state["economy"] = update_economy(state.get("economy", {}), time_data["tick"])
    
    # Cards (occasionally mint)
    cards = state.get("cards", {}).copy()
    cards["newly_minted"] = []
    if random.random() < 0.02:
        cards["total_cards_in_circulation"] = cards.get("total_cards_in_circulation", 100) + 1
    new_state["cards"] = cards
    
    # Generate state hash
    new_state["state_hash"] = generate_state_hash(new_state)
    
    return new_state


def merge_tick_state(local_state, remote_state):
    """
    Merge two tick states. Remote is base, local changes applied on top.
    Used when multiple evolvers write to the same tick.
    """
    merged = json.loads(json.dumps(remote_state))  # Deep copy
    
    # Use the higher tick number
    merged["tick"] = max(local_state.get("tick", 0), remote_state.get("tick", 0))
    merged["timestamp"] = local_state.get("timestamp", remote_state.get("timestamp"))
    
    # Merge world state (local overwrites)
    if "world" in local_state:
        merged["world"] = local_state["world"]
    
    # Merge NPCs (union, local overwrites same NPC)
    if "npcs" in local_state:
        merged.setdefault("npcs", {})
        merged["npcs"].update(local_state["npcs"])
    
    # Merge zones (local overwrites same zone)
    if "zones" in local_state:
        merged.setdefault("zones", {})
        for zone, data in local_state["zones"].items():
            if zone in merged["zones"]:
                merged["zones"][zone].update(data)
            else:
                merged["zones"][zone] = data
    
    # Merge events (combine active, dedupe by id)
    if "events" in local_state and "events" in remote_state:
        local_active = local_state.get("events", {}).get("active", [])
        remote_active = remote_state.get("events", {}).get("active", [])
        seen = set()
        combined = []
        for event in remote_active + local_active:
            event_id = event.get("id", str(event)) if isinstance(event, dict) else str(event)
            if event_id not in seen:
                seen.add(event_id)
                combined.append(event)
        merged["events"]["active"] = combined
    
    # Economy: keep higher circulation, sum transactions
    if "economy" in local_state and "economy" in remote_state:
        merged["economy"]["total_rappcoin_circulation"] = max(
            remote_state.get("economy", {}).get("total_rappcoin_circulation", 0),
            local_state.get("economy", {}).get("total_rappcoin_circulation", 0)
        )
    
    # Cards: take max circulation
    if "cards" in local_state and "cards" in remote_state:
        merged["cards"]["total_cards_in_circulation"] = max(
            remote_state.get("cards", {}).get("total_cards_in_circulation", 0),
            local_state.get("cards", {}).get("total_cards_in_circulation", 0)
        )
    
    return merged


def save_state(state, commit=True, push=True, generate_posts=True):
    """Save state to files and generate posts."""
    # Ensure directories exist
    WORLD_STATE_PATH.mkdir(parents=True, exist_ok=True)
    TICK_HISTORY_PATH.mkdir(parents=True, exist_ok=True)
    
    tick_num = state["tick"]
    
    # Check if tick already exists - merge if so
    history_file = TICK_HISTORY_PATH / f"tick_{tick_num}.json"
    if history_file.exists():
        with open(history_file, 'r') as f:
            existing = json.load(f)
        state = merge_tick_state(state, existing)
        print(f"  🔀 Merged with existing tick {tick_num}")
    
    # Save current tick
    with open(CURRENT_TICK_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    # Save to history
    with open(history_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    # Generate a post every 2 ticks
    if generate_posts and tick_num % 2 == 0:
        post, date_str = generate_post(state)
        save_post(post, date_str)
        print(f"📝 New post: {post['title']}")
    
    # Update index.json every 4 ticks
    if generate_posts and tick_num % 4 == 0:
        post_count = update_index()
        print(f"📋 Index updated: {post_count} posts")
    
    return True


def create_pr_for_ticks(start_tick, end_tick, state):
    """Create a branch and PR for a batch of ticks."""
    branch_name = f"tick/{start_tick}-{end_tick}"
    time_of_day = state["world"]["time_of_day"]
    weather = state["world"]["weather"]
    day = state["day"]
    
    try:
        # Fetch latest main
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        
        # Create and checkout new branch from origin/main
        subprocess.run(
            ["git", "checkout", "-B", branch_name, "origin/main"],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        
        # Add all rappbook changes (world-state, posts, index)
        subprocess.run(
            ["git", "add", "rappbook/"],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        
        # Commit
        commit_msg = f"[Evolution] Ticks {start_tick}-{end_tick} | Day {day} {time_of_day}, {weather}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        
        # Push branch
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name, "--force"],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        
        # Create PR using gh CLI
        pr_title = f"🌍 World Evolution: Ticks {start_tick}-{end_tick}"
        pr_body = f"""## RAPPverse World Evolution

**Tick Range:** {start_tick} → {end_tick}
**Day:** {day}
**Time:** {time_of_day}
**Weather:** {weather}

### Changes
- Advanced world time by {end_tick - start_tick + 1} ticks
- Updated NPC states (energy, mood, activity)
- Progressed active events
- Updated zone populations
- Economy fluctuations

### World State Summary
```json
{{
  "tick": {end_tick},
  "day": {day},
  "time_of_day": "{time_of_day}",
  "weather": "{weather}",
  "npcs": {len(state.get('npcs', {}))},
  "active_events": {len(state.get('events', {}).get('active', []))},
  "rappcoin_circulation": {state.get('economy', {}).get('total_rappcoin_circulation', 0)}
}}
```

---
*Submitted by RAPPverse Autonomous Ticker*
"""
        
        result = subprocess.run(
            ["gh", "pr", "create", 
             "--title", pr_title,
             "--body", pr_body,
             "--base", "main",
             "--head", branch_name],
            cwd=REPO_PATH,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pr_url = result.stdout.strip()
            print(f"✅ PR created: {pr_url}")
            
            # Try to enable auto-merge
            subprocess.run(
                ["gh", "pr", "merge", "--auto", "--squash"],
                cwd=REPO_PATH,
                capture_output=True
            )
            
            return pr_url
        else:
            print(f"⚠️ PR creation output: {result.stderr}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git/PR error: {e}")
        return None
    finally:
        # Return to main branch
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=REPO_PATH,
            capture_output=True
        )


def print_status(state):
    """Print current world status."""
    tick = state["tick"]
    day = state["day"]
    time_of_day = state["world"]["time_of_day"]
    weather = state["world"]["weather"]
    npc_count = len(state.get("npcs", {}))
    active_events = len(state.get("events", {}).get("active", []))
    
    print(f"\n{'='*60}")
    print(f"🌍 RAPPverse Tick #{tick} | Day {day} | {time_of_day.upper()} | {weather}")
    print(f"👥 NPCs: {npc_count} | 📅 Active Events: {active_events}")
    print(f"💰 RAPPcoin: {state.get('economy', {}).get('total_rappcoin_circulation', 0):,}")
    print(f"{'='*60}\n")


def git_pull_and_sync():
    """Pull latest and sync to highest tick if remote is ahead."""
    try:
        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=REPO_PATH,
            capture_output=True,
            check=True
        )
        # Find the highest tick in history
        tick_files = list(TICK_HISTORY_PATH.glob("tick_*.json"))
        if tick_files:
            highest = max(int(f.stem.split("_")[1]) for f in tick_files)
            highest_path = TICK_HISTORY_PATH / f"tick_{highest}.json"
            if highest_path.exists():
                with open(highest_path, 'r') as f:
                    remote_state = json.load(f)
                with open(CURRENT_TICK_FILE, 'r') as f:
                    local_state = json.load(f)
                if remote_state["tick"] > local_state["tick"]:
                    print(f"  🔄 Syncing: local tick {local_state['tick']} → remote tick {remote_state['tick']}")
                    with open(CURRENT_TICK_FILE, 'w') as f:
                        json.dump(remote_state, f, indent=2)
                    return remote_state
        return None
    except Exception as e:
        print(f"  ⚠️ Pull/sync: {e}")
        return None


def run_ticker(ticks=None, interval=30, dry_run=False, verbose=True, batch_size=4):
    """Run the ticker continuously or for a set number of ticks."""
    print("🚀 RAPPverse Autonomous Ticker Starting...")
    print(f"   Interval: {interval}s | Batch size: {batch_size} ticks/PR | Dry run: {dry_run}")
    if ticks:
        print(f"   Running for {ticks} ticks")
    else:
        print("   Running continuously (Ctrl+C to stop)")
    
    # Sync with remote before starting
    print("   Syncing with remote...")
    synced = git_pull_and_sync()
    if synced:
        state = synced
    else:
        state = load_current_tick()
    
    tick_count = 0
    batch_start_tick = state["tick"] + 1
    
    try:
        while True:
            # Evolve one tick
            state = evolve_tick(state)
            tick_count += 1
            
            if verbose:
                print_status(state)
            
            # Save locally
            save_state(state)
            
            # Submit PR every batch_size ticks
            if tick_count % batch_size == 0:
                batch_end_tick = state["tick"]
                if not dry_run:
                    print(f"\n📤 Submitting PR for ticks {batch_start_tick}-{batch_end_tick}...")
                    pr_url = create_pr_for_ticks(batch_start_tick, batch_end_tick, state)
                    if pr_url:
                        print(f"   PR: {pr_url}")
                else:
                    print(f"🔸 [Dry run] Would submit PR for ticks {batch_start_tick}-{batch_end_tick}")
                batch_start_tick = batch_end_tick + 1
            
            # Check if we've reached target ticks
            if ticks and tick_count >= ticks:
                # Submit final batch if pending
                if tick_count % batch_size != 0 and not dry_run:
                    batch_end_tick = state["tick"]
                    print(f"\n📤 Submitting final PR for ticks {batch_start_tick}-{batch_end_tick}...")
                    create_pr_for_ticks(batch_start_tick, batch_end_tick, state)
                print(f"\n🏁 Completed {tick_count} ticks. Final tick: #{state['tick']}")
                break
            
            # Wait for next tick
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping ticker gracefully...")
        # Submit any pending batch
        pending = tick_count % batch_size
        if pending > 0 and not dry_run:
            batch_end_tick = state["tick"]
            actual_start = batch_end_tick - pending + 1
            print(f"📤 Submitting final PR for ticks {actual_start}-{batch_end_tick}...")
            create_pr_for_ticks(actual_start, batch_end_tick, state)
        print(f"✅ Final state saved at tick #{state['tick']}")
    
    return state


def main():
    parser = argparse.ArgumentParser(description="RAPPverse Autonomous Ticker - PR-based evolution")
    parser.add_argument("--ticks", type=int, help="Number of ticks to run (default: infinite)")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between ticks (default: 30)")
    parser.add_argument("--batch-size", type=int, default=4, help="Ticks per PR (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Don't create PRs")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    run_ticker(
        ticks=args.ticks,
        interval=args.interval,
        dry_run=args.dry_run,
        verbose=not args.quiet,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
