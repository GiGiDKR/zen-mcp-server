"""
Exceptions spécifiques au module personas.

Ce module définit les exceptions customisées pour les opérations
sur les personas, permettant une gestion d'erreurs spécialisée.
"""

from typing import Optional


class PersonaError(Exception):
    """Exception de base pour toutes les erreurs liées aux personas"""

    def __init__(self, message: str, persona_id: Optional[str] = None):
        self.persona_id = persona_id
        super().__init__(message)


class PersonaNotFoundError(PersonaError):
    """Exception levée quand un persona demandé n'existe pas"""

    def __init__(self, persona_id: str, message: Optional[str] = None):
        if message is None:
            message = f"Persona '{persona_id}' introuvable"
        super().__init__(message, persona_id)


class DuplicatePersonaError(PersonaError):
    """Exception levée lors de la création d'un persona avec un ID déjà existant"""

    def __init__(self, persona_id: str, message: Optional[str] = None):
        if message is None:
            message = f"Persona '{persona_id}' existe déjà"
        super().__init__(message, persona_id)


class PersonaValidationError(PersonaError):
    """Exception levée lors de la validation des données d'un persona"""

    def __init__(self, persona_id: Optional[str], validation_errors: list, message: Optional[str] = None):
        self.validation_errors = validation_errors
        if message is None:
            error_details = ", ".join(validation_errors)
            message = f"Erreurs de validation pour persona '{persona_id}': {error_details}"
        super().__init__(message, persona_id)


class PersonaStorageError(PersonaError):
    """Exception levée lors d'erreurs de stockage/persistance"""

    def __init__(self, operation: str, persona_id: Optional[str] = None, message: Optional[str] = None):
        self.operation = operation
        if message is None:
            if persona_id:
                message = f"Erreur de stockage lors de l'opération '{operation}' pour persona '{persona_id}'"
            else:
                message = f"Erreur de stockage lors de l'opération '{operation}'"
        super().__init__(message, persona_id)


class PersonaConfigError(PersonaError):
    """Exception levée lors d'erreurs de configuration du système personas"""

    def __init__(self, config_key: str, message: Optional[str] = None):
        self.config_key = config_key
        if message is None:
            message = f"Erreur de configuration pour '{config_key}'"
        super().__init__(message)


class PersonaLimitExceededError(PersonaError):
    """Exception levée quand la limite de personas est atteinte"""

    def __init__(self, current_count: int, max_allowed: int, message: Optional[str] = None):
        self.current_count = current_count
        self.max_allowed = max_allowed
        if message is None:
            message = f"Limite de personas atteinte ({current_count}/{max_allowed})"
        super().__init__(message)


class PersonaAccessError(PersonaError):
    """Exception levée lors de problèmes d'accès aux personas (permissions, verrous, etc.)"""

    def __init__(self, persona_id: str, operation: str, message: Optional[str] = None):
        self.operation = operation
        if message is None:
            message = f"Accès refusé pour l'opération '{operation}' sur persona '{persona_id}'"
        super().__init__(message, persona_id)


class PersonaCorruptionError(PersonaError):
    """Exception levée quand les données d'un persona sont corrompues"""

    def __init__(self, persona_id: Optional[str], corruption_details: str, message: Optional[str] = None):
        self.corruption_details = corruption_details
        if message is None:
            if persona_id:
                message = f"Données corrompues pour persona '{persona_id}': {corruption_details}"
            else:
                message = f"Données corrompues: {corruption_details}"
        super().__init__(message, persona_id)


# Fonctions utilitaires pour gestion d'erreurs


def handle_persona_error(error: Exception, context: str = "") -> PersonaError:
    """
    Convertit une exception générique en PersonaError appropriée

    Args:
        error: Exception originale
        context: Contexte de l'erreur pour améliorer le message

    Returns:
        PersonaError appropriée
    """
    if isinstance(error, PersonaError):
        return error

    error_message = str(error)
    if context:
        error_message = f"{context}: {error_message}"

    # Classification basique des erreurs
    if "permission" in error_message.lower() or "access" in error_message.lower():
        return PersonaAccessError("unknown", "access", error_message)
    elif "file" in error_message.lower() or "storage" in error_message.lower():
        return PersonaStorageError("file_operation", message=error_message)
    elif "validation" in error_message.lower():
        return PersonaValidationError(None, [error_message])
    else:
        return PersonaError(error_message)


def is_recoverable_error(error: PersonaError) -> bool:
    """
    Détermine si une erreur persona est récupérable

    Args:
        error: L'erreur à analyser

    Returns:
        True si l'erreur est récupérable, False sinon
    """
    # Erreurs récupérables : problèmes temporaires, réseau, permissions
    recoverable_types = (PersonaStorageError, PersonaAccessError, PersonaConfigError)

    # Erreurs non-récupérables : corruption, validation, limites
    non_recoverable_types = (
        PersonaCorruptionError,
        PersonaValidationError,
        PersonaLimitExceededError,
        DuplicatePersonaError,
        PersonaNotFoundError,
    )

    if isinstance(error, non_recoverable_types):
        return False
    elif isinstance(error, recoverable_types):
        return True
    else:
        # Analyse du message pour cas génériques
        error_message = str(error).lower()
        non_recoverable_keywords = ["corrupt", "invalid", "exceeded", "duplicate"]
        return not any(keyword in error_message for keyword in non_recoverable_keywords)


def get_user_friendly_error_message(error: PersonaError) -> str:
    """
    Convertit une PersonaError en message utilisateur convivial

    Args:
        error: L'erreur à convertir

    Returns:
        Message utilisateur convivial
    """
    if isinstance(error, PersonaNotFoundError):
        return f"Le persona '{error.persona_id}' n'existe pas. Utilisez l'outil personas_list pour voir les personas disponibles."

    elif isinstance(error, DuplicatePersonaError):
        return f"Un persona avec l'ID '{error.persona_id}' existe déjà. Choisissez un autre nom ou mettez à jour le persona existant."

    elif isinstance(error, PersonaValidationError):
        return f"Données du persona invalides: {', '.join(error.validation_errors[:3])}{'...' if len(error.validation_errors) > 3 else ''}"

    elif isinstance(error, PersonaLimitExceededError):
        return f"Limite de personas atteinte ({error.max_allowed} maximum). Supprimez d'abord des personas inutilisés."

    elif isinstance(error, PersonaStorageError):
        return "Erreur de sauvegarde des personas. Vérifiez les permissions du fichier de configuration."

    elif isinstance(error, PersonaAccessError):
        return f"Accès refusé au persona '{error.persona_id}'. Vérifiez les permissions."

    elif isinstance(error, PersonaCorruptionError):
        return "Données de persona corrompues. Restaurez depuis une sauvegarde ou recréez le persona."

    else:
        return f"Erreur persona: {str(error)}"
