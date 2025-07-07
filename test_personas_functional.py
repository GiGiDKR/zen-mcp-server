"""
Tests fonctionnels pour les outils personas - approche simplifiée.

Ces tests vérifient que nos outils MCP fonctionnent correctement
sans interferer avec le singleton PersonaManager.
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from personas.tools import (
    PersonasCreateTool,
    PersonasDeleteTool,
    PersonasListTool,
    PersonasSelectTool,
    PersonasUpdateTool,
)


async def test_tools_functionality():
    """Test fonctionnel des outils personas"""
    print("=== TESTS FONCTIONNELS OUTILS PERSONAS ===\n")

    # Test 1: Vérifier que tous les outils peuvent être créés
    print("1. Test de création des outils...")
    try:
        tools = {
            "list": PersonasListTool(),
            "create": PersonasCreateTool(),
            "update": PersonasUpdateTool(),
            "delete": PersonasDeleteTool(),
            "select": PersonasSelectTool(),
        }
        print(f"✅ {len(tools)} outils créés avec succès")
    except Exception as e:
        print(f"❌ Erreur création outils: {e}")
        return False

    # Test 2: Vérifier les métadonnées des outils
    print("\n2. Test des métadonnées des outils...")
    try:
        for _name, tool in tools.items():
            tool_name = tool.get_name()
            description = tool.get_description()
            required_fields = tool.get_required_fields()
            tool_fields = tool.get_tool_fields()

            print(f"  - {_name}:")
            print(f"    Name: {tool_name}")
            print(f"    Required fields: {required_fields}")
            print(f"    Total fields: {len(tool_fields)}")

            # Vérifications basiques
            assert tool_name.startswith("personas_")
            assert len(description) > 10
            assert isinstance(required_fields, list)
            assert isinstance(tool_fields, dict)

        print("✅ Toutes les métadonnées sont valides")
    except Exception as e:
        print(f"❌ Erreur métadonnées: {e}")
        return False

    # Test 3: Test des champs requis
    print("\n3. Test des champs requis...")
    try:
        expected_required = {
            "list": [],
            "create": ["id", "name", "description", "system_instructions"],
            "update": ["id"],
            "delete": ["id"],
            "select": ["id"],
        }
        for _name, tool in tools.items():
            required = tool.get_required_fields()
            expected = expected_required[_name]

            if set(required) != set(expected):
                print(f"❌ Champs requis incorrects pour {_name}")
                print(f"   Attendu: {expected}")
                print(f"   Trouvé: {required}")
                return False

        print("✅ Tous les champs requis sont corrects")
    except Exception as e:
        print(f"❌ Erreur champs requis: {e}")
        return False

    # Test 4: Test des types de champs
    print("\n4. Test des types de champs...")
    try:
        for _name, tool in tools.items():
            fields = tool.get_tool_fields()

            for field_name, field_config in fields.items():
                # Vérifier que chaque champ a un type
                assert "type" in field_config, f"Champ {field_name} sans type"
                assert "description" in field_config, f"Champ {field_name} sans description"

                # Vérifier les types valides
                valid_types = {"string", "integer", "number", "boolean", "array", "object"}
                assert field_config["type"] in valid_types, f"Type invalide: {field_config['type']}"

        print("✅ Tous les types de champs sont valides")
    except Exception as e:
        print(f"❌ Erreur types de champs: {e}")
        return False

    # Test 5: Test de compatibilité avec MCP
    print("\n5. Test de compatibilité MCP...")
    try:
        # Simuler une structure de données MCP
        for _name, tool in tools.items():
            mcp_tool_def = {
                "name": tool.get_name(),
                "description": tool.get_description(),
                "inputSchema": {
                    "type": "object",
                    "properties": tool.get_tool_fields(),
                    "required": tool.get_required_fields(),
                },
            }

            # Vérifications basiques MCP
            assert isinstance(mcp_tool_def["name"], str)
            assert isinstance(mcp_tool_def["description"], str)
            assert isinstance(mcp_tool_def["inputSchema"], dict)
            assert "type" in mcp_tool_def["inputSchema"]
            assert "properties" in mcp_tool_def["inputSchema"]
            assert "required" in mcp_tool_def["inputSchema"]

        print("✅ Compatibilité MCP validée")
    except Exception as e:
        print(f"❌ Erreur compatibilité MCP: {e}")
        return False

    return True


async def test_server_integration():
    """Test d'intégration avec le serveur"""
    print("\n=== TEST INTÉGRATION SERVEUR ===\n")

    try:
        from server import TOOLS

        # Vérifier que nos outils sont présents
        expected_personas_tools = {
            "personas_list",
            "personas_create",
            "personas_update",
            "personas_delete",
            "personas_select",
        }

        found_personas_tools = {name for name in TOOLS.keys() if name.startswith("personas_")}

        print(f"Outils personas attendus: {expected_personas_tools}")
        print(f"Outils personas trouvés: {found_personas_tools}")

        missing = expected_personas_tools - found_personas_tools
        extra = found_personas_tools - expected_personas_tools

        if missing:
            print(f"❌ Outils manquants: {missing}")
            return False

        if extra:
            print(f"⚠️ Outils supplémentaires: {extra}")

        # Vérifier que chaque outil peut être instancié depuis le serveur
        for tool_name in expected_personas_tools:
            tool_instance = TOOLS[tool_name]
            assert hasattr(tool_instance, "get_name")
            assert hasattr(tool_instance, "get_description")
            assert tool_instance.get_name() == tool_name

        print("✅ Tous les outils personas sont correctement intégrés dans le serveur")
        print(f"✅ Total outils serveur: {len(TOOLS)}")

        return True

    except Exception as e:
        print(f"❌ Erreur intégration serveur: {e}")
        return False


async def main():
    """Fonction principale des tests"""
    print("🚀 DÉMARRAGE DES TESTS PERSONAS FONCTIONNELS\n")

    # Test 1: Fonctionnalité des outils
    tools_ok = await test_tools_functionality()

    # Test 2: Intégration serveur
    server_ok = await test_server_integration()

    # Résumé final
    print("\n=== RÉSUMÉ FINAL ===")
    print(f"🔧 Tests fonctionnels outils: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"🖥️ Tests intégration serveur: {'✅ PASS' if server_ok else '❌ FAIL'}")

    if tools_ok and server_ok:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("✨ Le module personas est prêt pour utilisation!")
        print("\n📝 Outils disponibles:")
        print("   - personas_list: Lister les personas disponibles")
        print("   - personas_create: Créer un nouveau persona")
        print("   - personas_update: Modifier un persona existant")
        print("   - personas_delete: Supprimer un persona")
        print("   - personas_select: Sélectionner et activer un persona")
        return True
    else:
        print("\n💥 ÉCHECS DÉTECTÉS!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
