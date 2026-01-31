"""
Skills Library Agent - Converts Claude Skills to RAPP-compatible agents.

Bridges the Anthropic Skills directory format (SKILL.md with YAML frontmatter)
to the RAPP agent pattern (Python classes inheriting from BasicAgent).

Supports both local skills repository and fetching from GitHub (anthropics/skills).
"""

from agents.basic_agent import BasicAgent
from utils.storage_factory import get_storage_manager
import logging
import os
import json
import re
import yaml
import requests
from datetime import datetime
from pathlib import Path


class SkillsLibraryAgent(BasicAgent):
    """
    Manages the Anthropic Skills library and converts skills to RAPP-compatible agents.

    Reads Claude Skills from the local repository OR the public GitHub repository,
    parses SKILL.md files, and generates deployable agent.py files that integrate
    with the RAPP system.
    """

    # Default skills repository location
    DEFAULT_SKILLS_PATH = "/Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/skills"

    # GitHub repository configuration
    GITHUB_REPO = "anthropics/skills"
    GITHUB_BRANCH = "main"
    GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
    GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"

    def __init__(self):
        self.name = 'SkillsLibrary'
        self.metadata = {
            "name": self.name,
            "description": "Converts Anthropic Claude Skills to RAPP-compatible agents. Discovers, previews, and generates deployable agent.py files from skills. Supports BOTH local skills repository AND fetching from GitHub (anthropics/skills). Use source='github' to fetch skills like algorithmic-art, pdf, xlsx, mcp-builder directly from https://github.com/anthropics/skills",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'discover' (list all available skills), 'preview' (show skill details without generating), 'generate' (create agent.py from skill), 'install' (generate and deploy to Azure storage), 'list_installed' (show deployed skill agents), 'get_skill_content' (get full SKILL.md content), 'fetch_github' (fetch skill from GitHub and save locally)",
                        "enum": ["discover", "preview", "generate", "install", "list_installed", "get_skill_content", "fetch_github"]
                    },
                    "skill_name": {
                        "type": "string",
                        "description": "Name of the skill to operate on (e.g., 'pdf', 'xlsx', 'mcp-builder', 'algorithmic-art', 'skill-creator'). Required for preview, generate, install, get_skill_content, fetch_github actions."
                    },
                    "source": {
                        "type": "string",
                        "description": "Where to fetch skills from: 'local' (default - local skills directory) or 'github' (fetch from https://github.com/anthropics/skills). Use 'github' to pull skills directly from the public Anthropic skills repository.",
                        "enum": ["local", "github"],
                        "default": "local"
                    },
                    "skills_path": {
                        "type": "string",
                        "description": "Optional: Custom path to local skills repository. Defaults to the local skills directory. Only used when source='local'."
                    },
                    "include_scripts": {
                        "type": "boolean",
                        "description": "Optional: Whether to bundle scripts from the skill into the generated agent. Default is true."
                    },
                    "include_references": {
                        "type": "boolean",
                        "description": "Optional: Whether to bundle reference documentation into the generated agent. Default is true."
                    },
                    "agent_name_override": {
                        "type": "string",
                        "description": "Optional: Override the generated agent's name. Defaults to skill name + 'Agent'."
                    }
                },
                "required": ["action"]
            }
        }
        self.storage_manager = get_storage_manager()
        self._github_cache = {}  # Cache for GitHub API responses
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action')
        source = kwargs.get('source', 'local')

        try:
            if action == 'discover':
                if source == 'github':
                    return self._discover_github_skills(kwargs)
                return self._discover_skills(kwargs)
            elif action == 'preview':
                if source == 'github':
                    return self._preview_github_skill(kwargs)
                return self._preview_skill(kwargs)
            elif action == 'generate':
                if source == 'github':
                    return self._generate_agent_from_github(kwargs)
                return self._generate_agent(kwargs)
            elif action == 'install':
                if source == 'github':
                    return self._install_agent_from_github(kwargs)
                return self._install_agent(kwargs)
            elif action == 'list_installed':
                return self._list_installed_skill_agents()
            elif action == 'get_skill_content':
                if source == 'github':
                    return self._get_github_skill_content(kwargs)
                return self._get_skill_content(kwargs)
            elif action == 'fetch_github':
                return self._fetch_github_skill(kwargs)
            else:
                return f"Error: Unknown action '{action}'"
        except Exception as e:
            logging.error(f"Error in SkillsLibrary: {str(e)}")
            return f"Error: {str(e)}"

    def _get_skills_path(self, params):
        """Get the skills repository path"""
        return params.get('skills_path') or self.DEFAULT_SKILLS_PATH

    def _parse_skill_md(self, skill_path):
        """Parse a SKILL.md file and extract frontmatter + body"""
        skill_md_path = os.path.join(skill_path, 'SKILL.md')

        if not os.path.exists(skill_md_path):
            return None

        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError as e:
                    logging.warning(f"Failed to parse YAML frontmatter: {e}")
                body = parts[2].strip()

        return {
            'frontmatter': frontmatter,
            'body': body,
            'raw': content
        }

    def _get_skill_resources(self, skill_path):
        """Get bundled resources (scripts, references, assets) for a skill"""
        resources = {
            'scripts': [],
            'references': [],
            'assets': [],
            'templates': []
        }

        # Check for scripts directory
        scripts_dir = os.path.join(skill_path, 'scripts')
        if os.path.isdir(scripts_dir):
            for filename in os.listdir(scripts_dir):
                filepath = os.path.join(scripts_dir, filename)
                if os.path.isfile(filepath):
                    resources['scripts'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath)
                    })

        # Check for references/reference directory
        for ref_dir_name in ['references', 'reference']:
            ref_dir = os.path.join(skill_path, ref_dir_name)
            if os.path.isdir(ref_dir):
                for filename in os.listdir(ref_dir):
                    filepath = os.path.join(ref_dir, filename)
                    if os.path.isfile(filepath):
                        resources['references'].append({
                            'filename': filename,
                            'path': filepath,
                            'size': os.path.getsize(filepath)
                        })

        # Check for assets directory
        assets_dir = os.path.join(skill_path, 'assets')
        if os.path.isdir(assets_dir):
            for filename in os.listdir(assets_dir):
                filepath = os.path.join(assets_dir, filename)
                if os.path.isfile(filepath):
                    resources['assets'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath)
                    })

        # Check for templates directory
        templates_dir = os.path.join(skill_path, 'templates')
        if os.path.isdir(templates_dir):
            for filename in os.listdir(templates_dir):
                filepath = os.path.join(templates_dir, filename)
                if os.path.isfile(filepath):
                    resources['templates'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath)
                    })

        # Also check for standalone reference files (like reference.md, forms.md)
        for filename in os.listdir(skill_path):
            if filename.endswith('.md') and filename != 'SKILL.md':
                filepath = os.path.join(skill_path, filename)
                if os.path.isfile(filepath):
                    resources['references'].append({
                        'filename': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath)
                    })

        return resources

    def _discover_skills(self, params):
        """Discover all available skills in the repository"""
        skills_path = self._get_skills_path(params)
        skills_dir = os.path.join(skills_path, 'skills')

        if not os.path.exists(skills_dir):
            return f"Error: Skills directory not found at {skills_dir}"

        skills = []

        for skill_name in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, skill_name)

            if not os.path.isdir(skill_path):
                continue

            skill_data = self._parse_skill_md(skill_path)
            if not skill_data:
                continue

            frontmatter = skill_data['frontmatter']
            resources = self._get_skill_resources(skill_path)

            skills.append({
                'name': frontmatter.get('name', skill_name),
                'dir_name': skill_name,
                'description': frontmatter.get('description', 'No description'),
                'license': frontmatter.get('license', 'Not specified'),
                'has_scripts': len(resources['scripts']) > 0,
                'has_references': len(resources['references']) > 0,
                'has_assets': len(resources['assets']) > 0,
                'has_templates': len(resources['templates']) > 0,
                'script_count': len(resources['scripts']),
                'reference_count': len(resources['references'])
            })

        # Format response
        response = f"📚 Anthropic Skills Library\n\n"
        response += f"**Repository:** {skills_path}\n"
        response += f"**Total Skills:** {len(skills)}\n\n"

        # Group by type
        doc_skills = [s for s in skills if s['dir_name'] in ['xlsx', 'docx', 'pptx', 'pdf']]
        other_skills = [s for s in skills if s['dir_name'] not in ['xlsx', 'docx', 'pptx', 'pdf']]

        if doc_skills:
            response += "## 📄 Document Skills\n\n"
            for skill in doc_skills:
                response += f"**{skill['name']}** (`{skill['dir_name']}`)\n"
                response += f"  {skill['description'][:150]}{'...' if len(skill['description']) > 150 else ''}\n"
                badges = []
                if skill['has_scripts']:
                    badges.append(f"📜 {skill['script_count']} scripts")
                if skill['has_references']:
                    badges.append(f"📖 {skill['reference_count']} refs")
                if skill['has_templates']:
                    badges.append("📋 templates")
                if badges:
                    response += f"  [{', '.join(badges)}]\n"
                response += "\n"

        if other_skills:
            response += "## 🛠️ Tool & Workflow Skills\n\n"
            for skill in other_skills:
                response += f"**{skill['name']}** (`{skill['dir_name']}`)\n"
                response += f"  {skill['description'][:150]}{'...' if len(skill['description']) > 150 else ''}\n"
                badges = []
                if skill['has_scripts']:
                    badges.append(f"📜 {skill['script_count']} scripts")
                if skill['has_references']:
                    badges.append(f"📖 {skill['reference_count']} refs")
                if skill['has_templates']:
                    badges.append("📋 templates")
                if badges:
                    response += f"  [{', '.join(badges)}]\n"
                response += "\n"

        response += "\n**Actions:**\n"
        response += "• `action='preview', skill_name='pdf'` - View skill details\n"
        response += "• `action='generate', skill_name='pdf'` - Generate agent code\n"
        response += "• `action='install', skill_name='pdf'` - Deploy to Azure storage\n"
        response += "• `action='get_skill_content', skill_name='pdf'` - Get full SKILL.md\n"

        return response

    def _preview_skill(self, params):
        """Preview a skill's details without generating"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required for preview action"

        skills_path = self._get_skills_path(params)
        skill_path = os.path.join(skills_path, 'skills', skill_name)

        if not os.path.exists(skill_path):
            return f"Error: Skill '{skill_name}' not found at {skill_path}"

        skill_data = self._parse_skill_md(skill_path)
        if not skill_data:
            return f"Error: No SKILL.md found for '{skill_name}'"

        frontmatter = skill_data['frontmatter']
        resources = self._get_skill_resources(skill_path)

        response = f"📋 Skill Preview: {frontmatter.get('name', skill_name)}\n\n"

        # Frontmatter
        response += "**Metadata:**\n"
        response += f"• Name: {frontmatter.get('name', skill_name)}\n"
        response += f"• Description: {frontmatter.get('description', 'None')}\n"
        if frontmatter.get('license'):
            response += f"• License: {frontmatter.get('license')}\n"
        response += "\n"

        # Body preview
        body_lines = skill_data['body'].split('\n')[:20]
        response += "**SKILL.md Preview (first 20 lines):**\n```markdown\n"
        response += '\n'.join(body_lines)
        if len(skill_data['body'].split('\n')) > 20:
            response += f"\n... ({len(skill_data['body'].split(chr(10)))} total lines)\n"
        response += "\n```\n\n"

        # Resources
        response += "**Bundled Resources:**\n"

        if resources['scripts']:
            response += f"\n📜 Scripts ({len(resources['scripts'])}):\n"
            for script in resources['scripts']:
                response += f"  • {script['filename']} ({script['size']} bytes)\n"

        if resources['references']:
            response += f"\n📖 References ({len(resources['references'])}):\n"
            for ref in resources['references']:
                response += f"  • {ref['filename']} ({ref['size']} bytes)\n"

        if resources['assets']:
            response += f"\n🎨 Assets ({len(resources['assets'])}):\n"
            for asset in resources['assets']:
                response += f"  • {asset['filename']} ({asset['size']} bytes)\n"

        if resources['templates']:
            response += f"\n📋 Templates ({len(resources['templates'])}):\n"
            for template in resources['templates']:
                response += f"  • {template['filename']} ({template['size']} bytes)\n"

        if not any([resources['scripts'], resources['references'], resources['assets'], resources['templates']]):
            response += "  (No bundled resources)\n"

        # Generated agent info
        response += f"\n**Generated Agent Info:**\n"
        agent_class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))
        agent_filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))
        response += f"• Class Name: {agent_class_name}\n"
        response += f"• Filename: {agent_filename}\n"
        response += f"• Agent Name: {frontmatter.get('name', skill_name).replace('-', ' ').title().replace(' ', '')}Skill\n"

        response += f"\n**Next Steps:**\n"
        response += f"• `action='generate', skill_name='{skill_name}'` - Generate agent code\n"
        response += f"• `action='install', skill_name='{skill_name}'` - Deploy to Azure\n"

        return response

    def _skill_name_to_class_name(self, skill_name):
        """Convert skill name to Python class name"""
        # Handle hyphenated names: pdf -> PdfSkillAgent, mcp-builder -> McpBuilderSkillAgent
        parts = skill_name.replace('_', '-').split('-')
        class_name = ''.join(part.capitalize() for part in parts) + 'SkillAgent'
        return class_name

    def _skill_name_to_filename(self, skill_name):
        """Convert skill name to Python filename"""
        # Handle hyphenated names: pdf -> pdf_skill_agent.py
        filename = skill_name.replace('-', '_').lower() + '_skill_agent.py'
        return filename

    def _generate_agent(self, params):
        """Generate a RAPP-compatible agent from a skill"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required for generate action"

        include_scripts = params.get('include_scripts', True)
        include_references = params.get('include_references', True)
        agent_name_override = params.get('agent_name_override')

        skills_path = self._get_skills_path(params)
        skill_path = os.path.join(skills_path, 'skills', skill_name)

        if not os.path.exists(skill_path):
            return f"Error: Skill '{skill_name}' not found at {skill_path}"

        skill_data = self._parse_skill_md(skill_path)
        if not skill_data:
            return f"Error: No SKILL.md found for '{skill_name}'"

        frontmatter = skill_data['frontmatter']
        resources = self._get_skill_resources(skill_path)

        # Generate agent code
        agent_code = self._generate_agent_code(
            skill_name=frontmatter.get('name', skill_name),
            description=frontmatter.get('description', 'No description'),
            skill_body=skill_data['body'],
            resources=resources,
            include_scripts=include_scripts,
            include_references=include_references,
            agent_name_override=agent_name_override
        )

        class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))
        filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))

        response = f"✅ Generated Agent Code\n\n"
        response += f"**Skill:** {frontmatter.get('name', skill_name)}\n"
        response += f"**Class Name:** {class_name}\n"
        response += f"**Filename:** {filename}\n"
        response += f"**Code Length:** {len(agent_code)} characters\n\n"
        response += f"**Generated Code:**\n```python\n{agent_code}\n```\n\n"
        response += f"**Deploy with:**\n"
        response += f"`action='install', skill_name='{skill_name}'`\n"

        return response

    def _generate_agent_code(self, skill_name, description, skill_body, resources,
                             include_scripts=True, include_references=True, agent_name_override=None):
        """Generate the actual Python agent code"""

        # Determine agent names
        class_name = self._skill_name_to_class_name(skill_name)
        agent_display_name = agent_name_override or (skill_name.replace('-', ' ').title().replace(' ', '') + 'Skill')

        # Build scripts dictionary
        scripts_dict = {}
        if include_scripts and resources['scripts']:
            for script in resources['scripts']:
                try:
                    with open(script['path'], 'r', encoding='utf-8') as f:
                        scripts_dict[script['filename']] = f.read()
                except Exception as e:
                    logging.warning(f"Could not read script {script['filename']}: {e}")

        # Build references dictionary
        references_dict = {}
        if include_references and resources['references']:
            for ref in resources['references']:
                try:
                    with open(ref['path'], 'r', encoding='utf-8') as f:
                        references_dict[ref['filename']] = f.read()
                except Exception as e:
                    logging.warning(f"Could not read reference {ref['filename']}: {e}")

        # Generate the agent code using string template (avoiding f-string backslash issues)
        scripts_json = json.dumps(scripts_dict, indent=8) if scripts_dict else '{}'
        references_json = json.dumps(references_dict, indent=8) if references_dict else '{}'
        description_escaped = description.replace('"', '\\"').replace('\n', ' ')
        desc_truncated = (description[:200] + ('...' if len(description) > 200 else '')).replace('\n', ' ')
        timestamp = datetime.now().isoformat()

        # Encode skill body as repr() for safe Python string literal
        skill_body_repr = repr(skill_body)

        code = '''"""
CLASS_NAME - Auto-generated from Anthropic Claude Skill 'SKILL_NAME'

This agent wraps the Claude Skill and provides RAPP-compatible interface.
Generated by SkillsLibraryAgent on TIMESTAMP
"""

from agents.basic_agent import BasicAgent
import logging
import json


class CLASS_NAME(BasicAgent):
    """
    DESC_TRUNCATED

    Auto-generated from Anthropic Claude Skill.
    """

    # Skill instruction content (from SKILL.md body)
    SKILL_INSTRUCTIONS = SKILL_BODY_REPR

    # Bundled scripts from the skill
    BUNDLED_SCRIPTS = SCRIPTS_JSON

    # Bundled reference documentation
    BUNDLED_REFERENCES = REFERENCES_JSON

    def __init__(self):
        self.name = 'AGENT_DISPLAY_NAME'
        self.metadata = {
            "name": self.name,
            "description": """DESCRIPTION_ESCAPED""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'get_instructions' (return skill instructions), 'get_script' (get a bundled script), 'get_reference' (get reference documentation), 'list_resources' (list available scripts and references), 'execute' (process a task using skill knowledge)",
                        "enum": ["get_instructions", "get_script", "get_reference", "list_resources", "execute"]
                    },
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to retrieve (for get_script action)"
                    },
                    "reference_name": {
                        "type": "string",
                        "description": "Name of the reference document to retrieve (for get_reference action)"
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task to execute using the skill's knowledge (for execute action)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context or parameters for the task"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action', 'get_instructions')

        try:
            if action == 'get_instructions':
                return self._get_instructions()
            elif action == 'get_script':
                return self._get_script(kwargs.get('script_name'))
            elif action == 'get_reference':
                return self._get_reference(kwargs.get('reference_name'))
            elif action == 'list_resources':
                return self._list_resources()
            elif action == 'execute':
                return self._execute_task(kwargs.get('task_description'), kwargs.get('context'))
            else:
                return f"Error: Unknown action '{action}'"
        except Exception as e:
            logging.error(f"Error in CLASS_NAME: {str(e)}")
            return f"Error: {str(e)}"

    def _get_instructions(self):
        """Return the skill's instruction content"""
        return f"""📚 AGENT_DISPLAY_NAME Instructions

{self.SKILL_INSTRUCTIONS}

---
**Available Resources:**
- Scripts: {', '.join(self.BUNDLED_SCRIPTS.keys()) if self.BUNDLED_SCRIPTS else 'None'}
- References: {', '.join(self.BUNDLED_REFERENCES.keys()) if self.BUNDLED_REFERENCES else 'None'}
"""

    def _get_script(self, script_name):
        """Return a bundled script by name"""
        if not script_name:
            return f"Error: script_name is required. Available: {list(self.BUNDLED_SCRIPTS.keys())}"

        if script_name not in self.BUNDLED_SCRIPTS:
            return f"Error: Script '{script_name}' not found. Available: {list(self.BUNDLED_SCRIPTS.keys())}"

        return f"""📜 Script: {script_name}

```python
{self.BUNDLED_SCRIPTS[script_name]}
```
"""

    def _get_reference(self, reference_name):
        """Return reference documentation by name"""
        if not reference_name:
            return f"Error: reference_name is required. Available: {list(self.BUNDLED_REFERENCES.keys())}"

        if reference_name not in self.BUNDLED_REFERENCES:
            return f"Error: Reference '{reference_name}' not found. Available: {list(self.BUNDLED_REFERENCES.keys())}"

        return f"""📖 Reference: {reference_name}

{self.BUNDLED_REFERENCES[reference_name]}
"""

    def _list_resources(self):
        """List all available scripts and references"""
        nl = chr(10)
        response = f"📦 AGENT_DISPLAY_NAME Resources{nl}{nl}"

        if self.BUNDLED_SCRIPTS:
            response += f"**Scripts:**{nl}"
            for name in self.BUNDLED_SCRIPTS.keys():
                response += f"  • {name}{nl}"
        else:
            response += f"**Scripts:** None{nl}"

        response += nl

        if self.BUNDLED_REFERENCES:
            response += f"**References:**{nl}"
            for name in self.BUNDLED_REFERENCES.keys():
                response += f"  • {name}{nl}"
        else:
            response += f"**References:** None{nl}"

        return response

    def _execute_task(self, task_description, context=None):
        """Provide guidance for executing a task using the skill's knowledge"""
        if not task_description:
            return "Error: task_description is required for execute action"

        instructions_preview = self.SKILL_INSTRUCTIONS[:2000]
        if len(self.SKILL_INSTRUCTIONS) > 2000:
            instructions_preview += "..."

        response = f"""🎯 Task Execution Guidance

**Task:** {task_description}

**Skill Instructions:**
{instructions_preview}

**Available Scripts:** {list(self.BUNDLED_SCRIPTS.keys()) if self.BUNDLED_SCRIPTS else 'None'}
**Available References:** {list(self.BUNDLED_REFERENCES.keys()) if self.BUNDLED_REFERENCES else 'None'}
"""

        if context:
            response += f"\\n**Additional Context:** {context}"

        return response
'''

        # Replace placeholders with actual values
        code = code.replace('CLASS_NAME', class_name)
        code = code.replace('SKILL_NAME', skill_name)
        code = code.replace('TIMESTAMP', timestamp)
        code = code.replace('DESC_TRUNCATED', desc_truncated)
        code = code.replace('SKILL_BODY_REPR', skill_body_repr)
        code = code.replace('SCRIPTS_JSON', scripts_json)
        code = code.replace('REFERENCES_JSON', references_json)
        code = code.replace('AGENT_DISPLAY_NAME', agent_display_name)
        code = code.replace('DESCRIPTION_ESCAPED', description_escaped)

        return code

    def _install_agent(self, params):
        """Generate and deploy agent to Azure storage"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required for install action"

        # Generate the agent code first
        include_scripts = params.get('include_scripts', True)
        include_references = params.get('include_references', True)
        agent_name_override = params.get('agent_name_override')

        skills_path = self._get_skills_path(params)
        skill_path = os.path.join(skills_path, 'skills', skill_name)

        if not os.path.exists(skill_path):
            return f"Error: Skill '{skill_name}' not found at {skill_path}"

        skill_data = self._parse_skill_md(skill_path)
        if not skill_data:
            return f"Error: No SKILL.md found for '{skill_name}'"

        frontmatter = skill_data['frontmatter']
        resources = self._get_skill_resources(skill_path)

        # Generate agent code
        agent_code = self._generate_agent_code(
            skill_name=frontmatter.get('name', skill_name),
            description=frontmatter.get('description', 'No description'),
            skill_body=skill_data['body'],
            resources=resources,
            include_scripts=include_scripts,
            include_references=include_references,
            agent_name_override=agent_name_override
        )

        filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))
        class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))

        # Write to Azure storage
        try:
            success = self.storage_manager.write_file('agents', filename, agent_code)
            if not success:
                return f"Error: Failed to write agent to Azure storage"
        except Exception as e:
            logging.error(f"Error storing agent: {str(e)}")
            return f"Error: Failed to save agent to storage: {str(e)}"

        # Update installation log
        try:
            log_data = self.storage_manager.read_file('agent_catalogue', 'skill_installations.json')

            if log_data:
                installations = json.loads(log_data)
            else:
                installations = {'installations': []}

            # Remove old entry if exists
            installations['installations'] = [
                a for a in installations['installations'] if a['skill_name'] != skill_name
            ]

            # Add new entry
            installations['installations'].append({
                'skill_name': skill_name,
                'class_name': class_name,
                'filename': filename,
                'installed_at': datetime.now().isoformat(),
                'source': 'skills_library',
                'description': frontmatter.get('description', 'No description')[:200],
                'scripts_included': include_scripts and len(resources['scripts']) > 0,
                'references_included': include_references and len(resources['references']) > 0,
                'script_count': len(resources['scripts']),
                'reference_count': len(resources['references'])
            })

            self.storage_manager.write_file(
                'agent_catalogue',
                'skill_installations.json',
                json.dumps(installations, indent=2)
            )
        except Exception as e:
            logging.error(f"Error updating installation log: {str(e)}")

        response = f"✅ Successfully installed skill agent!\n\n"
        response += f"**Skill:** {frontmatter.get('name', skill_name)}\n"
        response += f"**Class Name:** {class_name}\n"
        response += f"**Filename:** {filename}\n"
        response += f"**Description:** {frontmatter.get('description', 'None')[:150]}...\n\n"

        response += f"**Bundled Resources:**\n"
        if include_scripts and resources['scripts']:
            response += f"• Scripts: {len(resources['scripts'])} included\n"
        if include_references and resources['references']:
            response += f"• References: {len(resources['references'])} included\n"

        response += f"\n**Status:**\n"
        response += f"• Generated: ✅\n"
        response += f"• Saved to Azure storage: ✅\n"
        response += f"• Installation logged: ✅\n"
        response += f"• Ready to use: ✅\n"

        return response

    def _list_installed_skill_agents(self):
        """List all installed skill agents"""
        try:
            log_data = self.storage_manager.read_file('agent_catalogue', 'skill_installations.json')

            if not log_data:
                return "No skill agents have been installed yet.\n\nUse `action='discover'` to browse available skills."

            installations = json.loads(log_data)
            installed = installations.get('installations', [])

            if not installed:
                return "No skill agents have been installed yet.\n\nUse `action='discover'` to browse available skills."

            response = f"📦 Installed Skill Agents ({len(installed)})\n\n"

            for i, agent in enumerate(installed, 1):
                response += f"{i}. **{agent['skill_name']}** → `{agent['class_name']}`\n"
                response += f"   • Filename: {agent['filename']}\n"
                response += f"   • Installed: {agent['installed_at']}\n"
                if agent.get('scripts_included'):
                    response += f"   • Scripts: {agent.get('script_count', 0)} included\n"
                if agent.get('references_included'):
                    response += f"   • References: {agent.get('reference_count', 0)} included\n"
                response += "\n"

            response += f"**Management:**\n"
            response += f"• Re-install to update: `action='install', skill_name='name'`\n"
            response += f"• Browse more skills: `action='discover'`\n"

            return response
        except Exception as e:
            logging.error(f"Error listing installed skill agents: {str(e)}")
            return f"Error: {str(e)}"

    def _get_skill_content(self, params):
        """Get the full content of a SKILL.md file"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required for get_skill_content action"

        skills_path = self._get_skills_path(params)
        skill_path = os.path.join(skills_path, 'skills', skill_name)

        if not os.path.exists(skill_path):
            return f"Error: Skill '{skill_name}' not found at {skill_path}"

        skill_data = self._parse_skill_md(skill_path)
        if not skill_data:
            return f"Error: No SKILL.md found for '{skill_name}'"

        response = f"📄 Full SKILL.md Content: {skill_name}\n\n"
        response += "```markdown\n"
        response += skill_data['raw']
        response += "\n```"

        return response

    # ===========================
    # GITHUB METHODS
    # ===========================

    def _fetch_github_file(self, path):
        """Fetch a file from GitHub raw content"""
        url = f"{self.GITHUB_RAW_BASE}/{path}"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            else:
                logging.warning(f"GitHub fetch failed for {path}: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching from GitHub: {e}")
            return None

    def _list_github_directory(self, path):
        """List files in a GitHub directory using the API"""
        cache_key = f"dir:{path}"
        if cache_key in self._github_cache:
            return self._github_cache[cache_key]

        url = f"{self.GITHUB_API_BASE}/contents/{path}"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                items = response.json()
                self._github_cache[cache_key] = items
                return items
            else:
                logging.warning(f"GitHub API failed for {path}: {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"Error listing GitHub directory: {e}")
            return []

    def _parse_github_skill_md(self, skill_name):
        """Parse a SKILL.md file from GitHub"""
        content = self._fetch_github_file(f"skills/{skill_name}/SKILL.md")

        if not content:
            return None

        # Parse YAML frontmatter
        frontmatter = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError as e:
                    logging.warning(f"Failed to parse YAML frontmatter: {e}")
                body = parts[2].strip()

        return {
            'frontmatter': frontmatter,
            'body': body,
            'raw': content
        }

    def _get_github_skill_resources(self, skill_name):
        """Get bundled resources for a skill from GitHub"""
        resources = {
            'scripts': [],
            'references': [],
            'assets': [],
            'templates': []
        }

        # List skill directory contents
        items = self._list_github_directory(f"skills/{skill_name}")

        for item in items:
            if item['type'] == 'dir':
                # Check subdirectories
                if item['name'] == 'scripts':
                    script_items = self._list_github_directory(f"skills/{skill_name}/scripts")
                    for script in script_items:
                        if script['type'] == 'file':
                            resources['scripts'].append({
                                'filename': script['name'],
                                'path': script['path'],
                                'size': script.get('size', 0),
                                'download_url': script.get('download_url')
                            })
                elif item['name'] in ['references', 'reference']:
                    ref_items = self._list_github_directory(f"skills/{skill_name}/{item['name']}")
                    for ref in ref_items:
                        if ref['type'] == 'file':
                            resources['references'].append({
                                'filename': ref['name'],
                                'path': ref['path'],
                                'size': ref.get('size', 0),
                                'download_url': ref.get('download_url')
                            })
                elif item['name'] == 'assets':
                    asset_items = self._list_github_directory(f"skills/{skill_name}/assets")
                    for asset in asset_items:
                        if asset['type'] == 'file':
                            resources['assets'].append({
                                'filename': asset['name'],
                                'path': asset['path'],
                                'size': asset.get('size', 0),
                                'download_url': asset.get('download_url')
                            })
                elif item['name'] == 'templates':
                    template_items = self._list_github_directory(f"skills/{skill_name}/templates")
                    for template in template_items:
                        if template['type'] == 'file':
                            resources['templates'].append({
                                'filename': template['name'],
                                'path': template['path'],
                                'size': template.get('size', 0),
                                'download_url': template.get('download_url')
                            })
            elif item['type'] == 'file' and item['name'].endswith('.md') and item['name'] != 'SKILL.md':
                # Standalone reference files
                resources['references'].append({
                    'filename': item['name'],
                    'path': item['path'],
                    'size': item.get('size', 0),
                    'download_url': item.get('download_url')
                })

        return resources

    def _discover_github_skills(self, params):
        """Discover all available skills from GitHub"""
        items = self._list_github_directory("skills")

        if not items:
            return "Error: Unable to fetch skills list from GitHub. Check your internet connection."

        skills = []

        for item in items:
            if item['type'] != 'dir':
                continue

            skill_name = item['name']
            skill_data = self._parse_github_skill_md(skill_name)

            if not skill_data:
                continue

            frontmatter = skill_data['frontmatter']
            resources = self._get_github_skill_resources(skill_name)

            skills.append({
                'name': frontmatter.get('name', skill_name),
                'dir_name': skill_name,
                'description': frontmatter.get('description', 'No description'),
                'license': frontmatter.get('license', 'Not specified'),
                'has_scripts': len(resources['scripts']) > 0,
                'has_references': len(resources['references']) > 0,
                'has_assets': len(resources['assets']) > 0,
                'has_templates': len(resources['templates']) > 0,
                'script_count': len(resources['scripts']),
                'reference_count': len(resources['references'])
            })

        # Format response
        response = f"🌐 Anthropic Skills Library (GitHub)\n\n"
        response += f"**Repository:** https://github.com/{self.GITHUB_REPO}\n"
        response += f"**Total Skills:** {len(skills)}\n\n"

        # Group by type
        doc_skills = [s for s in skills if s['dir_name'] in ['xlsx', 'docx', 'pptx', 'pdf']]
        other_skills = [s for s in skills if s['dir_name'] not in ['xlsx', 'docx', 'pptx', 'pdf']]

        if doc_skills:
            response += "## 📄 Document Skills\n\n"
            for skill in doc_skills:
                response += f"**{skill['name']}** (`{skill['dir_name']}`)\n"
                response += f"  {skill['description'][:150]}{'...' if len(skill['description']) > 150 else ''}\n"
                badges = []
                if skill['has_scripts']:
                    badges.append(f"📜 {skill['script_count']} scripts")
                if skill['has_references']:
                    badges.append(f"📖 {skill['reference_count']} refs")
                if skill['has_templates']:
                    badges.append("📋 templates")
                if badges:
                    response += f"  [{', '.join(badges)}]\n"
                response += "\n"

        if other_skills:
            response += "## 🛠️ Tool & Workflow Skills\n\n"
            for skill in other_skills:
                response += f"**{skill['name']}** (`{skill['dir_name']}`)\n"
                response += f"  {skill['description'][:150]}{'...' if len(skill['description']) > 150 else ''}\n"
                badges = []
                if skill['has_scripts']:
                    badges.append(f"📜 {skill['script_count']} scripts")
                if skill['has_references']:
                    badges.append(f"📖 {skill['reference_count']} refs")
                if skill['has_templates']:
                    badges.append("📋 templates")
                if badges:
                    response += f"  [{', '.join(badges)}]\n"
                response += "\n"

        response += "\n**Actions (with source='github'):**\n"
        response += "• `action='preview', skill_name='algorithmic-art', source='github'`\n"
        response += "• `action='generate', skill_name='pdf', source='github'`\n"
        response += "• `action='install', skill_name='mcp-builder', source='github'`\n"
        response += "• `action='fetch_github', skill_name='skill-creator'` - Save skill locally\n"

        return response

    def _preview_github_skill(self, params):
        """Preview a skill from GitHub"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required for preview action"

        skill_data = self._parse_github_skill_md(skill_name)
        if not skill_data:
            return f"Error: Skill '{skill_name}' not found on GitHub at https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}"

        frontmatter = skill_data['frontmatter']
        resources = self._get_github_skill_resources(skill_name)

        response = f"📋 Skill Preview (GitHub): {frontmatter.get('name', skill_name)}\n\n"

        # Source info
        response += f"**Source:** https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}\n\n"

        # Frontmatter
        response += "**Metadata:**\n"
        response += f"• Name: {frontmatter.get('name', skill_name)}\n"
        response += f"• Description: {frontmatter.get('description', 'None')}\n"
        if frontmatter.get('license'):
            response += f"• License: {frontmatter.get('license')}\n"
        response += "\n"

        # Body preview
        body_lines = skill_data['body'].split('\n')[:20]
        response += "**SKILL.md Preview (first 20 lines):**\n```markdown\n"
        response += '\n'.join(body_lines)
        if len(skill_data['body'].split('\n')) > 20:
            response += f"\n... ({len(skill_data['body'].split(chr(10)))} total lines)\n"
        response += "\n```\n\n"

        # Resources
        response += "**Bundled Resources:**\n"

        if resources['scripts']:
            response += f"\n📜 Scripts ({len(resources['scripts'])}):\n"
            for script in resources['scripts']:
                response += f"  • {script['filename']} ({script['size']} bytes)\n"

        if resources['references']:
            response += f"\n📖 References ({len(resources['references'])}):\n"
            for ref in resources['references']:
                response += f"  • {ref['filename']} ({ref['size']} bytes)\n"

        if resources['assets']:
            response += f"\n🎨 Assets ({len(resources['assets'])}):\n"
            for asset in resources['assets']:
                response += f"  • {asset['filename']} ({asset['size']} bytes)\n"

        if resources['templates']:
            response += f"\n📋 Templates ({len(resources['templates'])}):\n"
            for template in resources['templates']:
                response += f"  • {template['filename']} ({template['size']} bytes)\n"

        if not any([resources['scripts'], resources['references'], resources['assets'], resources['templates']]):
            response += "  (No bundled resources)\n"

        # Generated agent info
        response += f"\n**Generated Agent Info:**\n"
        agent_class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))
        agent_filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))
        response += f"• Class Name: {agent_class_name}\n"
        response += f"• Filename: {agent_filename}\n"

        response += f"\n**Next Steps:**\n"
        response += f"• `action='generate', skill_name='{skill_name}', source='github'` - Generate code\n"
        response += f"• `action='install', skill_name='{skill_name}', source='github'` - Deploy to Azure\n"
        response += f"• `action='fetch_github', skill_name='{skill_name}'` - Save skill locally\n"

        return response

    def _get_github_skill_content(self, params):
        """Get full SKILL.md content from GitHub"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required"

        skill_data = self._parse_github_skill_md(skill_name)
        if not skill_data:
            return f"Error: Skill '{skill_name}' not found on GitHub"

        response = f"📄 Full SKILL.md Content (GitHub): {skill_name}\n\n"
        response += f"**Source:** https://github.com/{self.GITHUB_REPO}/blob/main/skills/{skill_name}/SKILL.md\n\n"
        response += "```markdown\n"
        response += skill_data['raw']
        response += "\n```"

        return response

    def _generate_agent_from_github(self, params):
        """Generate a RAPP-compatible agent from a GitHub skill"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required"

        include_scripts = params.get('include_scripts', True)
        include_references = params.get('include_references', True)
        agent_name_override = params.get('agent_name_override')

        skill_data = self._parse_github_skill_md(skill_name)
        if not skill_data:
            return f"Error: Skill '{skill_name}' not found on GitHub"

        frontmatter = skill_data['frontmatter']
        resources = self._get_github_skill_resources(skill_name)

        # Generate agent code
        agent_code = self._generate_agent_code_from_github(
            skill_name=frontmatter.get('name', skill_name),
            description=frontmatter.get('description', 'No description'),
            skill_body=skill_data['body'],
            resources=resources,
            include_scripts=include_scripts,
            include_references=include_references,
            agent_name_override=agent_name_override
        )

        class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))
        filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))

        response = f"✅ Generated Agent Code (from GitHub)\n\n"
        response += f"**Skill:** {frontmatter.get('name', skill_name)}\n"
        response += f"**Source:** https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}\n"
        response += f"**Class Name:** {class_name}\n"
        response += f"**Filename:** {filename}\n"
        response += f"**Code Length:** {len(agent_code)} characters\n\n"
        response += f"**Generated Code:**\n```python\n{agent_code}\n```\n\n"
        response += f"**Deploy with:**\n"
        response += f"`action='install', skill_name='{skill_name}', source='github'`\n"

        return response

    def _generate_agent_code_from_github(self, skill_name, description, skill_body, resources,
                                         include_scripts=True, include_references=True, agent_name_override=None):
        """Generate agent code with resources fetched from GitHub"""

        # Determine agent names
        class_name = self._skill_name_to_class_name(skill_name)
        agent_display_name = agent_name_override or (skill_name.replace('-', ' ').title().replace(' ', '') + 'Skill')

        # Build scripts dictionary by downloading from GitHub
        scripts_dict = {}
        if include_scripts and resources['scripts']:
            for script in resources['scripts']:
                try:
                    if script.get('download_url'):
                        resp = requests.get(script['download_url'], timeout=15)
                        if resp.status_code == 200:
                            scripts_dict[script['filename']] = resp.text
                    else:
                        content = self._fetch_github_file(script['path'])
                        if content:
                            scripts_dict[script['filename']] = content
                except Exception as e:
                    logging.warning(f"Could not fetch script {script['filename']}: {e}")

        # Build references dictionary by downloading from GitHub
        references_dict = {}
        if include_references and resources['references']:
            for ref in resources['references']:
                try:
                    if ref.get('download_url'):
                        resp = requests.get(ref['download_url'], timeout=15)
                        if resp.status_code == 200:
                            references_dict[ref['filename']] = resp.text
                    else:
                        content = self._fetch_github_file(ref['path'])
                        if content:
                            references_dict[ref['filename']] = content
                except Exception as e:
                    logging.warning(f"Could not fetch reference {ref['filename']}: {e}")

        # Generate the agent code using string template (avoiding f-string backslash issues)
        scripts_json = json.dumps(scripts_dict, indent=8) if scripts_dict else '{}'
        references_json = json.dumps(references_dict, indent=8) if references_dict else '{}'
        description_escaped = description.replace('"', '\\"').replace('\n', ' ')
        desc_truncated = (description[:200] + ('...' if len(description) > 200 else '')).replace('\n', ' ')
        timestamp = datetime.now().isoformat()
        github_url = f"https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}"

        # Encode skill body as repr() for safe Python string literal
        skill_body_repr = repr(skill_body)

        code = '''"""
CLASS_NAME - Auto-generated from Anthropic Claude Skill 'SKILL_NAME'

This agent wraps the Claude Skill and provides RAPP-compatible interface.
Generated by SkillsLibraryAgent on TIMESTAMP
Source: GITHUB_URL
"""

from agents.basic_agent import BasicAgent
import logging
import json


class CLASS_NAME(BasicAgent):
    """
    DESC_TRUNCATED

    Auto-generated from Anthropic Claude Skill (GitHub).
    """

    # Skill instruction content (from SKILL.md body)
    SKILL_INSTRUCTIONS = SKILL_BODY_REPR

    # Bundled scripts from the skill
    BUNDLED_SCRIPTS = SCRIPTS_JSON

    # Bundled reference documentation
    BUNDLED_REFERENCES = REFERENCES_JSON

    def __init__(self):
        self.name = 'AGENT_DISPLAY_NAME'
        self.metadata = {
            "name": self.name,
            "description": """DESCRIPTION_ESCAPED""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'get_instructions' (return skill instructions), 'get_script' (get a bundled script), 'get_reference' (get reference documentation), 'list_resources' (list available scripts and references), 'execute' (process a task using skill knowledge)",
                        "enum": ["get_instructions", "get_script", "get_reference", "list_resources", "execute"]
                    },
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to retrieve (for get_script action)"
                    },
                    "reference_name": {
                        "type": "string",
                        "description": "Name of the reference document to retrieve (for get_reference action)"
                    },
                    "task_description": {
                        "type": "string",
                        "description": "Description of the task to execute using the skill's knowledge (for execute action)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context or parameters for the task"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action', 'get_instructions')

        try:
            if action == 'get_instructions':
                return self._get_instructions()
            elif action == 'get_script':
                return self._get_script(kwargs.get('script_name'))
            elif action == 'get_reference':
                return self._get_reference(kwargs.get('reference_name'))
            elif action == 'list_resources':
                return self._list_resources()
            elif action == 'execute':
                return self._execute_task(kwargs.get('task_description'), kwargs.get('context'))
            else:
                return f"Error: Unknown action '{action}'"
        except Exception as e:
            logging.error(f"Error in CLASS_NAME: {str(e)}")
            return f"Error: {str(e)}"

    def _get_instructions(self):
        """Return the skill's instruction content"""
        return f"""📚 AGENT_DISPLAY_NAME Instructions

{self.SKILL_INSTRUCTIONS}

---
**Available Resources:**
- Scripts: {', '.join(self.BUNDLED_SCRIPTS.keys()) if self.BUNDLED_SCRIPTS else 'None'}
- References: {', '.join(self.BUNDLED_REFERENCES.keys()) if self.BUNDLED_REFERENCES else 'None'}
"""

    def _get_script(self, script_name):
        """Return a bundled script by name"""
        if not script_name:
            return f"Error: script_name is required. Available: {list(self.BUNDLED_SCRIPTS.keys())}"

        if script_name not in self.BUNDLED_SCRIPTS:
            return f"Error: Script '{script_name}' not found. Available: {list(self.BUNDLED_SCRIPTS.keys())}"

        return f"""📜 Script: {script_name}

```python
{self.BUNDLED_SCRIPTS[script_name]}
```
"""

    def _get_reference(self, reference_name):
        """Return reference documentation by name"""
        if not reference_name:
            return f"Error: reference_name is required. Available: {list(self.BUNDLED_REFERENCES.keys())}"

        if reference_name not in self.BUNDLED_REFERENCES:
            return f"Error: Reference '{reference_name}' not found. Available: {list(self.BUNDLED_REFERENCES.keys())}"

        return f"""📖 Reference: {reference_name}

{self.BUNDLED_REFERENCES[reference_name]}
"""

    def _list_resources(self):
        """List all available scripts and references"""
        nl = chr(10)
        response = f"📦 AGENT_DISPLAY_NAME Resources{nl}{nl}"

        if self.BUNDLED_SCRIPTS:
            response += f"**Scripts:**{nl}"
            for name in self.BUNDLED_SCRIPTS.keys():
                response += f"  • {name}{nl}"
        else:
            response += f"**Scripts:** None{nl}"

        response += nl

        if self.BUNDLED_REFERENCES:
            response += f"**References:**{nl}"
            for name in self.BUNDLED_REFERENCES.keys():
                response += f"  • {name}{nl}"
        else:
            response += f"**References:** None{nl}"

        return response

    def _execute_task(self, task_description, context=None):
        """Provide guidance for executing a task using the skill's knowledge"""
        if not task_description:
            return "Error: task_description is required for execute action"

        instructions_preview = self.SKILL_INSTRUCTIONS[:2000]
        if len(self.SKILL_INSTRUCTIONS) > 2000:
            instructions_preview += "..."

        response = f"""🎯 Task Execution Guidance

**Task:** {task_description}

**Skill Instructions:**
{instructions_preview}

**Available Scripts:** {list(self.BUNDLED_SCRIPTS.keys()) if self.BUNDLED_SCRIPTS else 'None'}
**Available References:** {list(self.BUNDLED_REFERENCES.keys()) if self.BUNDLED_REFERENCES else 'None'}
"""

        if context:
            response += f"\\n**Additional Context:** {context}"

        return response
'''

        # Replace placeholders with actual values
        code = code.replace('CLASS_NAME', class_name)
        code = code.replace('SKILL_NAME', skill_name)
        code = code.replace('TIMESTAMP', timestamp)
        code = code.replace('GITHUB_URL', github_url)
        code = code.replace('DESC_TRUNCATED', desc_truncated)
        code = code.replace('SKILL_BODY_REPR', skill_body_repr)
        code = code.replace('SCRIPTS_JSON', scripts_json)
        code = code.replace('REFERENCES_JSON', references_json)
        code = code.replace('AGENT_DISPLAY_NAME', agent_display_name)
        code = code.replace('DESCRIPTION_ESCAPED', description_escaped)

        return code

    def _install_agent_from_github(self, params):
        """Generate and deploy agent from GitHub to Azure storage"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required"

        include_scripts = params.get('include_scripts', True)
        include_references = params.get('include_references', True)
        agent_name_override = params.get('agent_name_override')

        skill_data = self._parse_github_skill_md(skill_name)
        if not skill_data:
            return f"Error: Skill '{skill_name}' not found on GitHub"

        frontmatter = skill_data['frontmatter']
        resources = self._get_github_skill_resources(skill_name)

        # Generate agent code
        agent_code = self._generate_agent_code_from_github(
            skill_name=frontmatter.get('name', skill_name),
            description=frontmatter.get('description', 'No description'),
            skill_body=skill_data['body'],
            resources=resources,
            include_scripts=include_scripts,
            include_references=include_references,
            agent_name_override=agent_name_override
        )

        filename = self._skill_name_to_filename(frontmatter.get('name', skill_name))
        class_name = self._skill_name_to_class_name(frontmatter.get('name', skill_name))

        # Write to Azure storage
        try:
            success = self.storage_manager.write_file('agents', filename, agent_code)
            if not success:
                return f"Error: Failed to write agent to Azure storage"
        except Exception as e:
            logging.error(f"Error storing agent: {str(e)}")
            return f"Error: Failed to save agent to storage: {str(e)}"

        # Update installation log
        try:
            log_data = self.storage_manager.read_file('agent_catalogue', 'skill_installations.json')

            if log_data:
                installations = json.loads(log_data)
            else:
                installations = {'installations': []}

            # Remove old entry if exists
            installations['installations'] = [
                a for a in installations['installations'] if a['skill_name'] != skill_name
            ]

            # Add new entry
            installations['installations'].append({
                'skill_name': skill_name,
                'class_name': class_name,
                'filename': filename,
                'installed_at': datetime.now().isoformat(),
                'source': 'github',
                'github_url': f"https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}",
                'description': frontmatter.get('description', 'No description')[:200],
                'scripts_included': include_scripts and len(resources['scripts']) > 0,
                'references_included': include_references and len(resources['references']) > 0,
                'script_count': len(resources['scripts']),
                'reference_count': len(resources['references'])
            })

            self.storage_manager.write_file(
                'agent_catalogue',
                'skill_installations.json',
                json.dumps(installations, indent=2)
            )
        except Exception as e:
            logging.error(f"Error updating installation log: {str(e)}")

        response = f"✅ Successfully installed skill agent from GitHub!\n\n"
        response += f"**Skill:** {frontmatter.get('name', skill_name)}\n"
        response += f"**Source:** https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}\n"
        response += f"**Class Name:** {class_name}\n"
        response += f"**Filename:** {filename}\n"
        response += f"**Description:** {frontmatter.get('description', 'None')[:150]}...\n\n"

        response += f"**Bundled Resources (fetched from GitHub):**\n"
        if include_scripts and resources['scripts']:
            response += f"• Scripts: {len(resources['scripts'])} downloaded\n"
        if include_references and resources['references']:
            response += f"• References: {len(resources['references'])} downloaded\n"

        response += f"\n**Status:**\n"
        response += f"• Fetched from GitHub: ✅\n"
        response += f"• Scripts downloaded: ✅\n"
        response += f"• References downloaded: ✅\n"
        response += f"• Saved to Azure storage: ✅\n"
        response += f"• Installation logged: ✅\n"
        response += f"• Ready to use: ✅\n"

        return response

    def _fetch_github_skill(self, params):
        """Fetch a skill from GitHub and save it locally"""
        skill_name = params.get('skill_name')
        if not skill_name:
            return "Error: skill_name is required"

        skill_data = self._parse_github_skill_md(skill_name)
        if not skill_data:
            return f"Error: Skill '{skill_name}' not found on GitHub"

        # Create local skill directory
        local_skills_path = self._get_skills_path(params)
        local_skill_path = os.path.join(local_skills_path, 'skills', skill_name)

        try:
            os.makedirs(local_skill_path, exist_ok=True)

            # Save SKILL.md
            skill_md_path = os.path.join(local_skill_path, 'SKILL.md')
            with open(skill_md_path, 'w', encoding='utf-8') as f:
                f.write(skill_data['raw'])

            # Fetch and save resources
            resources = self._get_github_skill_resources(skill_name)
            saved_files = ['SKILL.md']

            # Save scripts
            if resources['scripts']:
                scripts_dir = os.path.join(local_skill_path, 'scripts')
                os.makedirs(scripts_dir, exist_ok=True)
                for script in resources['scripts']:
                    content = None
                    if script.get('download_url'):
                        resp = requests.get(script['download_url'], timeout=15)
                        if resp.status_code == 200:
                            content = resp.text
                    else:
                        content = self._fetch_github_file(script['path'])

                    if content:
                        filepath = os.path.join(scripts_dir, script['filename'])
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        saved_files.append(f"scripts/{script['filename']}")

            # Save references
            if resources['references']:
                # Check if any refs are in a subdirectory
                ref_in_subdir = any('/' in r['path'].replace(f'skills/{skill_name}/', '') for r in resources['references'])
                if ref_in_subdir:
                    refs_dir = os.path.join(local_skill_path, 'references')
                    os.makedirs(refs_dir, exist_ok=True)

                for ref in resources['references']:
                    content = None
                    if ref.get('download_url'):
                        resp = requests.get(ref['download_url'], timeout=15)
                        if resp.status_code == 200:
                            content = resp.text
                    else:
                        content = self._fetch_github_file(ref['path'])

                    if content:
                        # Determine if it goes in root or references subdir
                        relative_path = ref['path'].replace(f'skills/{skill_name}/', '')
                        if '/' in relative_path:
                            filepath = os.path.join(local_skill_path, relative_path)
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        else:
                            filepath = os.path.join(local_skill_path, ref['filename'])

                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        saved_files.append(relative_path)

            # Save templates
            if resources['templates']:
                templates_dir = os.path.join(local_skill_path, 'templates')
                os.makedirs(templates_dir, exist_ok=True)
                for template in resources['templates']:
                    content = None
                    if template.get('download_url'):
                        resp = requests.get(template['download_url'], timeout=15)
                        if resp.status_code == 200:
                            content = resp.text
                    else:
                        content = self._fetch_github_file(template['path'])

                    if content:
                        filepath = os.path.join(templates_dir, template['filename'])
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        saved_files.append(f"templates/{template['filename']}")

            frontmatter = skill_data['frontmatter']

            response = f"✅ Successfully fetched skill from GitHub!\n\n"
            response += f"**Skill:** {frontmatter.get('name', skill_name)}\n"
            response += f"**Source:** https://github.com/{self.GITHUB_REPO}/tree/main/skills/{skill_name}\n"
            response += f"**Saved to:** {local_skill_path}\n\n"

            response += f"**Files Saved ({len(saved_files)}):**\n"
            for f in saved_files[:20]:
                response += f"  • {f}\n"
            if len(saved_files) > 20:
                response += f"  ... and {len(saved_files) - 20} more files\n"

            response += f"\n**Next Steps:**\n"
            response += f"• `action='preview', skill_name='{skill_name}'` - Preview locally\n"
            response += f"• `action='install', skill_name='{skill_name}'` - Deploy to Azure\n"

            return response

        except Exception as e:
            logging.error(f"Error fetching skill from GitHub: {str(e)}")
            return f"Error: Failed to save skill locally: {str(e)}"
