"""
Test simple pour vérifier le bon fonctionnement des outils personas.
"""

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


def test_tools_instantiation():
    """Test que tous les outils peuvent être instanciés sans erreur"""
    print("Testing tools instantiation...")

    try:
        tools = {
            "list": PersonasListTool(),
            "create": PersonasCreateTool(),
            "update": PersonasUpdateTool(),
            "delete": PersonasDeleteTool(),
            "select": PersonasSelectTool(),
        }

        print(f"✅ Successfully created {len(tools)} tools")

        # Test que chaque outil a les bonnes méthodes
        for name, tool in tools.items():
            print(f"  - {name}: {tool.get_name()}")

            # Vérifier les méthodes essentielles
            assert hasattr(tool, "get_name")
            assert hasattr(tool, "get_description")
            assert hasattr(tool, "get_tool_fields")
            assert hasattr(tool, "get_required_fields")

        print("✅ All tools have required methods")

        # Test des champs requis
        print("\n📋 Required fields:")
        for name, tool in tools.items():
            required = tool.get_required_fields()
            print(f"  - {name}: {required}")

        # Test des tool fields
        print("\n🔧 Tool fields count:")
        for name, tool in tools.items():
            fields = tool.get_tool_fields()
            print(f"  - {name}: {len(fields)} fields")

        print("\n✅ All tools tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error testing tools: {e}")
        return False


def test_server_integration():
    """Test que les outils sont bien intégrés dans le serveur"""
    print("\nTesting server integration...")

    try:
        from server import TOOLS

        # Compter les outils personas
        personas_tools = [name for name in TOOLS.keys() if "personas" in name]

        print(f"✅ Found {len(personas_tools)} personas tools in server:")
        for tool_name in personas_tools:
            print(f"  - {tool_name}")

        expected_tools = {"personas_list", "personas_create", "personas_update", "personas_delete", "personas_select"}

        found_tools = set(personas_tools)

        if found_tools == expected_tools:
            print("✅ All expected personas tools are registered!")
            return True
        else:
            missing = expected_tools - found_tools
            extra = found_tools - expected_tools
            if missing:
                print(f"❌ Missing tools: {missing}")
            if extra:
                print(f"⚠️ Extra tools: {extra}")
            return False

    except Exception as e:
        print(f"❌ Error testing server integration: {e}")
        return False


if __name__ == "__main__":
    print("=== PERSONAS TOOLS INTEGRATION TEST ===\n")

    # Test 1: Instantiation des outils
    test1_success = test_tools_instantiation()

    # Test 2: Intégration serveur
    test2_success = test_server_integration()

    print("\n=== RÉSULTATS ===")
    print(f"🔧 Tools instantiation: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"🖥️  Server integration: {'✅ PASS' if test2_success else '❌ FAIL'}")

    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! Personas tools are ready to use!")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        sys.exit(1)
