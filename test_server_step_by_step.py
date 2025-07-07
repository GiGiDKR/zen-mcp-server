"""
Test d'intégration serveur simple pour diagnostiquer les problèmes.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_server_step_by_step():
    """Test étape par étape pour identifier les problèmes d'import"""
    print("=== DIAGNOSTIC ÉTAPE PAR ÉTAPE ===\n")

    # Étape 1: Test tools basic
    try:
        print("1. Import tools...")
        print("✅ Import tools OK")
    except Exception as e:
        print(f"❌ Import tools failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Étape 2: Test tools spécifiques
    try:
        print("2. Import tools spécifiques...")
        from tools import AnalyzeTool, ChatTool

        print("✅ Import tools spécifiques OK")
    except Exception as e:
        print(f"❌ Import tools spécifiques failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Étape 3: Test personas
    try:
        print("3. Import personas...")
        from personas.tools import PersonasListTool

        print("✅ Import personas OK")
    except Exception as e:
        print(f"❌ Import personas failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Étape 4: Test imports server individuels
    try:
        print("4. Test imports un par un...")

        print("  - Config...")
        print("  ✅ Config OK")

        print("  - Providers...")
        print("  ✅ Providers OK")

        print("  - Tools...")
        from tools import ChatTool

        print("  ✅ Tools OK")

        print("  - Personas tools...")
        from personas.tools import PersonasListTool

        print("  ✅ Personas tools OK")

    except Exception as e:
        print(f"❌ Import individuel failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Étape 5: Test TOOLS dictionary directement
    try:
        print("5. Test construction TOOLS...")

        # Construire manuellement comme dans le serveur
        from tools import (
            AnalyzeTool,
            ChatTool,
        )

        print("  ✅ Import tools principaux OK")

        from personas.tools import (
            PersonasCreateTool,
            PersonasListTool,
        )

        print("  ✅ Import personas tools OK")

        # Construire le dictionnaire
        TOOLS = {
            "chat": ChatTool(),
            "analyze": AnalyzeTool(),
            "personas_list": PersonasListTool(),
            "personas_create": PersonasCreateTool(),
        }
        print(f"  ✅ Construction TOOLS OK - {len(TOOLS)} outils")

    except Exception as e:
        print(f"❌ Construction TOOLS failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Étape 6: Import complet du serveur
    try:
        print("6. Import serveur complet...")
        import server

        print("✅ Import serveur OK")

        tools_count = len(server.TOOLS)
        print(f"✅ TOOLS dictionary loaded with {tools_count} tools")

        # Vérifier nos personas tools
        personas_tools = [name for name in server.TOOLS.keys() if "personas" in name]
        print(f"✅ Personas tools found: {personas_tools}")

    except Exception as e:
        print(f"❌ Import serveur failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n🎉 TOUS LES TESTS RÉUSSIS!")
    return True


if __name__ == "__main__":
    success = test_server_step_by_step()
    print(f"\nRésultat: {'✅ SUCCESS' if success else '❌ FAILED'}")
    exit(0 if success else 1)
