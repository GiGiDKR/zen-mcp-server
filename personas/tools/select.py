"""
Outil MCP pour sélectionner et activer des personas.

Ce module fournit l'outil PersonasSelectTool qui permet aux utilisateurs
de sélectionner des personas pour usage dans d'autres outils.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from tools.simple.base import SimpleTool

from ..exceptions import handle_persona_error
from ..manager import PersonaManager


class PersonasSelectRequest(BaseModel):
    """Request model pour l'outil personas_select"""

    id: str = Field(..., min_length=1, max_length=100, description="Identifiant du persona à sélectionner")
    show_usage_examples: bool = Field(default=True, description="Afficher des exemples d'utilisation du persona")


class PersonasSelectTool(SimpleTool):
    """
    Outil pour sélectionner et activer des personas.

    Cet outil permet aux utilisateurs de:
    - Sélectionner un persona pour utilisation
    - Voir les détails du persona sélectionné
    - Obtenir des exemples d'utilisation
    - Valider que le persona est disponible
    """

    def get_name(self) -> str:
        return "personas_select"

    def get_description(self) -> str:
        return (
            "PERSONAS SELECT - Select and activate a persona for use in "
            "other tools. Shows persona details, model preferences, and "
            "provides usage examples. Use this tool to understand how to "
            "apply a specific persona to your tasks and get the exact "
            "parameter format needed."
        )

    def get_system_prompt(self) -> str:
        return """You are a persona selection assistant. Your job is to help \
users understand and apply personas to their tasks.

When selecting personas, provide:
1. Clear confirmation of the selected persona
2. Detailed explanation of the persona's capabilities
3. Practical usage examples with exact syntax
4. Guidance on when to use this persona vs others

Be helpful in explaining how the persona will change the AI's behavior."""

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Define the tool-specific fields for personas_select"""
        return {
            "id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "description": "Identifier of the persona to select",
            },
            "show_usage_examples": {
                "type": "boolean",
                "default": True,
                "description": "Show practical usage examples for the persona",
            },
        }

    def get_required_fields(self) -> list[str]:
        """Required fields for selecting a persona"""
        return ["id"]

    def get_request_model(self):
        """Return the request model for validation"""
        return PersonasSelectRequest

    async def prepare_prompt(self, request: PersonasSelectRequest) -> str:
        """Prepare the prompt for the AI model"""
        try:
            # Get persona manager
            manager = PersonaManager.get_instance()

            # Check if persona exists
            if not manager.exists(request.id):
                # Show available personas as suggestions
                all_personas = manager.list_personas()
                suggestions = []
                for persona in all_personas[:5]:  # Show top 5 suggestions
                    suggestions.append(f"• {persona.id} - {persona.name}")

                return f"""ERROR: Persona '{request.id}' does not exist.

=== AVAILABLE PERSONAS ===
{chr(10).join(suggestions) if suggestions else "No personas available"}

Use the personas_list tool to see all available personas."""

            # Get persona details
            persona = manager.get_persona(request.id)

            # Check if it's predefined
            from ..models import PREDEFINED_PERSONAS

            is_predefined = request.id in {p["id"] for p in PREDEFINED_PERSONAS}

            prompt = f"""✅ PERSONA SELECTED SUCCESSFULLY

=== SELECTED PERSONA ===
**ID:** {persona.id}
**Name:** {persona.name}
**Description:** {persona.description}
**Type:** {"Predefined" if is_predefined else "Custom"}
**Tags:** {", ".join(persona.tags) if persona.tags else "None"}

=== PERSONA CHARACTERISTICS ===
{persona.system_instructions[:200]}{"..." if len(persona.system_instructions) > 200 else ""}

=== MODEL PREFERENCES ===
- **Preferred Model:** {persona.model_preferences.model_name or "Default"}
- **Temperature:** {persona.model_preferences.temperature or "Default"}
- **Thinking Mode:** {persona.model_preferences.thinking_mode or "Default"}
- **Top-p:** {persona.model_preferences.top_p or "Default"}
- **Max Tokens:** {persona.model_preferences.max_tokens or "Default"}"""

            if request.show_usage_examples:
                prompt += f"""

=== HOW TO USE THIS PERSONA ===

**Basic Usage:** Add this parameter to any tool call:
```json
"persona_id": "{persona.id}"
```

**Example with Chat Tool:**
```json
{{
  "prompt": "Help me design a scalable web architecture",
  "persona_id": "{persona.id}"
}}
```

**Example with Analysis Tool:**
```json
{{
  "step": "Analyze this code for security issues",
  "persona_id": "{persona.id}",
  "files": ["src/auth.py"]
}}
```

**What This Persona Will Do:**
- Apply specialized system instructions for better context
- Use preferred model settings for optimal performance
- Provide responses tailored to the persona's expertise domain

**Best Used For:**
{", ".join(persona.tags) if persona.tags else "General purpose tasks"}"""

            prompt += f"""

=== PERSONA INFO ===
- Created: {persona.created_at.strftime("%Y-%m-%d %H:%M")}
- Last Updated: {persona.updated_at.strftime("%Y-%m-%d %H:%M")}
- Version: {persona.version}

Please explain to the user how to use this persona and what to expect \
from it."""

            return prompt

        except Exception as e:
            error_msg = handle_persona_error(e)
            return f"Error selecting persona: {error_msg}"

    def format_response(self, response: str, request: PersonasSelectRequest, model_info: Optional[dict] = None) -> str:
        """Format the AI response"""
        return response
