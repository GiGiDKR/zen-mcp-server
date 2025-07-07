"""
Outil MCP pour lister les personas disponibles.

Ce module fournit l'outil PersonasListTool qui permet aux utilisateurs
de voir tous les personas disponibles avec filtrage et pagination optionnels.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from tools.simple.base import SimpleTool

from ..exceptions import handle_persona_error
from ..manager import PersonaManager
from ..models import PREDEFINED_PERSONAS, PersonaSearchFilters


class PersonasListRequest(BaseModel):
    """Request model pour l'outil personas_list"""

    tags_filter: Optional[list[str]] = Field(
        None, description="Filtrer par tags (liste). Retourne les personas ayant au moins un de ces tags."
    )
    name_filter: Optional[str] = Field(None, description="Filtrer par nom (recherche partielle, insensible à la casse)")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Nombre maximum de personas à retourner (1-100)")
    include_predefined: bool = Field(True, description="Inclure les personas prédéfinis dans les résultats")


class PersonasListTool(SimpleTool):
    """
    Outil pour lister les personas disponibles avec filtrage optionnel.

    Cet outil permet aux utilisateurs de:
    - Voir tous les personas disponibles
    - Filtrer par tags ou nom
    - Limiter le nombre de résultats
    - Inclure ou exclure les personas prédéfinis
    """

    def get_name(self) -> str:
        return "personas_list"

    def get_description(self) -> str:
        return (
            "PERSONAS LIST - List all available personas with optional "
            "filtering. Shows persona details including ID, name, description, "
            "tags, and model preferences. Supports filtering by tags or name, "
            "and pagination with configurable limits. Use this tool to "
            "discover available personas before using them in other tools."
        )

    def get_system_prompt(self) -> str:
        return """You are a persona listing assistant. Your job is to help \
users discover and understand available personas.

When listing personas, provide:
1. Clear, organized presentation of persona information
2. Highlighting of key characteristics and use cases
3. Guidance on when to use specific personas
4. Information about model preferences when relevant

Format the output as a clear, readable list with persona details."""

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        """Define the tool-specific fields for personas_list"""
        return {
            "tags_filter": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by tags (list). Returns personas having at least one of these tags.",
            },
            "name_filter": {"type": "string", "description": "Filter by name (partial search, case-insensitive)"},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "Maximum number of personas to return (1-100)",
            },
            "include_predefined": {
                "type": "boolean",
                "default": True,
                "description": "Include predefined personas in results",
            },
        }

    def get_required_fields(self) -> list[str]:
        """No required fields for listing personas"""
        return []

    def get_request_model(self):
        """Return the request model for validation"""
        return PersonasListRequest

    async def prepare_prompt(self, request: PersonasListRequest) -> str:
        """Prepare the prompt for the AI model"""
        try:
            # Get persona manager
            manager = PersonaManager.get_instance()

            # Create filters
            filters = PersonaSearchFilters(
                query=request.name_filter,
                tags=request.tags_filter or [],
                has_model_preference=None,
                created_after=None,
                created_before=None,
            )

            # Get filtered personas using list_personas method
            personas = manager.list_personas(filters)

            # Apply our own limit if specified
            if request.limit and len(personas) > request.limit:
                personas = personas[: request.limit]

            # Filter predefined if needed
            if not request.include_predefined:
                # Filter out predefined personas (those matching PREDEFINED_PERSONAS ids)
                predefined_ids = {p["id"] for p in PREDEFINED_PERSONAS}
                personas = [p for p in personas if p.id not in predefined_ids]

            # Format personas information
            if not personas:
                personas_info = "No personas found matching the criteria."
            else:
                personas_info = self._format_personas_list(personas, request)

            # Get stats
            stats = manager.get_stats()

            prompt = f"""Please present the following persona information \
in a clear, user-friendly format:

=== PERSONAS SEARCH RESULTS ===
{personas_info}

=== SEARCH CRITERIA ===
- Tags filter: {request.tags_filter or "None"}
- Name filter: {request.name_filter or "None"}
- Limit: {request.limit or "No limit"}
- Include predefined: {request.include_predefined}

=== PERSONA MANAGER STATS ===
- Total personas loaded: {len(manager._personas_cache)}
- Cache hits: {stats["cache_hits"]}
- Cache misses: {stats["cache_misses"]}
- Created: {stats["personas_created"]}
- Updated: {stats["personas_updated"]}
- Deleted: {stats["personas_deleted"]}

Please format this information in a readable way, explaining what each \
persona is for and when to use it."""

            return prompt

        except Exception as e:
            error_msg = handle_persona_error(e)
            return f"Error retrieving personas: {error_msg}"

    def _format_personas_list(self, personas: list, request: PersonasListRequest) -> str:
        """Format the personas list for display"""
        if not personas:
            return "No personas found."

        lines = []
        for i, persona in enumerate(personas, 1):
            lines.append(f"## {i}. {persona.name} (ID: {persona.id})")
            lines.append(f"**Description:** {persona.description}")

            if persona.tags:
                lines.append(f"**Tags:** {', '.join(persona.tags)}")

            # Model preferences
            prefs = []
            if persona.model_preferences.model_name:
                prefs.append(f"Model: {persona.model_preferences.model_name}")
            if persona.model_preferences.temperature is not None:
                prefs.append(f"Temperature: {persona.model_preferences.temperature}")
            if persona.model_preferences.thinking_mode:
                prefs.append(f"Thinking: {persona.model_preferences.thinking_mode}")

            if prefs:
                lines.append(f"**Model Preferences:** {', '.join(prefs)}")

            lines.append(f"**Created:** {persona.created_at.strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"**Version:** {persona.version}")
            lines.append("")  # Empty line between personas

        return "\n".join(lines)

    def format_response(self, response: str, request: PersonasListRequest, model_info: Optional[dict] = None) -> str:
        """Format the AI response"""
        return response
