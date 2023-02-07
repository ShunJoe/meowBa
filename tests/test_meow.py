
import unittest
 
from typing import Any, Union, Tuple

from core.correctness.vars import SWEEP_STOP, SWEEP_JUMP, SWEEP_START
from core.meow import BasePattern, BaseRecipe, BaseRule, BaseMonitor, \
    BaseHandler, BaseConductor, create_rules, create_rule
from patterns import FileEventPattern
from recipes.jupyter_notebook_recipe import JupyterNotebookRecipe
from shared import setup, teardown, BAREBONES_NOTEBOOK

valid_pattern_one = FileEventPattern(
    "pattern_one", "path_one", "recipe_one", "file_one")
valid_pattern_two = FileEventPattern(
    "pattern_two", "path_two", "recipe_two", "file_two")

valid_recipe_one = JupyterNotebookRecipe(
    "recipe_one", BAREBONES_NOTEBOOK)
valid_recipe_two = JupyterNotebookRecipe(
    "recipe_two", BAREBONES_NOTEBOOK)


class MeowTests(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()

    # Test that BaseRecipe instantiation
    def testBaseRecipe(self)->None:
        with self.assertRaises(TypeError):
            BaseRecipe("name", "")
        
        class NewRecipe(BaseRecipe):
            pass
        with self.assertRaises(NotImplementedError):
            NewRecipe("name", "")

        class FullRecipe(BaseRecipe):
            def _is_valid_recipe(self, recipe:Any)->None:
                pass
            def _is_valid_parameters(self, parameters:Any)->None:
                pass
            def _is_valid_requirements(self, requirements:Any)->None:
                pass
        FullRecipe("name", "")

    # Test that BaseRecipe instantiation
    def testBasePattern(self)->None:
        with self.assertRaises(TypeError):
            BasePattern("name", "", "", "")

        class NewPattern(BasePattern):
            pass
        with self.assertRaises(NotImplementedError):
            NewPattern("name", "", "", "")

        class FullPattern(BasePattern):
            def _is_valid_recipe(self, recipe:Any)->None:
                pass
            def _is_valid_parameters(self, parameters:Any)->None:
                pass
            def _is_valid_output(self, outputs:Any)->None:
                pass
            def _is_valid_sweep(self, 
                    sweep:dict[str,Union[int,float,complex]])->None:
                pass
        FullPattern("name", "", "", "", "")

    # Test expansion of parameter sweeps
    def testBasePatternExpandSweeps(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", "A", "recipe_one", "file_one", sweep={
                "s1":{
                    SWEEP_START: 10, SWEEP_STOP: 20, SWEEP_JUMP:5
                }
            })

        es = pattern_one.expand_sweeps()

        self.assertIsInstance(es, list)
        self.assertEqual(len(es), 3)

        values = [
            "s1-10", "s1-15", "s1-20", 
        ]

        for sweep_vals in es:
            self.assertIsInstance(sweep_vals, tuple)
            self.assertEqual(len(sweep_vals), 1)

            val1 = None
            for sweep_val in sweep_vals:
                self.assertIsInstance(sweep_val, tuple)
                self.assertEqual(len(sweep_val), 2)
                if sweep_val[0] == "s1":
                    val1 = f"s1-{sweep_val[1]}"
            if val1:
                values.remove(val1)
        self.assertEqual(len(values), 0)

        pattern_one = FileEventPattern(
            "pattern_one", "A", "recipe_one", "file_one", sweep={
                "s1":{
                    SWEEP_START: 0, SWEEP_STOP: 2, SWEEP_JUMP:1
                },
                "s2":{
                    SWEEP_START: 20, SWEEP_STOP: 80, SWEEP_JUMP:15
                }
            })

        es = pattern_one.expand_sweeps()

        self.assertIsInstance(es, list)
        self.assertEqual(len(es), 15)

        values = [
            "s1-0/s2-20", "s1-1/s2-20", "s1-2/s2-20", 
            "s1-0/s2-35", "s1-1/s2-35", "s1-2/s2-35", 
            "s1-0/s2-50", "s1-1/s2-50", "s1-2/s2-50", 
            "s1-0/s2-65", "s1-1/s2-65", "s1-2/s2-65", 
            "s1-0/s2-80", "s1-1/s2-80", "s1-2/s2-80", 
        ]

        for sweep_vals in es:
            self.assertIsInstance(sweep_vals, tuple)
            self.assertEqual(len(sweep_vals), 2)

            val1 = None
            val2 = None
            for sweep_val in sweep_vals:
                self.assertIsInstance(sweep_val, tuple)
                self.assertEqual(len(sweep_val), 2)
                if sweep_val[0] == "s1":
                    val1 = f"s1-{sweep_val[1]}"
                if sweep_val[0] == "s2":
                    val2 = f"s2-{sweep_val[1]}"
            if val1 and val2:
                values.remove(f"{val1}/{val2}")
        self.assertEqual(len(values), 0)

    # Test that BaseRecipe instantiation
    def testBaseRule(self)->None:
        with self.assertRaises(TypeError):
            BaseRule("name", "", "")

        class NewRule(BaseRule):
            pass
        with self.assertRaises(NotImplementedError):
            NewRule("name", "", "")

        class FullRule(BaseRule):
            pattern_type = "pattern"
            recipe_type = "recipe"
            def _is_valid_recipe(self, recipe:Any)->None:
                pass
            def _is_valid_pattern(self, pattern:Any)->None:
                pass
        FullRule("name", valid_pattern_one, valid_recipe_one)

    # Test that create_rule creates a rule from pattern and recipe
    def testCreateRule(self)->None:
        rule = create_rule(valid_pattern_one, valid_recipe_one)

        self.assertIsInstance(rule, BaseRule)

        with self.assertRaises(ValueError):
            rule = create_rule(valid_pattern_one, valid_recipe_two)
    
    # Test that create_rules creates nothing from nothing
    def testCreateRulesMinimum(self)->None:
        rules = create_rules({}, {})

        self.assertEqual(len(rules), 0)

    # Test that create_rules creates rules from patterns and recipes
    def testCreateRulesPatternsAndRecipesDicts(self)->None:
        patterns = {
            valid_pattern_one.name: valid_pattern_one,
            valid_pattern_two.name: valid_pattern_two
        }
        recipes = {
            valid_recipe_one.name: valid_recipe_one,
            valid_recipe_two.name: valid_recipe_two
        }
        rules = create_rules(patterns, recipes)
        self.assertIsInstance(rules, dict)
        self.assertEqual(len(rules), 2)
        for k, rule in rules.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(rule, BaseRule)
            self.assertEqual(k, rule.name)

    # Test that create_rules creates nothing from invalid pattern inputs
    def testCreateRulesMisindexedPatterns(self)->None:
        patterns = {
            valid_pattern_two.name: valid_pattern_one,
            valid_pattern_one.name: valid_pattern_two
        }
        with self.assertRaises(KeyError):
            create_rules(patterns, {})

    # Test that create_rules creates nothing from invalid recipe inputs
    def testCreateRulesMisindexedRecipes(self)->None:
        recipes = {
            valid_recipe_two.name: valid_recipe_one,
            valid_recipe_one.name: valid_recipe_two
        }
        with self.assertRaises(KeyError):
            create_rules({}, recipes)

    # Test that BaseMonitor instantiation
    def testBaseMonitor(self)->None:
        with self.assertRaises(TypeError):
            BaseMonitor({}, {})

        class TestMonitor(BaseMonitor):
            pass

        with self.assertRaises(NotImplementedError):
            TestMonitor({}, {})

        class FullTestMonitor(BaseMonitor):
            def start(self):
                pass
            def stop(self):
                pass
            def _is_valid_patterns(self, patterns:dict[str,BasePattern])->None:
                pass
            def _is_valid_recipes(self, recipes:dict[str,BaseRecipe])->None:
                pass
            def add_pattern(self, pattern:BasePattern)->None:
                pass
            def update_pattern(self, pattern:BasePattern)->None:
                pass
            def remove_pattern(self, pattern:Union[str,BasePattern])->None:
                pass
            def get_patterns(self)->None:
                pass
            def add_recipe(self, recipe:BaseRecipe)->None:
                pass
            def update_recipe(self, recipe:BaseRecipe)->None:
                pass
            def remove_recipe(self, recipe:Union[str,BaseRecipe])->None:
                pass
            def get_recipes(self)->None:
                pass
            def get_rules(self)->None:
                pass
            
        FullTestMonitor({}, {})

    # Test that BaseHandler instantiation
    def testBaseHandler(self)->None:
        with self.assertRaises(TypeError):
            BaseHandler()

        class TestHandler(BaseHandler):
            pass

        with self.assertRaises(NotImplementedError):
            TestHandler()

        class FullTestHandler(BaseHandler):
            def handle(self, event):
                pass
            def start(self):
                pass
            def stop(self):
                pass
            def _is_valid_inputs(self, inputs:Any)->None:
                pass
            def valid_handle_criteria(self, event:dict[str,Any]
                    )->Tuple[bool,str]:
                pass

        FullTestHandler()

    # Test that BaseConductor instantiation
    def testBaseConductor(self)->None:
        with self.assertRaises(TypeError):
            BaseConductor()

        class TestConductor(BaseConductor):
            pass

        with self.assertRaises(NotImplementedError):
            TestConductor()

        class FullTestConductor(BaseConductor):
            def execute(self, job:dict[str,Any])->None:
                pass

            def valid_execute_criteria(self, job:dict[str,Any]
                    )->Tuple[bool,str]:
                pass

        FullTestConductor()
