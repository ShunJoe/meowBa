
"""
This file contains definitions for a MEOW rule connecting the FileEventPattern
and PythonRecipe.

Author(s): David Marchant
"""
from core.correctness.validation import check_type
from core.meow import BaseRule
from patterns.file_event_pattern import FileEventPattern
from recipes.python_recipe import PythonRecipe

# TODO potentailly remove this and just invoke BaseRule directly, as does not
# add any functionality other than some validation.
class FileEventPythonRule(BaseRule):
    pattern_type = "FileEventPattern"
    recipe_type = "PythonRecipe" 
    def __init__(self, name: str, pattern:FileEventPattern, 
            recipe:PythonRecipe):
        super().__init__(name, pattern, recipe)

    def _is_valid_pattern(self, pattern:FileEventPattern)->None:
        """Validation check for 'pattern' variable from main constructor. Is 
        automatically called during initialisation."""
        check_type(
            pattern, 
            FileEventPattern,
            hint="FileEventPythonRule.pattern"
        )

    def _is_valid_recipe(self, recipe:PythonRecipe)->None:
        """Validation check for 'recipe' variable from main constructor. Is 
        automatically called during initialisation."""
        check_type(
            recipe, 
            PythonRecipe,
            hint="FileEventPythonRule.recipe"
        )
