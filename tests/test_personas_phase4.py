"""
Tests unitaires pour le module personas - Phase 4.

Ces tests vérifient le fonctionnement complet des outils MCP personas
avec validation de toutes les fonctionn        # Créer un persona avec tags spécifiques
        persona = Persona(
            id="search_test",
            name="Searchable Persona",
            description="Test searchable",
            system_instructions="Instructions système pour recherche",
            tags=["searchable", "testing"]
        )ritiques.
"""

import sys
import unittest
from pathlib import Path

# Ajouter le répertoire parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from personas.exceptions import DuplicatePersonaError
from personas.manager import PersonaManager
from personas.models import ModelPreferences, Persona


class TestPersonasModels(unittest.TestCase):
    """Tests unitaires pour les modèles Pydantic"""

    def test_persona_creation_valid(self):
        """Test création d'un persona valide"""
        persona = Persona(
            id="test_persona",
            name="Test Persona",
            description="Description de test",
            system_instructions="Instructions système de test",
            model_preferences=ModelPreferences(temperature=0.7),
            tags=["test", "unit"],
        )

        self.assertEqual(persona.id, "test_persona")
        self.assertEqual(persona.name, "Test Persona")
        self.assertEqual(persona.model_preferences.temperature, 0.7)
        self.assertIn("test", persona.tags)

    def test_persona_id_validation(self):
        """Test validation de l'ID persona"""
        with self.assertRaises(ValueError):
            Persona(
                id="invalid-id-with-dash",  # Doit échouer
                name="Test",
                description="Test",
                system_instructions="Test",
            )

    def test_model_preferences_validation(self):
        """Test validation des préférences de modèle"""
        # Temperature invalide
        with self.assertRaises(ValueError):
            ModelPreferences(temperature=1.5)  # Doit être <= 1.0

        # Thinking mode invalide
        with self.assertRaises(ValueError):
            ModelPreferences(thinking_mode="invalid")


class TestPersonaManager(unittest.TestCase):
    """Tests unitaires pour PersonaManager"""

    def setUp(self):
        """Setup pour chaque test"""
        # Réinitialiser le singleton
        PersonaManager.reset_instance()
        self.manager = PersonaManager.get_instance()

    def tearDown(self):
        """Cleanup après chaque test"""
        PersonaManager.reset_instance()

    def test_create_persona(self):
        """Test création d'un persona"""
        persona = Persona(
            id="test_create",
            name="Test Create",
            description="Test de création",
            system_instructions="Instructions de test",
            tags=["test"],
        )

        success = self.manager.create_persona(persona)
        self.assertTrue(success)
        self.assertTrue(self.manager.exists("test_create"))

    def test_duplicate_persona_creation(self):
        """Test que la création de doublons échoue"""
        persona = Persona(
            id="duplicate_test",
            name="Duplicate",
            description="Test",
            system_instructions="Instructions de test longues",
        )

        # Première création doit réussir
        success1 = self.manager.create_persona(persona)
        self.assertTrue(success1)

        # Deuxième création doit échouer avec une exception
        with self.assertRaises(DuplicatePersonaError):
            self.manager.create_persona(persona)

    def test_update_persona(self):
        """Test mise à jour d'un persona"""
        # Créer un persona
        persona = Persona(
            id="update_test",
            name="Original",
            description="Original description",
            system_instructions="Original instructions",
            tags=["original"],
        )
        self.manager.create_persona(persona)

        # Mettre à jour
        update_data = {"name": "Updated Name", "tags": ["updated"]}
        updated_persona = self.manager.update_persona("update_test", update_data)
        self.assertIsNotNone(updated_persona)

        # Vérifier les changements
        updated = self.manager.get_persona("update_test")
        self.assertEqual(updated.name, "Updated Name")
        self.assertIn("updated", updated.tags)
        # Note: pour ce test, on ne peut pas facilement tester la suppression de tag
        # car on remplace complètement la liste des tags

    def test_delete_persona(self):
        """Test suppression d'un persona"""
        persona = Persona(
            id="delete_test",
            name="To Delete",
            description="Test",
            system_instructions="Instructions de test pour suppression",
        )

        self.manager.create_persona(persona)
        self.assertTrue(self.manager.exists("delete_test"))

        success = self.manager.delete_persona("delete_test")
        self.assertTrue(success)
        self.assertFalse(self.manager.exists("delete_test"))

    def test_list_personas(self):
        """Test listing des personas"""
        # Au démarrage, on doit avoir les personas prédéfinis
        personas = self.manager.list_personas()
        self.assertGreaterEqual(len(personas), 3)  # 3 prédéfinis minimum

        # Ajouter un persona custom
        custom_persona = Persona(
            id="custom_test",
            name="Custom",
            description="Test",
            system_instructions="Instructions système personnalisées",
        )
        self.manager.create_persona(custom_persona)

        # Vérifier qu'il apparaît dans la liste
        personas_after = self.manager.list_personas()
        self.assertEqual(len(personas_after), len(personas) + 1)

    def test_search_personas(self):
        """Test recherche de personas"""
        # Créer un persona avec tags spécifiques
        persona = Persona(
            id="search_test",
            name="Searchable Persona",
            description="Test searchable",
            system_instructions="Instructions système pour recherche",
            tags=["searchable", "testing"],
        )
        self.manager.create_persona(persona)

        # Rechercher par nom
        results = self.manager.search_personas("Searchable")
        self.assertGreater(len(results), 0)
        self.assertTrue(any(p.id == "search_test" for p in results))

    def test_get_stats(self):
        """Test récupération des statistiques"""
        stats = self.manager.get_stats()

        # Vérifier que les stats ont les bonnes clés
        expected_keys = {"cache_hits", "cache_misses", "personas_created", "personas_updated", "personas_deleted"}
        self.assertTrue(expected_keys.issubset(set(stats.keys())))


