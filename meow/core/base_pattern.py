
"""
This file contains the base MEOW pattern defintion. This should be inherited 
from for all pattern instances.

Author(s): David Marchant
"""

import itertools

from typing import Any, Union, Tuple, Dict, List

from core.correctness.vars import get_drt_imp_msg, \
    VALID_PATTERN_NAME_CHARS, SWEEP_JUMP, SWEEP_START, SWEEP_STOP
from core.correctness.validation import valid_string, check_type, \
    check_implementation, valid_dict


class BasePattern:
    # A unique identifier for the pattern
    name:str
    # An identifier of a recipe
    recipe:str
    # Parameters to be overridden in the recipe
    parameters:Dict[str,Any]
    # Parameters showing the potential outputs of a recipe
    outputs:Dict[str,Any]
    # A collection of variables to be swept over for job scheduling
    sweep:Dict[str,Any]
    # TODO Add requirements to patterns
    def __init__(self, name:str, recipe:str, parameters:Dict[str,Any]={}, 
            outputs:Dict[str,Any]={}, sweep:Dict[str,Any]={}):
        """BasePattern Constructor. This will check that any class inheriting 
        from it implements its validation functions. It will then call these on
        the input parameters."""
        check_implementation(type(self)._is_valid_recipe, BasePattern)
        check_implementation(type(self)._is_valid_parameters, BasePattern)
        check_implementation(type(self)._is_valid_output, BasePattern)
        self._is_valid_name(name)
        self.name = name
        self._is_valid_recipe(recipe)
        self.recipe = recipe
        self._is_valid_parameters(parameters)
        self.parameters = parameters
        self._is_valid_output(outputs)
        self.outputs = outputs
        self._is_valid_sweep(sweep)
        self.sweep = sweep

    def __new__(cls, *args, **kwargs):
        """A check that this base class is not instantiated itself, only 
        inherited from"""
        if cls is BasePattern:
            msg = get_drt_imp_msg(BasePattern)
            raise TypeError(msg)
        return object.__new__(cls)

    def _is_valid_name(self, name:str)->None:
        """Validation check for 'name' variable from main constructor. Is 
        automatically called during initialisation. This does not need to be 
        overridden by child classes."""
        valid_string(name, VALID_PATTERN_NAME_CHARS)

    def _is_valid_recipe(self, recipe:Any)->None:
        """Validation check for 'recipe' variable from main constructor. Must 
        be implemented by any child class."""
        pass

    def _is_valid_parameters(self, parameters:Any)->None:
        """Validation check for 'parameters' variable from main constructor. 
        Must be implemented by any child class."""
        pass

    def _is_valid_output(self, outputs:Any)->None:
        """Validation check for 'outputs' variable from main constructor. Must 
        be implemented by any child class."""
        pass

    def _is_valid_sweep(self, sweep:Dict[str,Union[int,float,complex]])->None:
        """Validation check for 'sweep' variable from main constructor. This 
        function is implemented to check for the types given in the signature, 
        and must be overridden if these differ."""
        check_type(sweep, Dict, hint="BasePattern.sweep")
        if not sweep:
            return
        for _, v in sweep.items():
            valid_dict(
                v, str, Any, [
                    SWEEP_START, SWEEP_STOP, SWEEP_JUMP
                ], strict=True)

            check_type(
                v[SWEEP_START], 
                expected_type=int, 
                alt_types=[float, complex],
                hint=f"BasePattern.sweep[{SWEEP_START}]"
            )
            check_type(
                v[SWEEP_STOP], 
                expected_type=int, 
                alt_types=[float, complex],
                hint=f"BasePattern.sweep[{SWEEP_STOP}]"
            )
            check_type(
                v[SWEEP_JUMP], 
                expected_type=int, 
                alt_types=[float, complex],
                hint=f"BasePattern.sweep[{SWEEP_JUMP}]"
            )
            # Try to check that this loop is not infinite
            if v[SWEEP_JUMP] == 0:
                raise ValueError(
                    f"Cannot create sweep with a '{SWEEP_JUMP}' value of zero"
                )
            elif v[SWEEP_JUMP] > 0:
                if not v[SWEEP_STOP] > v[SWEEP_START]:
                    raise ValueError(
                        f"Cannot create sweep with a positive '{SWEEP_JUMP}' "
                        "value where the end point is smaller than the start."
                    )
            elif v[SWEEP_JUMP] < 0:
                if not v[SWEEP_STOP] < v[SWEEP_START]:
                    raise ValueError(
                        f"Cannot create sweep with a negative '{SWEEP_JUMP}' "
                        "value where the end point is smaller than the start."
                    )

    def expand_sweeps(self)->List[Tuple[str,Any]]:
        """Function to get all combinations of sweep parameters"""
        values_dict = {}
        # get a collection of a individual sweep values
        for var, val in self.sweep.items():
            values_dict[var] = []
            par_val = val[SWEEP_START]
            while par_val <= val[SWEEP_STOP]:
                values_dict[var].append((var, par_val))
                par_val += val[SWEEP_JUMP]

        # combine all combinations of sweep values
        return list(itertools.product(
            *[v for v in values_dict.values()]))
