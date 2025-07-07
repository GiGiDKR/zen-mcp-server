"""
Couche d'abstraction pour la persistance des personas.

Ce module définit les interfaces et implémentations pour stocker
et récupérer les personas de manière persistante.
"""

import json
import logging
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .exceptions import PersonaAccessError, PersonaCorruptionError, PersonaNotFoundError, PersonaStorageError
from .models import Persona

logger = logging.getLogger(__name__)

# Détection des capacités de verrouillage de fichiers
# Temporairement désactivé pour résoudre les problèmes de compatibilité
HAS_FCNTL = False
HAS_MSVCRT = False


def _lock_file(file_obj, exclusive: bool = False):
    """
    Verrouille un fichier de manière multiplateforme

    Args:
        file_obj: Objet fichier à verrouiller
        exclusive: True pour verrou exclusif, False pour partagé

    Note: Verrouillage désactivé temporairement pour compatibilité
    """
    # Verrouillage désactivé pour éviter les problèmes de compatibilité
    pass


def _unlock_file(file_obj):
    """
    Déverrouille un fichier de manière multiplateforme

    Args:
        file_obj: Objet fichier à déverrouiller

    Note: Verrouillage désactivé temporairement pour compatibilité
    """
    # Verrouillage désactivé pour éviter les problèmes de compatibilité
    pass


