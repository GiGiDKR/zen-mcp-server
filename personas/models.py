"""
Modèles de données pour les personas.

Ce module définit les structures de données pour représenter et valider
les personas avec leurs instructions système et préférences de modèles.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ModelPreferences(BaseModel):
    """Configuration des préférences de modèle pour un persona"""

    model_name: Optional[str] = Field(None, description="Nom du modèle préféré (ex: 'gemini-2.5-pro', 'flash')")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Température pour contrôler la créativité du modèle"
    )
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p pour contrôler la diversité des réponses")
    max_tokens: Optional[int] = Field(None, gt=0, le=100000, description="Nombre maximum de tokens en réponse")
    thinking_mode: Optional[str] = Field(None, description="Mode de réflexion (minimal, low, medium, high, max)")

    @validator("thinking_mode")
    def validate_thinking_mode(cls, v):
        if v is not None:
            valid_modes = {"minimal", "low", "medium", "high", "max"}
            if v not in valid_modes:
                raise ValueError(f"thinking_mode doit être l'un de : {valid_modes}")
        return v

    @validator("model_name")
    def validate_model_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("model_name ne peut pas être vide")
        return v.strip() if v else None


class Persona(BaseModel):
    """Modèle de données pour un persona"""

    id: str = Field(
        ..., min_length=1, max_length=100, description="Identifiant unique du persona (alphanumeric + underscore)"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Nom d'affichage du persona")
    description: str = Field(..., min_length=1, max_length=500, description="Description courte du persona")
    system_instructions: str = Field(
        ..., min_length=10, max_length=10000, description="Instructions système personnalisées"
    )
    model_preferences: ModelPreferences = Field(
        default_factory=ModelPreferences, description="Préférences de modèle pour ce persona"
    )
    tags: list[str] = Field(default_factory=list, description="Tags pour catégorisation et recherche")
    created_at: datetime = Field(default_factory=datetime.now, description="Date et heure de création")
    updated_at: datetime = Field(default_factory=datetime.now, description="Date et heure de dernière modification")
    version: str = Field(default="1.0", description="Version du persona pour migration future")

    @validator("id")
    def validate_id(cls, v):
        # Vérifie que l'ID contient seulement des caractères alphanumériques et underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("ID ne peut contenir que des lettres, chiffres et underscores")
        return v.lower()  # Normalise en minuscules

    @validator("tags")
    def validate_tags(cls, v):
        # Limite le nombre de tags et leur longueur
        if len(v) > 20:
            raise ValueError("Maximum 20 tags autorisés")

        validated_tags = []
        for tag in v:
            if isinstance(tag, str) and len(tag.strip()) > 0:
                if len(tag.strip()) > 50:
                    raise ValueError("Les tags ne peuvent pas dépasser 50 caractères")
                validated_tags.append(tag.strip().lower())

        return list(set(validated_tags))  # Retire les doublons

    @validator("system_instructions")
    def validate_system_instructions(cls, v):
        # Vérification de sécurité basique contre l'injection de prompts
        if any(
            pattern in v.lower()
            for pattern in ["ignore previous instructions", "forget everything", "system:", "assistant:", "human:"]
        ):
            raise ValueError("Instructions système contiennent des patterns potentiellement dangereux")
        return v.strip()

    def update_timestamp(self):
        """Met à jour le timestamp de modification"""
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> bool:
        """Ajoute un tag s'il n'existe pas déjà"""
        tag = tag.strip().lower()
        if tag and tag not in self.tags and len(self.tags) < 20:
            self.tags.append(tag)
            self.update_timestamp()
            return True
        return False

    def remove_tag(self, tag: str) -> bool:
        """Supprime un tag s'il existe"""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_timestamp()
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """Vérifie si le persona a un tag spécifique"""
        return tag.strip().lower() in self.tags

    def matches_search(self, query: str) -> bool:
        """Vérifie si le persona correspond à une recherche textuelle"""
        query = query.lower().strip()
        if not query:
            return True

        searchable_text = f"{self.name} {self.description} {' '.join(self.tags)}".lower()
        return query in searchable_text