class TestPersonasIntegration(unittest.TestCase):
    """Tests d'intégration pour l'ensemble du système personas"""

    def test_predefined_personas_loaded(self):
        """Test que les personas prédéfinis sont chargés"""
        # test_dir = tempfile.mkdtemp()
        # personas_file = Path(test_dir) / "integration_test.json"

        # Réinitialiser et créer un nouveau manager
        PersonaManager.reset_instance()
        # storage = JsonFileStorage(str(personas_file))
        manager = PersonaManager.get_instance()

        # Vérifier les personas prédéfinis
        personas = manager.list_personas()
        predefined_ids = {"python_expert", "system_architect", "security_reviewer"}

        found_ids = {p.id for p in personas}
        self.assertTrue(predefined_ids.issubset(found_ids))

        # Cleanup
        PersonaManager.reset_instance()

    def test_end_to_end_workflow(self):
        """Test complet d'un workflow personas"""
        # test_dir = tempfile.mkdtemp()
        # personas_file = Path(test_dir) / "e2e_test.json"

        # Réinitialiser
        PersonaManager.reset_instance()
        manager = PersonaManager.get_instance()

        # 1. Créer un persona
        persona = Persona(
            id="e2e_test",
            name="End-to-End Test",
            description="Persona pour test E2E",
            system_instructions="Tu es un assistant de test E2E",
            model_preferences=ModelPreferences(
                model_name="gemini-2.5-flash", temperature=0.5, top_p=1.0, max_tokens=1024, thinking_mode="medium"
            ),
            tags=["e2e", "test"],
        )

        self.assertTrue(manager.create_persona(persona))

        # 2. Vérifier qu'il existe
        self.assertTrue(manager.exists("e2e_test"))

        # 3. Le récupérer
        retrieved = manager.get_persona("e2e_test")
        self.assertEqual(retrieved.name, "End-to-End Test")

        # 4. Le mettre à jour
        updated_persona = manager.update_persona(
            "e2e_test", {"description": "Description mise à jour", "tags": ["e2e", "test", "updated"]}
        )
        self.assertIsNotNone(updated_persona)

        # 5. Vérifier la mise à jour
        updated = manager.get_persona("e2e_test")
        self.assertEqual(updated.description, "Description mise à jour")
        self.assertIn("updated", updated.tags)

        # 6. Le supprimer
        self.assertTrue(manager.delete_persona("e2e_test"))
        self.assertFalse(manager.exists("e2e_test"))

        # Cleanup
        PersonaManager.reset_instance()


if __name__ == "__main__":
    # Configuration des tests

    print("=== PERSONAS UNIT TESTS - PHASE 4 ===\n")

    # Exécuter tous les tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ajouter les tests par ordre de complexité
    suite.addTests(loader.loadTestsFromTestCase(TestPersonasModels))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonaManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonasIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Résumé
    print("\n=== RÉSULTATS ===")
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")

    if result.wasSuccessful():
        print("🎉 TOUS LES TESTS RÉUSSIS! Le module personas est prêt pour production!")
    else:
        print("💥 ÉCHECS DÉTECTÉS! Vérifiez les erreurs ci-dessus.")
        for failure in result.failures:
            print(f"ÉCHEC: {failure[0]}")
        for error in result.errors:
            print(f"ERREUR: {error[0]}")