class PersonaStorage(ABC):
    """Interface abstraite pour la persistance des personas"""

    @abstractmethod
    def load_all_personas(self) -> list[Persona]:
        """
        Charge tous les personas depuis le stockage

        Returns:
            Liste de tous les personas disponibles

        Raises:
            PersonaStorageError: Erreur lors du chargement
        """
        pass

    @abstractmethod
    def save_persona(self, persona: Persona) -> bool:
        """
        Sauvegarde un persona dans le stockage

        Args:
            persona: Le persona à sauvegarder

        Returns:
            True si sauvegarde réussie, False sinon

        Raises:
            PersonaStorageError: Erreur lors de la sauvegarde
        """
        pass

    @abstractmethod
    def delete_persona(self, persona_id: str) -> bool:
        """
        Supprime un persona du stockage

        Args:
            persona_id: ID du persona à supprimer

        Returns:
            True si suppression réussie, False sinon

        Raises:
            PersonaStorageError: Erreur lors de la suppression
            PersonaNotFoundError: Persona introuvable
        """
        pass

    @abstractmethod
    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """
        Récupère un persona spécifique

        Args:
            persona_id: ID du persona à récupérer

        Returns:
            Le persona trouvé ou None

        Raises:
            PersonaStorageError: Erreur lors de la récupération
        """
        pass

    @abstractmethod
    def exists(self, persona_id: str) -> bool:
        """
        Vérifie si un persona existe

        Args:
            persona_id: ID du persona à vérifier

        Returns:
            True si le persona existe, False sinon
        """
        pass

    @abstractmethod
    def backup(self) -> str:
        """
        Crée une sauvegarde du stockage

        Returns:
            Chemin de la sauvegarde créée

        Raises:
            PersonaStorageError: Erreur lors de la sauvegarde
        """
        pass

    @abstractmethod
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restaure depuis une sauvegarde

        Args:
            backup_path: Chemin de la sauvegarde à restaurer

        Returns:
            True si restauration réussie, False sinon

        Raises:
            PersonaStorageError: Erreur lors de la restauration
        """
        pass


class JsonFileStorage(PersonaStorage):
    """Implémentation du stockage en fichier JSON"""

    def __init__(self, file_path: str = "~/.zen_personas.json", enable_backup: bool = True):
        """
        Initialise le stockage JSON

        Args:
            file_path: Chemin du fichier de stockage
            enable_backup: Active les sauvegardes automatiques
        """
        self.file_path = Path(file_path).expanduser().resolve()
        self.enable_backup = enable_backup
        self.backup_dir = self.file_path.parent / ".zen_personas_backups"

        # Crée les répertoires nécessaires
        self.file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.enable_backup:
            self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Initialise le fichier s'il n'existe pas
        self._ensure_file_exists()

        logger.info(f"JsonFileStorage initialisé avec fichier: {self.file_path}")

    def _ensure_file_exists(self):
        """Crée le fichier de stockage s'il n'existe pas"""
        if not self.file_path.exists():
            try:
                initial_data = {
                    "personas": [],
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, indent=2, ensure_ascii=False, default=str)

                # Définit les permissions restrictives
                os.chmod(self.file_path, 0o600)

                logger.info(f"Fichier de stockage initialisé: {self.file_path}")

            except Exception as e:
                raise PersonaStorageError("initialization", message=f"Impossible de créer le fichier de stockage: {e}")

    def _read_storage_file(self) -> dict[str, Any]:
        """
        Lit et parse le fichier de stockage avec verrouillage

        Returns:
            Données parsées du fichier

        Raises:
            PersonaStorageError: Erreur de lecture
            PersonaCorruptionError: Fichier corrompu
        """
        try:
            with open(self.file_path, encoding="utf-8") as f:
                # Verrouillage partagé pour lecture
                _lock_file(f)
                try:
                    data = json.load(f)

                    # Validation basique de la structure
                    if not isinstance(data, dict) or "personas" not in data:
                        raise PersonaCorruptionError(
                            None,
                            "Structure du fichier invalide",
                            "Le fichier de stockage n'a pas la structure attendue",
                        )

                    return data

                finally:
                    _unlock_file(f)

        except json.JSONDecodeError as e:
            raise PersonaCorruptionError(
                None, f"JSON invalide: {e}", "Le fichier de stockage contient du JSON invalide"
            )
        except FileNotFoundError:
            # Recrée le fichier s'il a été supprimé
            self._ensure_file_exists()
            return self._read_storage_file()
        except PermissionError as e:
            raise PersonaAccessError("unknown", "read", f"Permissions insuffisantes: {e}")
        except Exception as e:
            raise PersonaStorageError("read", message=f"Erreur lecture fichier: {e}")

    def _write_storage_file(self, data: dict[str, Any]):
        """
        Écrit les données dans le fichier avec sauvegarde atomique

        Args:
            data: Données à écrire

        Raises:
            PersonaStorageError: Erreur d'écriture
        """
        try:
            # Sauvegarde automatique avant modification
            if self.enable_backup and self.file_path.exists():
                self._create_backup()

            # Écriture atomique via fichier temporaire
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.file_path.parent, delete=False, suffix=".tmp"
                ) as temp_file:
                    # Verrouillage exclusif
                    _lock_file(temp_file, exclusive=True)

                    # Met à jour le timestamp
                    data["updated_at"] = datetime.now().isoformat()

                    # Écrit les données
                    json.dump(data, temp_file, indent=2, ensure_ascii=False, default=str)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())

                # Permissions restrictives
                os.chmod(temp_file.name, 0o600)

                # Déplacement atomique
                shutil.move(temp_file.name, self.file_path)

                logger.debug(f"Fichier de stockage mis à jour: {self.file_path}")

            except Exception as e:
                # Nettoyage du fichier temporaire en cas d'erreur
                if temp_file and os.path.exists(temp_file.name):
                    try:
                        os.unlink(temp_file.name)
                    except OSError:
                        pass
                raise e

        except PermissionError as e:
            raise PersonaAccessError("unknown", "write", f"Permissions insuffisantes: {e}")
        except Exception as e:
            raise PersonaStorageError("write", message=f"Erreur écriture fichier: {e}")

    def _create_backup(self) -> str:
        """
        Crée une sauvegarde horodatée du fichier actuel

        Returns:
            Chemin de la sauvegarde créée
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"personas_backup_{timestamp}.json"

        try:
            shutil.copy2(self.file_path, backup_path)
            os.chmod(backup_path, 0o600)

            # Nettoyage des anciennes sauvegardes (garde les 10 plus récentes)
            self._cleanup_old_backups()

            logger.debug(f"Sauvegarde créée: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.warning(f"Échec création sauvegarde: {e}")
            raise PersonaStorageError("backup", message=f"Impossible de créer la sauvegarde: {e}")

    def _cleanup_old_backups(self, max_backups: int = 10):
        """Supprime les anciennes sauvegardes en gardant les plus récentes"""
        try:
            backup_files = list(self.backup_dir.glob("personas_backup_*.json"))
            if len(backup_files) > max_backups:
                # Trie par date de modification et supprime les plus anciennes
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_backup in backup_files[max_backups:]:
                    old_backup.unlink()
                    logger.debug(f"Ancienne sauvegarde supprimée: {old_backup}")
        except Exception as e:
            logger.warning(f"Erreur nettoyage sauvegardes: {e}")

    def load_all_personas(self) -> list[Persona]:
        """Charge tous les personas depuis le fichier JSON"""
        try:
            data = self._read_storage_file()
            personas = []

            for persona_data in data.get("personas", []):
                try:
                    persona = Persona(**persona_data)
                    personas.append(persona)
                except Exception as e:
                    logger.warning(f"Persona corrompu ignoré: {e}")
                    continue

            logger.debug(f"Chargé {len(personas)} personas depuis le stockage")
            return personas

        except (PersonaStorageError, PersonaCorruptionError):
            raise
        except Exception as e:
            raise PersonaStorageError("load_all", message=f"Erreur chargement personas: {e}")

    def save_persona(self, persona: Persona) -> bool:
        """Sauvegarde un persona dans le fichier JSON"""
        try:
            data = self._read_storage_file()
            personas_data = data.get("personas", [])

            # Mise à jour du timestamp
            persona.update_timestamp()
            persona_dict = persona.dict()

            # Recherche et mise à jour ou ajout
            updated = False
            for i, existing_data in enumerate(personas_data):
                if existing_data.get("id") == persona.id:
                    personas_data[i] = persona_dict
                    updated = True
                    break

            if not updated:
                personas_data.append(persona_dict)

            data["personas"] = personas_data
            self._write_storage_file(data)

            logger.debug(f"Persona '{persona.id}' sauvegardé")
            return True

        except (PersonaStorageError, PersonaAccessError):
            raise
        except Exception as e:
            raise PersonaStorageError("save", persona.id, f"Erreur sauvegarde persona: {e}")

    def delete_persona(self, persona_id: str) -> bool:
        """Supprime un persona du fichier JSON"""
        try:
            data = self._read_storage_file()
            personas_data = data.get("personas", [])

            # Recherche et suppression
            initial_count = len(personas_data)
            personas_data = [p for p in personas_data if p.get("id") != persona_id]

            if len(personas_data) == initial_count:
                raise PersonaNotFoundError(persona_id)

            data["personas"] = personas_data
            self._write_storage_file(data)

            logger.debug(f"Persona '{persona_id}' supprimé")
            return True

        except PersonaNotFoundError:
            raise
        except (PersonaStorageError, PersonaAccessError):
            raise
        except Exception as e:
            raise PersonaStorageError("delete", persona_id, f"Erreur suppression persona: {e}")

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Récupère un persona spécifique par son ID"""
        try:
            personas = self.load_all_personas()
            for persona in personas:
                if persona.id == persona_id:
                    return persona
            return None

        except (PersonaStorageError, PersonaCorruptionError):
            raise
        except Exception as e:
            raise PersonaStorageError("get", persona_id, f"Erreur récupération persona: {e}")

    def exists(self, persona_id: str) -> bool:
        """Vérifie si un persona existe"""
        return self.get_persona(persona_id) is not None

    def backup(self) -> str:
        """Crée une sauvegarde manuelle"""
        if not self.file_path.exists():
            raise PersonaStorageError("backup", message="Aucun fichier de stockage à sauvegarder")

        return self._create_backup()

    def restore_from_backup(self, backup_path: str) -> bool:
        """Restaure depuis une sauvegarde"""
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise PersonaStorageError("restore", message=f"Fichier de sauvegarde introuvable: {backup_path}")

        try:
            # Validation du fichier de sauvegarde
            with open(backup_file, encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "personas" not in data:
                    raise PersonaCorruptionError(
                        None, "Sauvegarde invalide", "Le fichier de sauvegarde n'a pas la structure attendue"
                    )

            # Sauvegarde du fichier actuel avant restauration
            if self.file_path.exists():
                current_backup = self._create_backup()
                logger.info(f"Fichier actuel sauvegardé avant restauration: {current_backup}")

            # Restauration
            shutil.copy2(backup_file, self.file_path)
            os.chmod(self.file_path, 0o600)

            logger.info(f"Restauration réussie depuis: {backup_path}")
            return True

        except (PersonaStorageError, PersonaCorruptionError):
            raise
        except Exception as e:
            raise PersonaStorageError("restore", message=f"Erreur restauration: {e}")

    def get_storage_info(self) -> dict[str, Any]:
        """Retourne des informations sur le stockage"""
        try:
            data = self._read_storage_file()
            file_stat = self.file_path.stat()

            return {
                "storage_type": "json_file",
                "file_path": str(self.file_path),
                "file_size": file_stat.st_size,
                "personas_count": len(data.get("personas", [])),
                "version": data.get("version", "unknown"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "backup_enabled": self.enable_backup,
                "backup_dir": str(self.backup_dir) if self.enable_backup else None,
            }

        except Exception as e:
            return {"storage_type": "json_file", "file_path": str(self.file_path), "error": str(e)}
