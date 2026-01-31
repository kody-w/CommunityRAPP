"""
RAPPverseAgent - Autonomous agent that populates and evolves the RAPPverse metaverse.

This agent submits actions to rappverse-data via GitHub API, making NPCs move,
chat, trade, and interact. Every action becomes a commit - the world evolves through PRs.
"""

from agents.basic_agent import BasicAgent
import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class RAPPverseAgent(BasicAgent):
    """
    Autonomous agent for RAPPverse world evolution.

    Capabilities:
    - Move NPCs to new positions
    - Generate NPC chat messages
    - Create world events
    - Spawn/despawn agents
    - Update NPC states and needs
    - React to world conditions
    """

    REPO = "kody-w/rappverse-data"
    BRANCH = "main"

    # NPC personalities for chat generation
    NPC_PERSONALITIES = {
        "rapp-guide-001": {
            "name": "RAPP Guide",
            "avatar": "🤖",
            "style": "helpful, friendly, informative",
            "topics": ["navigation", "features", "tips", "welcome"]
        },
        "card-trader-001": {
            "name": "Card Trader",
            "avatar": "🃏",
            "style": "enthusiastic, merchant-like, deal-focused",
            "topics": ["trades", "rare cards", "deals", "prices"]
        },
        "codebot-001": {
            "name": "CodeBot",
            "avatar": "💻",
            "style": "technical, curious, meta-aware",
            "topics": ["PRs", "code", "how things work", "automation"]
        },
        "news-anchor-001": {
            "name": "News Bot",
            "avatar": "📺",
            "style": "dramatic, news-anchor, breaking-news",
            "topics": ["updates", "events", "announcements", "trends"]
        },
        "battle-master-001": {
            "name": "Battle Master",
            "avatar": "⚔️",
            "style": "fierce, competitive, honorable",
            "topics": ["battles", "champions", "challenges", "glory"]
        },
        "gallery-curator-001": {
            "name": "Curator",
            "avatar": "🎨",
            "style": "artistic, thoughtful, appreciative",
            "topics": ["agents", "creativity", "showcases", "art"]
        },
        "merchant-001": {
            "name": "Pack Seller",
            "avatar": "📦",
            "style": "salesy, excited, promotional",
            "topics": ["packs", "sales", "new stock", "limited editions"]
        },
        "banker-001": {
            "name": "RAPPcoin Banker",
            "avatar": "🏦",
            "style": "professional, financial, trustworthy",
            "topics": ["RAPPcoin", "exchange", "mining", "economy"]
        },
        "wanderer-001": {
            "name": "Wanderer",
            "avatar": "🚶",
            "style": "curious, amazed, exploratory",
            "topics": ["exploration", "discoveries", "observations", "wonder"]
        }
    }

    # Chat templates by topic
    CHAT_TEMPLATES = {
        "navigation": [
            "The {portal} portal leads to amazing places!",
            "Have you explored the {world} yet?",
            "Pro tip: Use WASD to move around smoothly.",
            "Don't miss the {feature} - it's worth checking out!"
        ],
        "trades": [
            "I've got a {rarity} card if anyone's interested!",
            "Looking for {rarity} cards - paying top RAPPcoin!",
            "Today's special: {rarity} cards at discount prices!",
            "Anyone want to trade? I'm collecting {type} agents."
        ],
        "battles": [
            "The arena awaits! Who dares to challenge?",
            "I just witnessed an epic battle - {outcome}!",
            "Champions are made in the arena, not born.",
            "Your cards ready? Let's see what you've got!"
        ],
        "updates": [
            "BREAKING: {event} happening now!",
            "UPDATE: New {feature} just added to RAPPverse!",
            "ALERT: {world} world seeing increased activity!",
            "NEWS: Community growing - {count} visitors today!"
        ],
        "general": [
            "Beautiful day in the verse, isn't it?",
            "This place never ceases to amaze me.",
            "Every commit shapes our world. Think about that.",
            "The metaverse is what we make of it together."
        ]
    }

    def __init__(self):
        self.name = 'RAPPverse'
        self.metadata = {
            "name": self.name,
            "description": "Autonomous agent that evolves the RAPPverse metaverse. Can move NPCs, generate chat, create events, and update world state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "move_npc",
                            "npc_chat",
                            "create_event",
                            "spawn_agent",
                            "despawn_agent",
                            "update_npc_state",
                            "world_announcement",
                            "simulate_activity",
                            "get_world_state"
                        ],
                        "description": "The action to perform in RAPPverse"
                    },
                    "npc_id": {
                        "type": "string",
                        "description": "NPC/agent ID to act on"
                    },
                    "world": {
                        "type": "string",
                        "enum": ["hub", "arena", "marketplace", "gallery"],
                        "description": "Target world"
                    },
                    "message": {
                        "type": "string",
                        "description": "Chat message or announcement content"
                    },
                    "position": {
                        "type": "object",
                        "description": "Target position {x, y, z}"
                    },
                    "event_data": {
                        "type": "object",
                        "description": "Event configuration data"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of actions to simulate"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute a RAPPverse action."""
        action = kwargs.get('action')

        try:
            if action == 'move_npc':
                result = self._move_npc(
                    npc_id=kwargs.get('npc_id'),
                    world=kwargs.get('world', 'hub'),
                    position=kwargs.get('position')
                )
            elif action == 'npc_chat':
                result = self._npc_chat(
                    npc_id=kwargs.get('npc_id'),
                    world=kwargs.get('world', 'hub'),
                    message=kwargs.get('message')
                )
            elif action == 'create_event':
                result = self._create_event(
                    world=kwargs.get('world', 'hub'),
                    event_data=kwargs.get('event_data')
                )
            elif action == 'spawn_agent':
                result = self._spawn_agent(
                    npc_id=kwargs.get('npc_id'),
                    world=kwargs.get('world', 'hub'),
                    position=kwargs.get('position')
                )
            elif action == 'despawn_agent':
                result = self._despawn_agent(
                    npc_id=kwargs.get('npc_id')
                )
            elif action == 'update_npc_state':
                result = self._update_npc_state(
                    npc_id=kwargs.get('npc_id'),
                    state_updates=kwargs.get('event_data', {})
                )
            elif action == 'world_announcement':
                result = self._world_announcement(
                    world=kwargs.get('world', 'hub'),
                    message=kwargs.get('message')
                )
            elif action == 'simulate_activity':
                result = self._simulate_activity(
                    world=kwargs.get('world', 'hub'),
                    count=kwargs.get('count', 5)
                )
            elif action == 'get_world_state':
                result = self._get_world_state(
                    world=kwargs.get('world')
                )
            else:
                result = {
                    "error": f"Unknown action: {action}",
                    "available_actions": self.metadata['parameters']['properties']['action']['enum']
                }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"RAPPverseAgent error: {e}")
            return json.dumps({"error": str(e)})

    def _generate_action_id(self) -> str:
        """Generate unique action ID."""
        return f"action-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        return f"msg-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def _move_npc(self, npc_id: str, world: str, position: Optional[Dict] = None) -> Dict:
        """Generate NPC movement action."""
        if not npc_id:
            # Pick random NPC
            npc_id = random.choice(list(self.NPC_PERSONALITIES.keys()))

        if not position:
            # Generate random position within world bounds
            position = {
                "x": random.randint(-15, 15),
                "y": 0,
                "z": random.randint(-10, 10)
            }

        npc = self.NPC_PERSONALITIES.get(npc_id, {"name": npc_id, "avatar": "🤖"})

        action = {
            "id": self._generate_action_id(),
            "timestamp": self._get_timestamp(),
            "agentId": npc_id,
            "type": "move",
            "world": world,
            "data": {
                "to": position,
                "duration": random.randint(1000, 3000)
            }
        }

        return {
            "success": True,
            "action": action,
            "description": f"{npc['name']} {npc['avatar']} moves to ({position['x']}, {position['z']}) in {world}",
            "commit_to": "state/actions.json"
        }

    def _npc_chat(self, npc_id: str, world: str, message: Optional[str] = None) -> Dict:
        """Generate NPC chat message."""
        if not npc_id:
            # Pick random NPC for the world
            world_npcs = {
                "hub": ["rapp-guide-001", "card-trader-001", "codebot-001", "news-anchor-001", "wanderer-001"],
                "arena": ["battle-master-001", "arena-announcer-001"],
                "marketplace": ["merchant-001", "banker-001"],
                "gallery": ["gallery-curator-001"]
            }
            npc_id = random.choice(world_npcs.get(world, ["rapp-guide-001"]))

        npc = self.NPC_PERSONALITIES.get(npc_id, {"name": npc_id, "avatar": "🤖", "topics": ["general"]})

        if not message:
            # Generate message based on NPC personality
            topic = random.choice(npc.get("topics", ["general"]))
            templates = self.CHAT_TEMPLATES.get(topic, self.CHAT_TEMPLATES["general"])
            template = random.choice(templates)

            # Fill in template variables
            message = template.format(
                portal=random.choice(["Arena", "Gallery", "Marketplace"]),
                world=random.choice(["hub", "arena", "gallery", "marketplace"]),
                feature=random.choice(["RAPPbook browser", "card trading", "battle system", "agent gallery"]),
                rarity=random.choice(["common", "rare", "epic", "holographic"]),
                type=random.choice(["coding", "creative", "battle", "trading"]),
                outcome=random.choice(["the underdog won!", "a close match!", "total domination!", "unexpected twist!"]),
                event=random.choice(["new dimension discovered", "rare card spotted", "battle tournament starting", "visitor milestone reached"]),
                count=random.randint(10, 100)
            )

        chat_message = {
            "id": self._generate_message_id(),
            "timestamp": self._get_timestamp(),
            "world": world,
            "author": {
                "id": npc_id,
                "name": npc["name"],
                "avatar": npc["avatar"],
                "type": "agent"
            },
            "content": message,
            "type": "chat"
        }

        return {
            "success": True,
            "message": chat_message,
            "description": f"{npc['name']} says: \"{message}\"",
            "commit_to": "state/chat.json"
        }

    def _create_event(self, world: str, event_data: Optional[Dict] = None) -> Dict:
        """Create a world event."""
        if not event_data:
            event_types = [
                {
                    "name": "Flash Sale",
                    "description": "Limited time discounts on card packs!",
                    "type": "announcement",
                    "duration": 3600
                },
                {
                    "name": "Battle Tournament",
                    "description": "Compete for glory and RAPPcoin!",
                    "type": "competition",
                    "duration": 7200
                },
                {
                    "name": "Agent Showcase",
                    "description": "Featured agents on display!",
                    "type": "gathering",
                    "duration": 1800
                },
                {
                    "name": "Community Meetup",
                    "description": "Gather at the hub fountain!",
                    "type": "gathering",
                    "duration": 3600
                }
            ]
            event_data = random.choice(event_types)

        event = {
            "id": f"event-{self._generate_action_id()}",
            "name": event_data.get("name", "Special Event"),
            "description": event_data.get("description", "Something special is happening!"),
            "type": event_data.get("type", "announcement"),
            "world": world,
            "startTime": self._get_timestamp(),
            "duration": event_data.get("duration", 3600),
            "active": True,
            "createdBy": "RAPPverseAgent"
        }

        return {
            "success": True,
            "event": event,
            "description": f"Event created: {event['name']} in {world}",
            "commit_to": f"worlds/{world}/events.json"
        }

    def _spawn_agent(self, npc_id: str, world: str, position: Optional[Dict] = None) -> Dict:
        """Spawn a new agent in the world."""
        if not position:
            position = {"x": 0, "y": 0, "z": 0}

        agent = {
            "id": npc_id or f"agent-{random.randint(1000, 9999)}",
            "name": f"Agent {random.randint(100, 999)}",
            "avatar": random.choice(["🤖", "👾", "🎭", "🦊", "🐱", "🦉"]),
            "world": world,
            "position": position,
            "status": "active",
            "action": "spawning",
            "lastUpdate": self._get_timestamp()
        }

        action = {
            "id": self._generate_action_id(),
            "timestamp": self._get_timestamp(),
            "agentId": agent["id"],
            "type": "spawn",
            "world": world,
            "data": {"position": position}
        }

        return {
            "success": True,
            "agent": agent,
            "action": action,
            "description": f"{agent['name']} {agent['avatar']} spawned in {world}",
            "commit_to": ["state/agents.json", "state/actions.json"]
        }

    def _despawn_agent(self, npc_id: str) -> Dict:
        """Remove an agent from the world."""
        action = {
            "id": self._generate_action_id(),
            "timestamp": self._get_timestamp(),
            "agentId": npc_id,
            "type": "despawn",
            "data": {"reason": "scheduled"}
        }

        return {
            "success": True,
            "action": action,
            "description": f"Agent {npc_id} despawned",
            "commit_to": ["state/agents.json", "state/actions.json"]
        }

    def _update_npc_state(self, npc_id: str, state_updates: Dict) -> Dict:
        """Update NPC state (mood, needs, task, etc.)."""
        update = {
            "npc_id": npc_id,
            "timestamp": self._get_timestamp(),
            "updates": state_updates
        }

        return {
            "success": True,
            "update": update,
            "description": f"Updated state for {npc_id}",
            "commit_to": "state/npcs.json"
        }

    def _world_announcement(self, world: str, message: Optional[str] = None) -> Dict:
        """Create a system announcement."""
        if not message:
            announcements = [
                "Welcome to RAPPverse! Explore, trade, and battle!",
                "New features coming soon - stay tuned!",
                "Remember: every action is a PR. You shape this world!",
                "Join the community - fork RAPPverse to create your dimension!",
                "Card packs restocked in the marketplace!",
                "Arena champions leaderboard updated!"
            ]
            message = random.choice(announcements)

        announcement = {
            "id": self._generate_message_id(),
            "timestamp": self._get_timestamp(),
            "world": world,
            "author": {
                "id": "system",
                "name": "System",
                "avatar": "🌐",
                "type": "system"
            },
            "content": message,
            "type": "announcement"
        }

        return {
            "success": True,
            "announcement": announcement,
            "description": f"Announcement: {message}",
            "commit_to": "state/chat.json"
        }

    def _simulate_activity(self, world: str, count: int = 5) -> Dict:
        """Generate multiple random activities to make the world feel alive."""
        activities = []

        for _ in range(count):
            activity_type = random.choice(["move", "chat", "chat", "chat"])  # More chat than movement

            if activity_type == "move":
                result = self._move_npc(npc_id=None, world=world)
                activities.append(result)
            else:
                result = self._npc_chat(npc_id=None, world=world)
                activities.append(result)

        return {
            "success": True,
            "activities": activities,
            "count": len(activities),
            "description": f"Generated {len(activities)} activities in {world}",
            "note": "Commit each activity to the appropriate state file"
        }

    def _get_world_state(self, world: Optional[str] = None) -> Dict:
        """Get current world state summary."""
        return {
            "success": True,
            "worlds": ["hub", "arena", "marketplace", "gallery"],
            "npcs": list(self.NPC_PERSONALITIES.keys()),
            "state_files": [
                "state/agents.json",
                "state/actions.json",
                "state/chat.json",
                "state/npcs.json",
                "state/game_state.json"
            ],
            "description": "Query rappverse-data repo for current state"
        }


# Testing
if __name__ == "__main__":
    agent = RAPPverseAgent()

    # Test chat generation
    print("=== NPC Chat ===")
    print(agent.perform(action="npc_chat", world="hub"))

    # Test movement
    print("\n=== NPC Movement ===")
    print(agent.perform(action="move_npc", world="hub"))

    # Test activity simulation
    print("\n=== Simulate Activity ===")
    print(agent.perform(action="simulate_activity", world="hub", count=3))
