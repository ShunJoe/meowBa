
"""
This file contains the base MEOW monitor defintion. This should be inherited 
from for all monitor instances.

Author(s): David Marchant
"""

from copy import deepcopy
from typing import Union, Dict

from core.base_pattern import BasePattern
from core.base_recipe import BaseRecipe
from core.base_rule import BaseRule
from core.correctness.vars import get_drt_imp_msg, VALID_CHANNELS
from core.correctness.validation import check_implementation
from functionality.meow import create_rules


class BaseMonitor:
    # A collection of patterns
    _patterns: Dict[str, BasePattern]
    # A collection of recipes
    _recipes: Dict[str, BaseRecipe]
    # A collection of rules derived from _patterns and _recipes
    _rules: Dict[str, BaseRule]
    # A channel for sending messages to the runner. Note that this is not 
    # initialised within the constructor, but within the runner when passed the
    # monitor is passed to it.
    to_runner: VALID_CHANNELS
    def __init__(self, patterns:Dict[str,BasePattern], 
            recipes:Dict[str,BaseRecipe])->None:
        """BaseMonitor Constructor. This will check that any class inheriting 
        from it implements its validation functions. It will then call these on
        the input parameters."""
        check_implementation(type(self).start, BaseMonitor)
        check_implementation(type(self).stop, BaseMonitor)
        check_implementation(type(self)._is_valid_patterns, BaseMonitor)
        self._is_valid_patterns(patterns)
        check_implementation(type(self)._is_valid_recipes, BaseMonitor)
        self._is_valid_recipes(recipes)
        check_implementation(type(self).add_pattern, BaseMonitor)
        check_implementation(type(self).update_pattern, BaseMonitor)
        check_implementation(type(self).remove_pattern, BaseMonitor)
        check_implementation(type(self).get_patterns, BaseMonitor)
        check_implementation(type(self).add_recipe, BaseMonitor)
        check_implementation(type(self).update_recipe, BaseMonitor)
        check_implementation(type(self).remove_recipe, BaseMonitor)
        check_implementation(type(self).get_recipes, BaseMonitor)
        check_implementation(type(self).get_rules, BaseMonitor)
        # Ensure that patterns and recipes cannot be trivially modified from 
        # outside the monitor, as this will cause internal consistency issues
        self._patterns = deepcopy(patterns)
        self._recipes = deepcopy(recipes)
        self._rules = create_rules(patterns, recipes)
        
    def __new__(cls, *args, **kwargs):
        """A check that this base class is not instantiated itself, only 
        inherited from"""
        if cls is BaseMonitor:
            msg = get_drt_imp_msg(BaseMonitor)
            raise TypeError(msg)
        return object.__new__(cls)

    def _is_valid_patterns(self, patterns:Dict[str,BasePattern])->None:
        """Validation check for 'patterns' variable from main constructor. Must
        be implemented by any child class."""
        pass

    def _is_valid_recipes(self, recipes:Dict[str,BaseRecipe])->None:
        """Validation check for 'recipes' variable from main constructor. Must 
        be implemented by any child class."""
        pass

    def start(self)->None:
        """Function to start the monitor as an ongoing process/thread. Must be 
        implemented by any child process"""
        pass

    def stop(self)->None:
        """Function to stop the monitor as an ongoing process/thread. Must be 
        implemented by any child process"""
        pass

    def add_pattern(self, pattern:BasePattern)->None:
        """Function to add a pattern to the current definitions. Must be 
        implemented by any child process."""
        pass

    def update_pattern(self, pattern:BasePattern)->None:
        """Function to update a pattern in the current definitions. Must be 
        implemented by any child process."""
        pass

    def remove_pattern(self, pattern:Union[str,BasePattern])->None:
        """Function to remove a pattern from the current definitions. Must be 
        implemented by any child process."""
        pass

    def get_patterns(self)->Dict[str,BasePattern]:
        """Function to get a dictionary of all current pattern definitions. 
        Must be implemented by any child process."""
        pass

    def add_recipe(self, recipe:BaseRecipe)->None:
        """Function to add a recipe to the current definitions. Must be 
        implemented by any child process."""
        pass

    def update_recipe(self, recipe:BaseRecipe)->None:
        """Function to update a recipe in the current definitions. Must be 
        implemented by any child process."""
        pass

    def remove_recipe(self, recipe:Union[str,BaseRecipe])->None:
        """Function to remove a recipe from the current definitions. Must be 
        implemented by any child process."""
        pass

    def get_recipes(self)->Dict[str,BaseRecipe]:
        """Function to get a dictionary of all current recipe definitions. 
        Must be implemented by any child process."""
        pass

    def get_rules(self)->Dict[str,BaseRule]:
        """Function to get a dictionary of all current rule definitions. 
        Must be implemented by any child process."""
        pass
