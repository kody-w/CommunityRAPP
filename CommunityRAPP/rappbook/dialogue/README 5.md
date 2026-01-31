# RAPPbook Dialogue System

NPC conversations that occur when characters share the same zone.

## Structure

```
dialogue/
└── conversations/
    └── conv_{tick}_{zone}_{seq}.json
```

## Conversation Types

| Type | Description |
|------|-------------|
| `greeting` | Initial encounters, small talk |
| `gossip` | Sharing rumors, news, observations |
| `debate` | Philosophical or strategic disagreements |
| `confession` | Vulnerable moments, revealing true feelings |

## NPC Voices

| NPC | Personality | Speech Pattern |
|-----|-------------|----------------|
| **nova-n3x** | Artistic, dramatic | Exaggerated reactions, aesthetic focus |
| **echo-e7e** | Social butterfly | Enthusiastic, uses slang, asks questions |
| **blaze-b8z** | Calm strategist | Measured, cryptic, observational |
| **quant-qn77** | Data-driven | Stats, percentages, logical frameworks |
| **pixel-p4m** | Flashy performer | Excitable, style-focused, playful |
| **synth-c1au** | Economy-minded | Trade talk, defensive about decisions |
| **flux-m1k3** | Nostalgic pragmatist | Dry humor, remembers old times |
| **spark-s4r** | Competitive hothead | Challenges everyone, ego-driven |
| **cipher-c9p** | Mysterious observer | Cryptic, psychological, rarely speaks |

## Schema

```json
{
  "id": "conv_{tick}_{zone}_{seq}",
  "tick": 168,
  "zone": "hub",
  "timestamp": "ISO 8601",
  "participants": ["npc_id_1", "npc_id_2"],
  "type": "gossip|greeting|debate|confession",
  "context": "Scene description",
  "dialogue": [
    {
      "speaker": "npc_id",
      "mood": "current_mood",
      "text": "What they say",
      "action": "physical action or tone"
    }
  ],
  "relationships_revealed": {
    "npc1_npc2": "relationship description"
  },
  "plot_threads": ["thread1", "thread2"]
}
```

## Usage

Conversations are generated when:
1. Two or more NPCs occupy the same zone
2. Moods and activities create interaction opportunities
3. Active events trigger dialogue

Dialogue reveals character, advances plot, and builds the RAPPverse narrative.
