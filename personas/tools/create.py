"""
Outil MCP pour créer de nouveaux personas.

Ce module fournit l'outil PersonasCreateTool qui permet aux utilisateurs
de créer de nouveaux personas avec validation complète.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from tools.simple.base import SimpleTool

from ..exceptions import handle_persona_error
from ..manager import PersonaManager
from ..models import ModelPreferences, Persona


class PersonasCreateRequest(BaseModel):
    """Request model pour l'outil personas_create"""

    id: str = Field(
        ..., min_length=1, max_length=100, description="Identifiant unique du persona (alphanumeric + underscore)"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Nom d'affichage du persona")
    description: str = Field(..., min_length=1, max_length=500, description="Description courte du persona")
    system_instructions: str = Field(
        ..., min_length=10, max_length=10000, description="Instructions système personnalisées"
    )
    model_name: Optional[str] = Field(None, description="Nom du modèle préféré (ex: 'gemini-2.5-pro', 'flash')")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Température pour contrôler la créativité du modèle"
    )
    thinking_mode: Optional[str] = Field(None, description="Mode de réflexion (minimal, low, medium, high, max)")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags pour catégorisation et recherche")


class PersonasCreateTool(SimpleTool):
    """
    Outil pour créer de nouveaux personas.

    Cet outil permet aux utilisateurs de:
    - Créer des personas avec validation complète
    - Configurer les préférences de modèle
    - Ajouter des tags pour organisation
    - Valider l'unicité des IDs
    """

    def get_name(self) -> str:
        return "personas_create"

    def get_description(self) -> str:
        return (
            "PERSONAS CREATE - Create a new persona with custom system "
            "instructions and model preferences. Allows defining specialized "
            "AI personalities for different roles, expertise domains, or "
            "specific use cases. Validates persona data and ensures ID "
            "uniqueness before creation."
        )

    def get_system_prompt(self) -> str:
        return """You are a persona creation assistant. Your job is to help \
users create well-defined personas for specialized AI interactions.

When creating personas, provide:
1. Confirmation of successful creation with details
2. Guidance on how to use the new persona
3. Suggestions for improvement if needed
4. Information about validation results

Be encouraging and helpful in explaining the persona creation process."""

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Define the tool-specific fields for personas_create"""
        return {
            "id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "description": "Unique identifier for the persona (alphanumeric + underscore)",
            },
            "name": {"type": "string", "minLength": 1, "maxLength": 200, "description": "Display name of the persona"},
            "description": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500,
                "description": "Short description of the persona",
            },
            "system_instructions": {
                "type": "string",
                "minLength": 10,
                "maxLength": 10000,
                "description": "Custom system instructions for the persona",
            },
            "model_name": {"type": "string", "description": "Preferred model name (e.g., 'gemini-2.5-pro', 'flash')"},
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Temperature to control model creativity",
            },
            "thinking_mode": {
                "type": "string",
                "enum": ["minimal", "low", "medium", "high", "max"],
                "description": "Thinking mode (minimal, low, medium, high, max)",
            },
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization and search"},
        }

    def get_required_fields(self) -> list[str]:
        """Required fields for creating a persona"""
        return ["id", "name", "description", "system_instructions"]

    def get_request_model(self):
        """Return the request model for validation"""
        return PersonasCreateRequest

    async def prepare_prompt(self, request: PersonasCreateRequest) -> str:
        """Prepare the prompt for the AI model"""
        try:
            # Get persona manager
            manager = PersonaManager.get_instance()

            # Check if persona already exists
            if manager.exists(request.id):
                return f"""ERROR: A persona with ID '{request.id}' already exists.
Please choose a different ID and try again.

Use the personas_list tool to see existing personas."""

            # Create model preferences
            model_prefs = ModelPreferences(
                model_name=request.model_name, temperature=request.temperature, thinking_mode=request.thinking_mode
            )

            # Create the persona
            persona = Persona(
                id=request.id,
                name=request.name,
                description=request.description,
                system_instructions=request.system_instructions,
                model_preferences=model_prefs,
                tags=request.tags or [],
            )

            # Save the persona
            success = manager.create_persona(persona)

            if success:
                # Get stats for context
                stats = manager.get_stats()

                prompt = f"""Please confirm the successful creation of the new persona:

=== PERSONA CREATED SUCCESSFULLY ===
**ID:** {persona.id}
**Name:** {persona.name}
**Description:** {persona.description}
**Tags:** {", ".join(persona.tags) if persona.tags else "None"}

=== SYSTEM INSTRUCTIONS ===
{persona.system_instructions}

=== MODEL PREFERENCES ===
- Model: {persona.model_preferences.model_name or "Default"}
- Temperature: {persona.model_preferences.temperature or "Default"}
- Thinking Mode: {persona.model_preferences.thinking_mode or "Default"}

=== CREATION INFO ===
- Created: {persona.created_at.strftime("%Y-%m-%d %H:%M:%S")}
- Version: {persona.version}

=== USAGE INSTRUCTIONS ===
To use this persona, add `"persona_id": "{persona.id}"` to any tool call.

=== MANAGER STATS ===
- Total personas: {len(manager._personas_cache)}
- Created this session: {stats["personas_created"]}

Please provide a friendly confirmation and explain how the user can start \
using their new persona."""

                return prompt
            else:
                return f"""ERROR: Failed to create persona '{request.id}'.
This could be due to validation errors or storage issues.
Please check your input and try again."""

        except Exception as e:
            error_msg = handle_persona_error(e)
            return f"Error creating persona: {error_msg}"

    def format_response(self, response: str, request: PersonasCreateRequest, model_info: Optional[dict] = None) -> str:
        """Format the AI response"""
        return response