class PersonaConfig(BaseModel):
    """Configuration globale du système personas"""

    default_persona_id: Optional[str] = Field(
        None, description="ID du persona par défaut à utiliser si aucun n'est spécifié"
    )
    personas_storage_path: str = Field(
        default="~/.zen_personas.json", description="Chemin du fichier de stockage des personas"
    )
    enable_persona_versioning: bool = Field(
        default=False, description="Active le versioning des personas pour migration"
    )
    max_personas: int = Field(default=100, ge=1, le=1000, description="Nombre maximum de personas autorisés")
    cache_enabled: bool = Field(default=True, description="Active le cache en mémoire pour les personas")
    backup_enabled: bool = Field(default=True, description="Active la sauvegarde automatique des personas")

    @validator("personas_storage_path")
    def validate_storage_path(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Le chemin de stockage ne peut pas être vide")
        return v.strip()


class PersonaSearchFilters(BaseModel):
    """Filtres pour rechercher des personas"""

    query: Optional[str] = Field(None, description="Recherche textuelle dans nom, description et tags")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags requis (ET logique)")
    has_model_preference: Optional[bool] = Field(
        None, description="Filtre les personas avec/sans préférences de modèle"
    )
    created_after: Optional[datetime] = Field(None, description="Personas créés après cette date")
    created_before: Optional[datetime] = Field(None, description="Personas créés avant cette date")


# Constantes utiles
DEFAULT_PERSONA_CONFIG = PersonaConfig()

# Expressions régulières pour validation
PERSONA_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_]{1,100}$")
TAG_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")

# Personas prédéfinis pour exemples (seront créés lors de l'initialisation)
PREDEFINED_PERSONAS = [
    {
        "id": "python_expert",
        "name": "Expert Python",
        "description": "Développeur Python senior spécialisé en backends robustes",
        "system_instructions": """Vous êtes un expert développeur Python avec 10+ années d'expérience.
Vous maîtrisez Django, FastAPI, SQLAlchemy et les bonnes pratiques Python.
Votre code respecte PEP 8, privilégie la lisibilité et la maintenabilité.
Vous fournissez des exemples concrets, expliquez vos choix techniques et proposez des tests appropriés.""",
        "model_preferences": {"model_name": "gemini-2.5-pro", "temperature": 0.3, "thinking_mode": "medium"},
        "tags": ["development", "python", "backend", "expert"],
    },
    {
        "id": "system_architect",
        "name": "Architecte Système",
        "description": "Expert en architecture logicielle et décisions techniques",
        "system_instructions": """Vous êtes un architecte logiciel expérimenté.
Vous analysez les besoins techniques sous l'angle de la scalabilité, maintenabilité et performance.
Vous proposez des architectures équilibrées évitant la sur-ingénierie.
Vos recommandations sont pragmatiques, considèrent les contraintes business et incluent les trade-offs.
Vous documentez clairement vos décisions architecturales.""",
        "model_preferences": {"model_name": "gemini-2.5-pro", "temperature": 0.4, "thinking_mode": "high"},
        "tags": ["architecture", "design", "scalability", "expert"],
    },
    {
        "id": "security_reviewer",
        "name": "Expert Sécurité",
        "description": "Spécialisé en analyse de vulnérabilités et bonnes pratiques sécuritaires",
        "system_instructions": """Vous êtes un expert en sécurité applicative.
Vous analysez le code sous l'angle des vulnérabilités OWASP Top 10, injection SQL, XSS, CSRF, failles d'authentification.
Vous proposez des corrections concrètes et expliquez les risques.
Votre approche est systématique, couvre la sécurité des données, l'authorisation et la surface d'attaque.""",
        "model_preferences": {"model_name": "gemini-2.5-pro", "temperature": 0.2, "thinking_mode": "high"},
        "tags": ["security", "vulnerabilities", "owasp", "expert"],
    },
]
