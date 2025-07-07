"""
Outil MCP pour supprimer des personas existants.

Ce module fournit l'outil PersonasDeleteTool qui permet aux utilisateurs
de supprimer des personas avec confirmations de sécurité.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from tools.simple.base import SimpleTool

from ..exceptions import handle_persona_error
from ..manager import PersonaManager


class PersonasDeleteRequest(BaseModel):
    """Request model pour l'outil personas_delete"""

    id: str = Field(..., min_length=1, max_length=100, description="Identifiant du persona à supprimer")
    confirm: bool = Field(default=False, description="Confirmation explicite de suppression (sécurité)")


class PersonasDeleteTool(SimpleTool):
    """
    Outil pour supprimer des personas existants.

    Cet outil permet aux utilisateurs de:
    - Supprimer des personas avec confirmation
    - Protéger contre les suppressions accidentelles
    - Afficher des informations avant suppression
    - Gérer les personas prédéfinis
    """

    def get_name(self) -> str:
        return "personas_delete"

    def get_description(self) -> str:
        return (
            "PERSONAS DELETE - Safely delete an existing persona with "
            "confirmation. Requires explicit confirmation to prevent "
            "accidental deletions. Shows persona details before deletion "
            "and handles predefined personas appropriately. Use with caution "
            "as this action cannot be undone."
        )

    def get_system_prompt(self) -> str:
        return """You are a persona deletion assistant. Your job is to help \
users safely delete personas with appropriate warnings and confirmations.

When handling deletion requests, provide:
1. Clear warnings about permanent deletion
2. Persona details before deletion for confirmation
3. Instructions for confirming deletion
4. Alternatives when appropriate (like updating instead)

Always emphasize the permanent nature of deletion and ask for explicit \
confirmation."""

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Define the tool-specific fields for personas_delete"""
        return {
            "id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "description": "Identifier of the persona to delete",
            },
            "confirm": {
                "type": "boolean",
                "default": False,
                "description": "Explicit confirmation of deletion (required for safety)",
            },
        }

    def get_required_fields(self) -> list[str]:
        """Required fields for deleting a persona"""
        return ["id"]

    def get_request_model(self):
        """Return the request model for validation"""
        return PersonasDeleteRequest

    async def prepare_prompt(self, request: PersonasDeleteRequest) -> str:
        """Prepare the prompt for the AI model"""
        try:
            # Get persona manager
            manager = PersonaManager.get_instance()

            # Check if persona exists
            if not manager.exists(request.id):
                return f"""ERROR: Persona '{request.id}' does not exist.
Use the personas_list tool to see available personas."""

            # Get persona details
            persona = manager.get_persona(request.id)

            # Check if it's a predefined persona
            from ..models import PREDEFINED_PERSONAS

            is_predefined = request.id in {p["id"] for p in PREDEFINED_PERSONAS}

            # If not confirmed, show warning and persona details
            if not request.confirm:
                prompt = f"""⚠️  DELETION CONFIRMATION REQUIRED ⚠️

You are about to delete the following persona:

=== PERSONA TO DELETE ===
**ID:** {persona.id}
**Name:** {persona.name}
**Description:** {persona.description}
**Tags:** {", ".join(persona.tags) if persona.tags else "None"}
**Created:** {persona.created_at.strftime("%Y-%m-%d %H:%M:%S")}
**Updated:** {persona.updated_at.strftime("%Y-%m-%d %H:%M:%S")}"""

                if is_predefined:
                    prompt += """

⚠️  **WARNING: This is a predefined persona!**
Predefined personas will be recreated automatically on next server restart.
Consider updating instead of deleting if you want to modify it."""

                prompt += f"""

=== IMPORTANT WARNINGS ===
🚨 **This action CANNOT be undone!**
🚨 **All persona data will be permanently lost!**
🚨 **Any configurations using this persona will stop working!**

=== TO PROCEED WITH DELETION ===
Call this tool again with: {{"id": "{request.id}", "confirm": true}}

=== ALTERNATIVES ===
- Use 'personas_update' to modify the persona instead
- Use 'personas_list' to find other similar personas
- Consider backing up the persona data manually

Please provide these warnings and instructions to the user."""

                return prompt

            # Confirmed deletion - proceed
            success = manager.delete_persona(request.id)

            if success:
                stats = manager.get_stats()

                prompt = f"""✅ PERSONA DELETED SUCCESSFULLY

=== DELETION CONFIRMED ===
**Persona ID:** {request.id}
**Name:** {persona.name}
**Deletion Time:** {persona.updated_at.strftime("%Y-%m-%d %H:%M:%S")}"""

                if is_predefined:
                    prompt += """

ℹ️  **Note:** This was a predefined persona that will be recreated on \
next server restart."""

                prompt += f"""

=== MANAGER STATS ===
- Total personas remaining: {len(manager._personas_cache)}
- Deleted this session: {stats["personas_deleted"]}

The persona has been permanently removed from the system. Any tool calls \
that previously used persona_id="{request.id}" will now use default behavior.

Please confirm the successful deletion to the user."""

                return prompt
            else:
                return f"""ERROR: Failed to delete persona '{request.id}'.
This could be due to storage issues or the persona being in use."""

        except Exception as e:
            error_msg = handle_persona_error(e)
            return f"Error deleting persona: {error_msg}"

    def format_response(self, response: str, request: PersonasDeleteRequest, model_info: Optional[dict] = None) -> str:
        """Format the AI response"""
        return response
