"""
Outil MCP pour mettre à jour des personas existants.

Ce module fournit l'outil PersonasUpdateTool qui permet aux utilisateurs
de modifier des personas existants avec gestion des conflits.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from tools.simple.base import SimpleTool

from ..exceptions import handle_persona_error
from ..manager import PersonaManager


class PersonasUpdateRequest(BaseModel):
    """Request model pour l'outil personas_update"""

    id: str = Field(..., min_length=1, max_length=100, description="Identifiant du persona à mettre à jour")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Nouveau nom d'affichage du persona")
    description: Optional[str] = Field(
        None, min_length=1, max_length=500, description="Nouvelle description courte du persona"
    )
    system_instructions: Optional[str] = Field(
        None, min_length=10, max_length=10000, description="Nouvelles instructions système personnalisées"
    )
    model_name: Optional[str] = Field(None, description="Nouveau nom du modèle préféré")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Nouvelle température pour contrôler la créativité"
    )
    thinking_mode: Optional[str] = Field(None, description="Nouveau mode de réflexion")
    add_tags: Optional[list[str]] = Field(default_factory=list, description="Tags à ajouter")
    remove_tags: Optional[list[str]] = Field(default_factory=list, description="Tags à supprimer")


class PersonasUpdateTool(SimpleTool):
    """
    Outil pour mettre à jour des personas existants.

    Cet outil permet aux utilisateurs de:
    - Modifier les propriétés d'un persona existant
    - Mettre à jour les préférences de modèle
    - Ajouter ou supprimer des tags
    - Gérer les conflits de version
    """

    def get_name(self) -> str:
        return "personas_update"

    def get_description(self) -> str:
        return (
            "PERSONAS UPDATE - Update an existing persona's properties, "
            "including name, description, system instructions, model "
            "preferences, and tags. Supports partial updates and handles "
            "version conflicts. Use this tool to refine and improve "
            "existing personas."
        )

    def get_system_prompt(self) -> str:
        return """You are a persona update assistant. Your job is to help \
users modify and improve their existing personas.

When updating personas, provide:
1. Clear confirmation of changes made
2. Before/after comparison when helpful
3. Information about any validation issues
4. Guidance on testing the updated persona

Be helpful in explaining what was changed and how it affects the persona."""

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Define the tool-specific fields for personas_update"""
        return {
            "id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "description": "Identifier of the persona to update",
            },
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200,
                "description": "New display name of the persona",
            },
            "description": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500,
                "description": "New short description of the persona",
            },
            "system_instructions": {
                "type": "string",
                "minLength": 10,
                "maxLength": 10000,
                "description": "New custom system instructions for the persona",
            },
            "model_name": {"type": "string", "description": "New preferred model name"},
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "New temperature to control model creativity",
            },
            "thinking_mode": {
                "type": "string",
                "enum": ["minimal", "low", "medium", "high", "max"],
                "description": "New thinking mode",
            },
            "add_tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to add to the persona"},
            "remove_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags to remove from the persona",
            },
        }

    def get_required_fields(self) -> list[str]:
        """Required fields for updating a persona"""
        return ["id"]

    def get_request_model(self):
        """Return the request model for validation"""
        return PersonasUpdateRequest

    async def prepare_prompt(self, request: PersonasUpdateRequest) -> str:
        """Prepare the prompt for the AI model"""
        try:
            # Get persona manager
            manager = PersonaManager.get_instance()

            # Check if persona exists
            if not manager.exists(request.id):
                return f"""ERROR: Persona '{request.id}' does not exist.
Use the personas_list tool to see available personas."""

            # Get current persona for comparison
            current_persona = manager.get_persona(request.id)

            # Track changes
            changes = []
            update_data = {}

            # Check each field for changes
            if request.name is not None and request.name != current_persona.name:
                changes.append(f"Name: '{current_persona.name}' → '{request.name}'")
                update_data["name"] = request.name

            if request.description is not None and request.description != current_persona.description:
                changes.append(f"Description: '{current_persona.description}' → '{request.description}'")
                update_data["description"] = request.description

            if (
                request.system_instructions is not None
                and request.system_instructions != current_persona.system_instructions
            ):
                changes.append("System instructions: Updated")
                update_data["system_instructions"] = request.system_instructions

            # Model preferences changes
            model_changes = {}
            current_prefs = current_persona.model_preferences

            if request.model_name is not None and request.model_name != current_prefs.model_name:
                changes.append(f"Model: '{current_prefs.model_name}' → '{request.model_name}'")
                model_changes["model_name"] = request.model_name

            if request.temperature is not None and request.temperature != current_prefs.temperature:
                changes.append(f"Temperature: {current_prefs.temperature} → {request.temperature}")
                model_changes["temperature"] = request.temperature

            if request.thinking_mode is not None and request.thinking_mode != current_prefs.thinking_mode:
                changes.append(f"Thinking mode: '{current_prefs.thinking_mode}' → '{request.thinking_mode}'")
                model_changes["thinking_mode"] = request.thinking_mode

            if model_changes:
                update_data["model_preferences"] = model_changes

            # Handle tags
            if request.add_tags:
                for tag in request.add_tags:
                    if tag not in current_persona.tags:
                        changes.append(f"Added tag: '{tag}'")

            if request.remove_tags:
                for tag in request.remove_tags:
                    if tag in current_persona.tags:
                        changes.append(f"Removed tag: '{tag}'")

            # Check if any changes were made
            if not changes and not request.add_tags and not request.remove_tags:
                return f"""No changes detected for persona '{request.id}'.
The provided values match the current persona configuration."""

            # Perform the update
            success = manager.update_persona(
                request.id, update_data, add_tags=request.add_tags or [], remove_tags=request.remove_tags or []
            )

            if success:
                # Get updated persona
                updated_persona = manager.get_persona(request.id)
                stats = manager.get_stats()

                prompt = f"""Please confirm the successful update of the persona:

=== PERSONA UPDATED SUCCESSFULLY ===
**ID:** {updated_persona.id}
**Name:** {updated_persona.name}
**Description:** {updated_persona.description}

=== CHANGES MADE ===
{chr(10).join(f"• {change}" for change in changes)}

=== CURRENT CONFIGURATION ===
**Tags:** {", ".join(updated_persona.tags) if updated_persona.tags else "None"}
**Model:** {updated_persona.model_preferences.model_name or "Default"}
**Temperature:** {updated_persona.model_preferences.temperature or "Default"}
**Thinking Mode:** {updated_persona.model_preferences.thinking_mode or "Default"}

=== UPDATE INFO ===
- Updated: {updated_persona.updated_at.strftime("%Y-%m-%d %H:%M:%S")}
- Version: {updated_persona.version}

=== MANAGER STATS ===
- Total personas: {len(manager._personas_cache)}
- Updated this session: {stats["personas_updated"]}

Please provide a friendly confirmation of the updates and any recommendations \
for testing the modified persona."""

                return prompt
            else:
                return f"""ERROR: Failed to update persona '{request.id}'.
This could be due to validation errors or storage issues."""

        except Exception as e:
            error_msg = handle_persona_error(e)
            return f"Error updating persona: {error_msg}"

    def format_response(self, response: str, request: PersonasUpdateRequest, model_info: Optional[dict] = None) -> str:
        """Format the AI response"""
        return response
