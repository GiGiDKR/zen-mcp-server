"""
Tests unitaires pour le module personas.

Ces tests vérifient le fonctionnement des outils MCP personas.
"""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

# Ajouter le répertoire parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from personas.manager import PersonaManager
from personas.models import ModelPreferences, Persona
from personas.tools import (
    PersonasCreateTool,
    PersonasDeleteTool,
    PersonasListTool,
    PersonasSelectTool,
    PersonasUpdateTool,
)


class TestPersonasTools(unittest.TestCase):
    """Tests pour les outils personas"""

    def setUp(self):
        """Setup pour chaque test"""
        # Créer un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        self.personas_file = Path(self.test_dir) / "test_personas.json"

        # Réinitialiser le singleton avec notre fichier de test
        PersonaManager._instance = None
        PersonaManager._lock = None
        self.manager = PersonaManager.get_instance(str(self.personas_file))

        # Créer les outils
        self.list_tool = PersonasListTool()
        self.create_tool = PersonasCreateTool()
        self.update_tool = PersonasUpdateTool()
        self.delete_tool = PersonasDeleteTool()
        self.select_tool = PersonasSelectTool()

    def tearDown(self):
        """Cleanup après chaque test"""
        # Réinitialiser le singleton
        PersonaManager._instance = None
        PersonaManager._lock = None

    def test_list_tool_empty(self):
        """Test de l'outil list avec aucun persona custom"""
        # Les personas prédéfinis devraient être présents
        personas = self.manager.list_personas()
        self.assertGreaterEqual(len(personas), 3)  # Au moins les 3 prédéfinis

    def test_create_tool_basic(self):
        """Test de création d'un persona basique"""
        # Compter les personas avant
        before_count = len(self.manager.list_personas())

        # Créer un persona de test
        test_persona = Persona(
            id="test_persona",
            name="Test Persona",
            description="Un persona de test",
            system_instructions="Tu es un assistant de test spécialisé dans les tests unitaires.",
            model_preferences=ModelPreferences(model_name="gemini-2.5-flash", temperature=0.3),
            tags=["test", "development"],
        )

        # Créer le persona
        success = self.manager.create_persona(test_persona)
        self.assertTrue(success)

        # Vérifier qu'il a été créé
        after_count = len(self.manager.list_personas())
        self.assertEqual(after_count, before_count + 1)

        # Vérifier qu'on peut le récupérer
        retrieved = self.manager.get_persona("test_persona")
        self.assertEqual(retrieved.name, "Test Persona")
        self.assertEqual(retrieved.model_preferences.temperature, 0.3)

    def test_update_tool_basic(self):
        """Test de mise à jour d'un persona"""
        # Créer un persona de test d'abord
        test_persona = Persona(
            id="update_test",
            name="Original Name",
            description="Original description",
            system_instructions="Original instructions",
            tags=["original"],
        )
        self.manager.create_persona(test_persona)

        # Mettre à jour
        update_data = {"name": "Updated Name", "description": "Updated description"}
        success = self.manager.update_persona(
            "update_test", update_data, add_tags=["updated"], remove_tags=["original"]
        )
        self.assertTrue(success)

        # Vérifier les modifications
        updated = self.manager.get_persona("update_test")
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.description, "Updated description")
        self.assertIn("updated", updated.tags)
        self.assertNotIn("original", updated.tags)

    def test_delete_tool_basic(self):
        """Test de suppression d'un persona"""
        # Créer un persona de test
        test_persona = Persona(
            id="delete_test", name="To Delete", description="Will be deleted", system_instructions="Test instructions"
        )
        self.manager.create_persona(test_persona)

        # Vérifier qu'il existe
        self.assertTrue(self.manager.exists("delete_test"))

        # Le supprimer
        success = self.manager.delete_persona("delete_test")
        self.assertTrue(success)

        # Vérifier qu'il n'existe plus
        self.assertFalse(self.manager.exists("delete_test"))

    def test_tool_names(self):
        """Test que les noms d'outils sont corrects"""
        self.assertEqual(self.list_tool.get_name(), "personas_list")
        self.assertEqual(self.create_tool.get_name(), "personas_create")
        self.assertEqual(self.update_tool.get_name(), "personas_update")
        self.assertEqual(self.delete_tool.get_name(), "personas_delete")
        self.assertEqual(self.select_tool.get_name(), "personas_select")

    def test_tool_required_fields(self):
        """Test que les champs requis sont corrects"""
        # List tool - pas de champs requis
        self.assertEqual(self.list_tool.get_required_fields(), [])

        # Create tool - tous les champs de base requis
        create_required = self.create_tool.get_required_fields()
        expected_create = ["id", "name", "description", "system_instructions"]
        self.assertEqual(set(create_required), set(expected_create))

        # Update tool - seul l'ID est requis
        self.assertEqual(self.update_tool.get_required_fields(), ["id"])

        # Delete tool - seul l'ID est requis
        self.assertEqual(self.delete_tool.get_required_fields(), ["id"])

        # Select tool - seul l'ID est requis
        self.assertEqual(self.select_tool.get_required_fields(), ["id"])


async def run_async_tests():
    """Execute les tests qui nécessitent async"""
    print("Running async integration tests...")

    # Test qu'on peut créer les outils sans erreur
    try:
        list_tool = PersonasListTool()
        create_tool = PersonasCreateTool()

        # Test que les tool fields sont valides
        list_fields = list_tool.get_tool_fields()
        create_fields = create_tool.get_tool_fields()

        print(f"✅ PersonasListTool fields: {len(list_fields)}")
        print(f"✅ PersonasCreateTool fields: {len(create_fields)}")

        # Test descriptions
        print(f"✅ List description: {list_tool.get_description()[:50]}...")
        print(f"✅ Create description: {create_tool.get_description()[:50]}...")

        print("✅ All async tests passed!")

    except Exception as e:
        print(f"❌ Async test failed: {e}")
        raise


if __name__ == "__main__":
    # Executer les tests sync
    print("Running synchronous unit tests...")
    unittest.main(verbosity=2, exit=False)

    # Executer les tests async
    asyncio.run(run_async_tests())
