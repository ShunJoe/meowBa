
import unittest

from patterns.file_event_pattern import FileEventPattern
from recipes.jupyter_notebook_recipe import JupyterNotebookRecipe
from rules.file_event_jupyter_notebook_rule import FileEventJupyterNotebookRule
from shared import setup, teardown, BAREBONES_NOTEBOOK

class CorrectnessTests(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()
        
    # Test FileEventJupyterNotebookRule created from valid pattern and recipe
    def testFileEventJupyterNotebookRuleCreationMinimum(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        FileEventJupyterNotebookRule("name", fep, jnr)

    # Test FileEventJupyterNotebookRule not created with empty name
    def testFileEventJupyterNotebookRuleCreationNoName(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        with self.assertRaises(ValueError):
            FileEventJupyterNotebookRule("", fep, jnr)

    # Test FileEventJupyterNotebookRule not created with invalid name
    def testFileEventJupyterNotebookRuleCreationInvalidName(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        with self.assertRaises(TypeError):
            FileEventJupyterNotebookRule(1, fep, jnr)

    # Test FileEventJupyterNotebookRule not created with invalid pattern
    def testFileEventJupyterNotebookRuleCreationInvalidPattern(self)->None:
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        with self.assertRaises(TypeError):
            FileEventJupyterNotebookRule("name", "pattern", jnr)

    # Test FileEventJupyterNotebookRule not created with invalid recipe
    def testFileEventJupyterNotebookRuleCreationInvalidRecipe(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")

        with self.assertRaises(TypeError):
            FileEventJupyterNotebookRule("name", fep, "recipe")

    # Test FileEventJupyterNotebookRule not created with mismatched recipe
    def testFileEventJupyterNotebookRuleCreationMissmatchedRecipe(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("test_recipe", BAREBONES_NOTEBOOK)

        with self.assertRaises(ValueError):
            FileEventJupyterNotebookRule("name", fep, jnr)

    # Test FileEventJupyterNotebookRule created with valid name
    def testFileEventJupyterNotebookRuleSetupName(self)->None:
        name = "name"
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        fejnr = FileEventJupyterNotebookRule(name, fep, jnr)

        self.assertEqual(fejnr.name, name)

    # Test FileEventJupyterNotebookRule not created with valid pattern
    def testFileEventJupyterNotebookRuleSetupPattern(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        fejnr = FileEventJupyterNotebookRule("name", fep, jnr)

        self.assertEqual(fejnr.pattern, fep)

    # Test FileEventJupyterNotebookRule not created with valid recipe
    def testFileEventJupyterNotebookRuleSetupRecipe(self)->None:
        fep = FileEventPattern("name", "path", "recipe", "file")
        jnr = JupyterNotebookRecipe("recipe", BAREBONES_NOTEBOOK)

        fejnr = FileEventJupyterNotebookRule("name", fep, jnr)

        self.assertEqual(fejnr.recipe, jnr)

