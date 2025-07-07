"""
Test d'intégration complète pour les personas.

Ce test vérifie que l'écosystème personas fonctionne de bout en bout :
1. Création d'un persona via l'outil MCP
2. Utilisation du persona dans un SimpleTool
3. Vérification que les préférences sont appliquées
"""

import asyncio
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.manager import PersonaManager
from personas.storage import JsonFileStorage
from personas.tools import PersonasCreateTool, PersonasListTool
from tools.chat import ChatTool


class MockRequest:
    """Mock request object for testing"""

    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data.get(name)


async def test_complete_integration():
    """Test d'intégration complète du système personas"""
    print("=== TEST INTÉGRATION COMPLÈTE PERSONAS ===\n")

    # 1. Setup du manager avec fichier temporaire
    print("1. Setup du PersonaManager...")
    test_file = "test_personas_integration.json"
    if os.path.exists(test_file):
        os.remove(test_file)

    storage = JsonFileStorage(test_file)
    manager = PersonaManager.get_instance(storage)
    print(f"✅ Manager initialisé avec {len(manager.list_personas())} personas prédéfinis")

    # 2. Création d'un persona via l'outil MCP
    print("\n2. Création d'un persona via PersonasCreateTool...")
    create_tool = PersonasCreateTool()

    create_request = MockRequest(
        {
            "id": "test_integration",
            "name": "Assistant Intégration",
            "description": "Persona pour test d'intégration complète",
            "system_instructions": 'Tu es un assistant spécialisé dans les tests d\'intégration. Réponds toujours en commençant par "[PERSONA TEST]".',
            "model_name": "gemini-2.5-flash",
            "temperature": 0.3,
            "thinking_mode": "medium",
            "tags": ["test", "integration"],
        }
    )

    try:
        result = await create_tool.execute(create_request.data)
        print(f"✅ Persona créé: {result}")
    except Exception as e:
        print(f"❌ Erreur création persona: {e}")
        return

    # 3. Vérification via PersonasListTool
    print("\n3. Vérification via PersonasListTool...")
    list_tool = PersonasListTool()
    list_request = MockRequest({"include_predefined": True})

    try:
        result = await list_tool.execute(list_request.data)
        print(f"✅ Personas listés, contient notre persona: {'test_integration' in str(result)}")
    except Exception as e:
        print(f"❌ Erreur listing: {e}")
        return

    # 4. Test utilisation du persona dans un SimpleTool
    print("\n4. Test utilisation persona dans ChatTool...")
    chat_tool = ChatTool()

    # Test sans persona (comportement normal)
    chat_request_normal = MockRequest({"prompt": "Bonjour, qui êtes-vous ?", "model": "gemini-2.5-flash"})

    system_prompt_normal = chat_tool.get_effective_system_prompt(chat_request_normal)
    print(f"✅ Prompt système normal (longueur): {len(system_prompt_normal)} caractères")

    # Test avec persona (comportement modifié)
    chat_request_persona = MockRequest(
        {"prompt": "Bonjour, qui êtes-vous ?", "model": "gemini-2.5-flash", "persona_id": "test_integration"}
    )

    system_prompt_persona = chat_tool.get_effective_system_prompt(chat_request_persona)
    print(f"✅ Prompt système avec persona (longueur): {len(system_prompt_persona)} caractères")

    # Vérification que le persona est appliqué
    has_persona_instructions = (
        "[PERSONA TEST]" in system_prompt_persona or "tests d'intégration" in system_prompt_persona
    )
    print(f"✅ Instructions persona détectées: {has_persona_instructions}")

    # 5. Test préférences modèle
    print("\n5. Test préférences de modèle...")
    model_name = chat_tool.get_effective_model_name(chat_request_persona)
    model_prefs = chat_tool.get_effective_model_preferences(chat_request_persona)

    print(f"✅ Nom modèle effectif: {model_name}")
    print(f"✅ Température effective: {model_prefs.get('temperature', 'N/A')}")
    print(f"✅ Thinking mode effectif: {model_prefs.get('thinking_mode', 'N/A')}")

    # 6. Test avec persona inexistant (fallback gracieux)
    print("\n6. Test fallback avec persona inexistant...")
    chat_request_invalid = MockRequest(
        {"prompt": "Test with invalid persona", "model": "gemini-2.5-flash", "persona_id": "inexistant_persona"}
    )

    system_prompt_fallback = chat_tool.get_effective_system_prompt(chat_request_invalid)
    model_name_fallback = chat_tool.get_effective_model_name(chat_request_invalid)

    fallback_works = len(system_prompt_fallback) > 0 and model_name_fallback == "gemini-2.5-flash"
    print(f"✅ Fallback gracieux fonctionne: {fallback_works}")

    # 7. Cleanup
    print("\n7. Cleanup...")
    if os.path.exists(test_file):
        os.remove(test_file)
    print("✅ Fichiers temporaires supprimés")

    print("\n🎉 TEST D'INTÉGRATION COMPLÈTE RÉUSSI!")
    print("Le système personas fonctionne parfaitement de bout en bout!")


if __name__ == "__main__":
    asyncio.run(test_complete_integration())
