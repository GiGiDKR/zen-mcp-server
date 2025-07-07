"""
Module personas pour zen-mcp-server.

Ce module fournit un système de personas permettant aux utilisateurs
de définir des rôles/personnalités IA avec des instructions système
personnalisées et des préférences de modèles.

Utilisation de base:
    from personas import PersonaManager, Persona

    # Obtenir le gestionnaire
    manager = PersonaManager.get_instance()

    # Créer un persona
    persona = Persona(
        id="expert_python",
        name="Expert Python",
        description="Spécialisé en développement Python",
        system_instructions="Vous êtes un expert Python..."
    )
    manager.create_persona(persona)

    # Utiliser un persona
    expert = manager.get_persona("expert_python")
"""

import logging

# Version du module
__version__ = "1.0.0"

# Import des classes principales
from .exceptions import (
    DuplicatePersonaError,
    PersonaAccessError,
    PersonaConfigError,
    PersonaCorruptionError,
    PersonaError,
    PersonaLimitExceededError,
    PersonaNotFoundError,
    PersonaStorageError,
    PersonaValidationError,
    get_user_friendly_error_message,
    handle_persona_error,
    is_recoverable_error,
)
from .manager import PersonaManager
from .models import (
    DEFAULT_PERSONA_CONFIG,
    PREDEFINED_PERSONAS,
    ModelPreferences,
    Persona,
    PersonaConfig,
    PersonaSearchFilters,
)
from .storage import JsonFileStorage, PersonaStorage

# Classes principales exposées
__all__ = [
    # Version
    "__version__",
    # Modèles de données
    "Persona",
    "PersonaConfig",
    "ModelPreferences",
    "PersonaSearchFilters",
    "PREDEFINED_PERSONAS",
    "DEFAULT_PERSONA_CONFIG",
    # Gestionnaire principal
    "PersonaManager",
    # Interface de stockage
    "PersonaStorage",
    "JsonFileStorage",
    # Exceptions
    "PersonaError",
    "PersonaNotFoundError",
    "DuplicatePersonaError",
    "PersonaValidationError",
    "PersonaStorageError",
    "PersonaConfigError",
    "PersonaLimitExceededError",
    "PersonaAccessError",
    "PersonaCorruptionError",
    # Utilitaires
    "handle_persona_error",
    "is_recoverable_error",
    "get_user_friendly_error_message",
]


# Fonctions de convenance
def get_manager() -> PersonaManager:
    """
    Retourne l'instance singleton du PersonaManager

    Returns:
        Instance du PersonaManager
    """
    return PersonaManager.get_instance()


def create_persona(id: str, name: str, description: str, system_instructions: str, **kwargs) -> Persona:
    """
    Fonction de convenance pour créer un persona

    Args:
        id: Identifiant unique
        name: Nom d'affichage
        description: Description courte
        system_instructions: Instructions système
        **kwargs: Arguments additionnels (tags, model_preferences, etc.)

    Returns:
        Persona créé et sauvegardé

    Raises:
        DuplicatePersonaError: Si l'ID existe déjà
        PersonaValidationError: Si validation échoue
    """
    manager = get_manager()
    persona = Persona(id=id, name=name, description=description, system_instructions=system_instructions, **kwargs)
    return manager.create_persona(persona)


def get_persona(persona_id: str) -> Persona:
    """
    Fonction de convenance pour récupérer un persona

    Args:
        persona_id: ID du persona à récupérer

    Returns:
        Persona trouvé

    Raises:
        PersonaNotFoundError: Si persona introuvable
    """
    manager = get_manager()
    return manager.get_persona(persona_id)


def list_personas() -> list[Persona]:
    """
    Fonction de convenance pour lister tous les personas

    Returns:
        Liste de tous les personas disponibles
    """
    manager = get_manager()
    return manager.list_personas()


def delete_persona(persona_id: str) -> bool:
    """
    Fonction de convenance pour supprimer un persona

    Args:
        persona_id: ID du persona à supprimer

    Returns:
        True si suppression réussie

    Raises:
        PersonaNotFoundError: Si persona introuvable
    """
    manager = get_manager()
    return manager.delete_persona(persona_id)


# Ajout des fonctions de convenance à __all__
__all__.extend(["get_manager", "create_persona", "get_persona", "list_personas", "delete_persona"])

# Configuration de logging pour le module

# Logger du module
logger = logging.getLogger(__name__)

# Évite la propagation des logs si pas de handler configuré
logger.propagate = True

# Message de démarrage (uniquement en mode debug)
logger.debug(f"Module personas {__version__} initialisé")
