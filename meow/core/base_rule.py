
"""
This file contains the base MEOW rule defintion. This should be inherited from 
for all rule instances.

Author(s): David Marchant
"""

from sys import modules
from typing import Any

if "BasePattern" not in modules:
    from core.base_pattern import BasePattern
if "BaseRecipe" not in modules:
    from core.base_recipe import BaseRecipe
from core.correctness.vars import get_drt_imp_msg, VALID_RULE_NAME_CHARS
from core.correctness.validation import valid_string, check_type, \
    check_implementation


class BaseRule:
    # A unique identifier for the rule
    name:str
    # A pattern to be used in rule triggering
    pattern:BasePattern
    # A recipe to be used in rule execution
    recipe:BaseRecipe
    # The string name of the pattern class that can be used to create this rule
    pattern_type:str=""
    # The string name of the recipe class that can be used to create this rule
    recipe_type:str=""
    def __init__(self, name:str, pattern:BasePattern, recipe:BaseRecipe):
        """BaseRule Constructor. This will check that any class inheriting 
        from it implements its validation functions. It will then call these on
        the input parameters."""
        check_implementation(type(self)._is_valid_pattern, BaseRule)
        check_implementation(type(self)._is_valid_recipe, BaseRule)
        self.__check_types_set()
        self._is_valid_name(name)
        self.name = name
        self._is_valid_pattern(pattern)
        self.pattern = pattern
        self._is_valid_recipe(recipe)
        self.recipe = recipe
        check_type(pattern, BasePattern, hint="BaseRule.pattern")
        check_type(recipe, BaseRecipe, hint="BaseRule.recipe")
        if pattern.recipe != recipe.name:
            raise ValueError(f"Cannot create Rule {name}. Pattern "
                f"{pattern.name} does not identify Recipe {recipe.name}. It "
                f"uses {pattern.recipe}")

    def __new__(cls, *args, **kwargs):
        """A check that this base class is not instantiated itself, only 
        inherited from"""
        if cls is BaseRule:
            msg = get_drt_imp_msg(BaseRule)
            raise TypeError(msg)
        return object.__new__(cls)

    def _is_valid_name(self, name:str)->None:
        """Validation check for 'name' variable from main constructor. Is 
        automatically called during initialisation. This does not need to be 
        overridden by child classes."""
        valid_string(name, VALID_RULE_NAME_CHARS)

    def _is_valid_pattern(self, pattern:Any)->None:
        """Validation check for 'pattern' variable from main constructor. Must 
        be implemented by any child class."""
        pass

    def _is_valid_recipe(self, recipe:Any)->None:
        """Validation check for 'recipe' variable from main constructor. Must 
        be implemented by any child class."""
        pass

    def __check_types_set(self)->None:
        """Validation check that the self.pattern_type and self.recipe_type 
        attributes have been set in a child class."""
        if self.pattern_type == "":
            raise AttributeError(f"Rule Class '{self.__class__.__name__}' "
                "does not set a pattern_type.")
        if self.recipe_type == "":
            raise AttributeError(f"Rule Class '{self.__class__.__name__}' "
                "does not set a recipe_type.")
