"""
Gestionnaire central pour les opérations CRUD sur les personas.

Ce module fournit une interface unifiée pour gérer les personas,
incluant création, lecture, mise à jour, suppression avec cache et validation.
"""

import logging
import threading
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Optional

from .exceptions import (
    DuplicatePersonaError,
    PersonaLimitExceededError,
    PersonaNotFoundError,
    PersonaValidationError,
    handle_persona_error,
)
from .models import PREDEFINED_PERSONAS, Persona, PersonaConfig, PersonaSearchFilters
from .storage import JsonFileStorage, PersonaStorage

logger = logging.getLogger(__name__)


class PersonaManager:
    """
    Gestionnaire des personas avec pattern singleton configurable.

    Fournit une interface unifiée pour toutes les opérations sur les personas
    avec cache en mémoire, validation et gestion d'erreurs robuste.
    """

    _instance: Optional["PersonaManager"] = None
    _lock = threading.Lock()

    def __init__(self, storage: PersonaStorage, config: Optional[PersonaConfig] = None):
        """
        Initialise le gestionnaire de personas

        Args:
            storage: Interface de stockage à utiliser
            config: Configuration optionnelle (utilise les défauts sinon)
        """
        self._storage = storage
        self._config = config or PersonaConfig()
        self._personas_cache: dict[str, Persona] = {}
        self._cache_lock = threading.RLock()
        self._last_cache_update = datetime.now()
        self._cache_ttl = timedelta(minutes=30)  # TTL du cache

        # Statistiques d'usage
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "personas_created": 0,
            "personas_updated": 0,
            "personas_deleted": 0,
        }

        # Chargement initial et initialisation des personas prédéfinis
        self._load_personas()
        self._ensure_predefined_personas()

        logger.info(f"PersonaManager initialisé avec {len(self._personas_cache)} personas")

    @classmethod
    def get_instance(
        cls, storage: Optional[PersonaStorage] = None, config: Optional[PersonaConfig] = None
    ) -> "PersonaManager":
        """
        Obtient l'instance singleton du manager

        Args:
            storage: Interface de stockage (crée JsonFileStorage par défaut)
            config: Configuration (utilise les défauts sinon)

        Returns:
            Instance singleton du PersonaManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if storage is None:
                        storage = JsonFileStorage()
                    cls._instance = cls(storage, config)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Réinitialise l'instance singleton (pour les tests)"""
        with cls._lock:
            cls._instance = None
        cls._lock = threading.Lock()  # Réinitialise le lock pour les tests

    def _load_personas(self):
        """Charge tous les personas depuis le stockage vers le cache"""
        try:
            with self._cache_lock:
                personas = self._storage.load_all_personas()
                self._personas_cache = {p.id: p for p in personas}
                self._last_cache_update = datetime.now()

            logger.debug(f"Cache rechargé avec {len(self._personas_cache)} personas")

        except Exception as e:
            error = handle_persona_error(e, "Chargement des personas")
            logger.error(f"Erreur chargement personas: {error}")
            raise error

    def _ensure_predefined_personas(self):
        """Crée les personas prédéfinis s'ils n'existent pas"""
        try:
            for persona_data in PREDEFINED_PERSONAS:
                if not self.exists(persona_data["id"]):
                    try:
                        persona = Persona(**persona_data)
                        self._storage.save_persona(persona)
                        with self._cache_lock:
                            self._personas_cache[persona.id] = persona

                        logger.info(f"Persona prédéfini créé: {persona.id}")

                    except Exception as e:
                        logger.warning(f"Impossible de créer persona prédéfini {persona_data['id']}: {e}")
                        continue

        except Exception as e:
            logger.warning(f"Erreur création personas prédéfinis: {e}")

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache est encore valide"""
        if not self._config.cache_enabled:
            return False
        return datetime.now() - self._last_cache_update < self._cache_ttl

    def _refresh_cache_if_needed(self):
        """Rafraîchit le cache s'il est expiré"""
        if not self._is_cache_valid():
            logger.debug("Cache expiré, rechargement...")
            self._load_personas()

    def _validate_persona_limit(self, exclude_id: Optional[str] = None):
        """
        Vérifie que la limite de personas n'est pas atteinte

        Args:
            exclude_id: ID à exclure du décompte (pour les mises à jour)

        Raises:
            PersonaLimitExceededError: Si limite atteinte
        """
        current_count = len(self._personas_cache)
        if exclude_id and exclude_id in self._personas_cache:
            current_count -= 1

        if current_count >= self._config.max_personas:
            raise PersonaLimitExceededError(current_count, self._config.max_personas)

    def create_persona(self, persona: Persona) -> Persona:
        """
        Crée un nouveau persona

        Args:
            persona: Le persona à créer

        Returns:
            Le persona créé avec timestamps mis à jour

        Raises:
            DuplicatePersonaError: Si l'ID existe déjà
            PersonaLimitExceededError: Si limite atteinte
            PersonaValidationError: Si validation échoue
            PersonaStorageError: Si erreur de stockage
        """
        try:
            # Validation de l'unicité de l'ID
            if self.exists(persona.id):
                raise DuplicatePersonaError(persona.id)

            # Validation de la limite
            self._validate_persona_limit()

            # Mise à jour des timestamps
            now = datetime.now()
            persona.created_at = now
            persona.updated_at = now

            # Sauvegarde
            self._storage.save_persona(persona)

            # Mise à jour du cache
            with self._cache_lock:
                self._personas_cache[persona.id] = deepcopy(persona)

            # Statistiques
            self._stats["personas_created"] += 1

            logger.info(f"Persona créé: {persona.id}")
            return persona

        except (DuplicatePersonaError, PersonaLimitExceededError, PersonaValidationError):
            raise
        except Exception as e:
            error = handle_persona_error(e, f"Création persona {persona.id}")
            logger.error(f"Erreur création persona {persona.id}: {error}")
            raise error

    def get_persona(self, persona_id: str) -> Persona:
        """
        Récupère un persona par son ID

        Args:
            persona_id: ID du persona à récupérer

        Returns:
            Le persona trouvé

        Raises:
            PersonaNotFoundError: Si persona introuvable
            PersonaStorageError: Si erreur de récupération
        """
        try:
            # Vérification cache
            if self._config.cache_enabled:
                with self._cache_lock:
                    if persona_id in self._personas_cache and self._is_cache_valid():
                        self._stats["cache_hits"] += 1
                        return deepcopy(self._personas_cache[persona_id])

            # Cache miss ou désactivé
            self._stats["cache_misses"] += 1
            self._refresh_cache_if_needed()

            with self._cache_lock:
                if persona_id in self._personas_cache:
                    return deepcopy(self._personas_cache[persona_id])

            raise PersonaNotFoundError(persona_id)

        except PersonaNotFoundError:
            raise
        except Exception as e:
            error = handle_persona_error(e, f"Récupération persona {persona_id}")
            logger.error(f"Erreur récupération persona {persona_id}: {error}")
            raise error

    def list_personas(self, filters: Optional[PersonaSearchFilters] = None) -> list[Persona]:
        """
        Liste tous les personas disponibles avec filtrage optionnel

        Args:
            filters: Filtres de recherche optionnels

        Returns:
            Liste des personas correspondant aux filtres

        Raises:
            PersonaStorageError: Si erreur de récupération
        """
        try:
            self._refresh_cache_if_needed()

            with self._cache_lock:
                personas = list(self._personas_cache.values())

            # Application des filtres
            if filters:
                personas = self._apply_filters(personas, filters)

            # Tri par nom
            personas.sort(key=lambda p: p.name.lower())

            return [deepcopy(p) for p in personas]

        except Exception as e:
            error = handle_persona_error(e, "Listage des personas")
            logger.error(f"Erreur listage personas: {error}")
            raise error

    def _apply_filters(self, personas: list[Persona], filters: PersonaSearchFilters) -> list[Persona]:
        """Applique les filtres de recherche à la liste de personas"""
        filtered = personas

        # Filtre par recherche textuelle
        if filters.query:
            filtered = [p for p in filtered if p.matches_search(filters.query)]

        # Filtre par tags (ET logique)
        if filters.tags:
            filtered = [p for p in filtered if all(p.has_tag(tag) for tag in filters.tags)]

        # Filtre par préférences de modèle
        if filters.has_model_preference is not None:
            if filters.has_model_preference:
                filtered = [p for p in filtered if p.model_preferences.model_name is not None]
            else:
                filtered = [p for p in filtered if p.model_preferences.model_name is None]

        # Filtres par date
        if filters.created_after:
            filtered = [p for p in filtered if p.created_at >= filters.created_after]

        if filters.created_before:
            filtered = [p for p in filtered if p.created_at <= filters.created_before]

        return filtered

    def update_persona(self, persona_id: str, updates: dict[str, Any]) -> Persona:
        """
        Met à jour un persona existant

        Args:
            persona_id: ID du persona à mettre à jour
            updates: Dictionnaire des champs à mettre à jour

        Returns:
            Le persona mis à jour

        Raises:
            PersonaNotFoundError: Si persona introuvable
            PersonaValidationError: Si validation échoue
            PersonaStorageError: Si erreur de stockage
        """
        try:
            # Récupération du persona existant
            persona = self.get_persona(persona_id)

            # Application des mises à jour
            for field, value in updates.items():
                if hasattr(persona, field):
                    setattr(persona, field, value)
                else:
                    logger.warning(f"Champ ignoré lors de la mise à jour: {field}")

            # Validation via Pydantic (recrée l'objet pour validation complète)
            updated_persona = Persona(**persona.dict())
            updated_persona.update_timestamp()

            # Sauvegarde
            self._storage.save_persona(updated_persona)

            # Mise à jour du cache
            with self._cache_lock:
                self._personas_cache[persona_id] = deepcopy(updated_persona)

            # Statistiques
            self._stats["personas_updated"] += 1

            logger.info(f"Persona mis à jour: {persona_id}")
            return updated_persona

        except PersonaNotFoundError:
            raise
        except Exception as e:
            error = handle_persona_error(e, f"Mise à jour persona {persona_id}")
            logger.error(f"Erreur mise à jour persona {persona_id}: {error}")
            raise error

    def delete_persona(self, persona_id: str) -> bool:
        """
        Supprime un persona

        Args:
            persona_id: ID du persona à supprimer

        Returns:
            True si suppression réussie

        Raises:
            PersonaNotFoundError: Si persona introuvable
            PersonaStorageError: Si erreur de suppression
        """
        try:
            # Vérification de l'existence
            if not self.exists(persona_id):
                raise PersonaNotFoundError(persona_id)

            # Suppression du stockage
            self._storage.delete_persona(persona_id)

            # Suppression du cache
            with self._cache_lock:
                if persona_id in self._personas_cache:
                    del self._personas_cache[persona_id]

            # Statistiques
            self._stats["personas_deleted"] += 1

            logger.info(f"Persona supprimé: {persona_id}")
            return True

        except PersonaNotFoundError:
            raise
        except Exception as e:
            error = handle_persona_error(e, f"Suppression persona {persona_id}")
            logger.error(f"Erreur suppression persona {persona_id}: {error}")
            raise error

    def exists(self, persona_id: str) -> bool:
        """
        Vérifie si un persona existe

        Args:
            persona_id: ID du persona à vérifier

        Returns:
            True si le persona existe, False sinon
        """
        try:
            if self._config.cache_enabled and self._is_cache_valid():
                with self._cache_lock:
                    return persona_id in self._personas_cache

            # Fallback vers le stockage
            return self._storage.exists(persona_id)

        except Exception:
            # En cas d'erreur, assume que le persona n'existe pas
            return False

    def search_personas(self, query: str) -> list[Persona]:
        """
        Recherche des personas par texte

        Args:
            query: Requête de recherche

        Returns:
            Liste des personas correspondants
        """
        filters = PersonaSearchFilters(query=query)
        return self.list_personas(filters)

    def get_personas_by_tag(self, tag: str) -> list[Persona]:
        """
        Récupère tous les personas ayant un tag spécifique

        Args:
            tag: Tag à rechercher

        Returns:
            Liste des personas avec ce tag
        """
        filters = PersonaSearchFilters(tags=[tag])
        return self.list_personas(filters)

    def get_stats(self) -> dict[str, Any]:
        """
        Retourne les statistiques d'usage du manager

        Returns:
            Dictionnaire des statistiques
        """
        cache_total = self._stats["cache_hits"] + self._stats["cache_misses"]
        cache_hit_rate = (self._stats["cache_hits"] / cache_total * 100) if cache_total > 0 else 0

        return {
            **self._stats,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "total_personas": len(self._personas_cache),
            "cache_enabled": self._config.cache_enabled,
            "cache_valid": self._is_cache_valid(),
            "last_cache_update": self._last_cache_update.isoformat(),
        }

    def clear_cache(self):
        """Vide le cache et force un rechargement"""
        with self._cache_lock:
            self._personas_cache.clear()
            self._last_cache_update = datetime.min

        logger.info("Cache des personas vidé")

    def backup_personas(self) -> str:
        """
        Crée une sauvegarde des personas

        Returns:
            Chemin de la sauvegarde créée

        Raises:
            PersonaStorageError: Si erreur de sauvegarde
        """
        try:
            backup_path = self._storage.backup()
            logger.info(f"Sauvegarde créée: {backup_path}")
            return backup_path

        except Exception as e:
            error = handle_persona_error(e, "Sauvegarde des personas")
            logger.error(f"Erreur sauvegarde: {error}")
            raise error

    def restore_personas(self, backup_path: str) -> bool:
        """
        Restaure les personas depuis une sauvegarde

        Args:
            backup_path: Chemin de la sauvegarde à restaurer

        Returns:
            True si restauration réussie

        Raises:
            PersonaStorageError: Si erreur de restauration
        """
        try:
            result = self._storage.restore_from_backup(backup_path)
            if result:
                # Recharge le cache
                self._load_personas()
                logger.info(f"Restauration réussie depuis: {backup_path}")
            return result

        except Exception as e:
            error = handle_persona_error(e, f"Restauration depuis {backup_path}")
            logger.error(f"Erreur restauration: {error}")
            raise error

    def get_config(self) -> PersonaConfig:
        """Retourne la configuration actuelle"""
        return deepcopy(self._config)

    def update_config(self, config: PersonaConfig):
        """
        Met à jour la configuration

        Args:
            config: Nouvelle configuration
        """
        self._config = config
        logger.info("Configuration mise à jour")

    def get_default_persona_id(self) -> Optional[str]:
        """Retourne l'ID du persona par défaut s'il est configuré et existe"""
        default_id = self._config.default_persona_id
        if default_id and self.exists(default_id):
            return default_id
        return None
