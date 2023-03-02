"""
This file contains functions for meow specific functionality.

Author(s): David Marchant
"""

from datetime import datetime
from os.path import basename, dirname, relpath, splitext
from typing import Any, Dict, Union, List

from core.base_pattern import BasePattern
from core.base_recipe import BaseRecipe
from core.base_rule import BaseRule
from core.correctness.validation import check_type, valid_dict, valid_list
from core.correctness.vars import EVENT_PATH, EVENT_RULE, EVENT_TYPE, \
    EVENT_TYPE_WATCHDOG, JOB_CREATE_TIME, JOB_EVENT, JOB_ID, JOB_PATTERN, \
    JOB_RECIPE, JOB_REQUIREMENTS, JOB_RULE, JOB_STATUS, JOB_TYPE, \
    STATUS_QUEUED, WATCHDOG_BASE, WATCHDOG_HASH, SWEEP_JUMP, SWEEP_START, \
    SWEEP_STOP
from functionality.naming import generate_job_id, generate_rule_id

# mig trigger keyword replacements
KEYWORD_PATH = "{PATH}"
KEYWORD_REL_PATH = "{REL_PATH}"
KEYWORD_DIR = "{DIR}"
KEYWORD_REL_DIR = "{REL_DIR}"
KEYWORD_FILENAME = "{FILENAME}"
KEYWORD_PREFIX = "{PREFIX}"
KEYWORD_BASE = "{BASE}"
KEYWORD_EXTENSION = "{EXTENSION}"
KEYWORD_JOB = "{JOB}"


def replace_keywords(old_dict:Dict[str,str], job_id:str, src_path:str, 
            monitor_base:str)->Dict[str,str]:
    """Function to replace all MEOW magic words in a dictionary with dynamic 
    values."""
    new_dict = {}

    filename = basename(src_path)
    dir = dirname(src_path)
    relativepath = relpath(src_path, monitor_base)
    reldirname = dirname(relativepath)
    (prefix, extension) = splitext(filename)

    for var, val in old_dict.items():
        if isinstance(val, str):
            val = val.replace(KEYWORD_PATH, src_path)
            val = val.replace(KEYWORD_REL_PATH, relativepath)
            val = val.replace(KEYWORD_DIR, dir)
            val = val.replace(KEYWORD_REL_DIR, reldirname)
            val = val.replace(KEYWORD_FILENAME, filename)
            val = val.replace(KEYWORD_PREFIX, prefix)
            val = val.replace(KEYWORD_BASE, monitor_base)
            val = val.replace(KEYWORD_EXTENSION, extension)
            val = val.replace(KEYWORD_JOB, job_id)

            new_dict[var] = val
        else:
            new_dict[var] = val

    return new_dict

def create_parameter_sweep(variable_name:str, start:Union[int,float,complex], 
        stop:Union[int,float,complex], jump:Union[int,float,complex]
        )->Dict[str,Dict[str,Union[int,float,complex]]]:
    """Function to create a valid parameter sweep dict for a givan variable, 
    from start to stop, with a regular jump of jump. This function will perform
    some basic checks to ensure this isn't infinitie in nature as that 
    would lead to unlimited jobs scheduled per event."""
    check_type(variable_name, str, hint="create_parameter_sweep.variable_name")
    check_type(start, int, alt_types=[float, complex])
    check_type(stop, int, alt_types=[float, complex])
    check_type(jump, int, alt_types=[float, complex])

    if jump == 0:
        raise ValueError(
            f"Cannot create sweep with a '{SWEEP_JUMP}' value of zero as this "
            "would be infinite in nature."
        )
    elif jump > 0:
        if not stop > start:
            raise ValueError(
                f"Cannot create sweep with a positive '{SWEEP_JUMP}' "
                "value where the end point is smaller than the start as this "
                "would be infinite in nature."
            )
    elif jump < 0:
        if not stop < start:
            raise ValueError(
                f"Cannot create sweep with a negative '{SWEEP_JUMP}' "
                "value where the end point is smaller than the start as this "
                "would be infinite in nature."
            )

    return {
        variable_name: {
            SWEEP_START: start,
            SWEEP_STOP: stop,
            SWEEP_JUMP: jump
        }
    }

def create_event(event_type:str, path:str, rule:Any, extras:Dict[Any,Any]={}
        )->Dict[Any,Any]:
    """Function to create a MEOW dictionary."""
    return {
        **extras, 
        EVENT_PATH: path, 
        EVENT_TYPE: event_type, 
        EVENT_RULE: rule
    }

def create_watchdog_event(path:str, rule:Any, base:str, hash:str, 
            extras:Dict[Any,Any]={})->Dict[Any,Any]:
    """Function to create a MEOW event dictionary."""
    return create_event(
        EVENT_TYPE_WATCHDOG, 
        path, 
        rule,
        extras={
            **extras,
            **{
                WATCHDOG_HASH: hash,
                WATCHDOG_BASE: base
            }
        }
    )

def create_job(job_type:str, event:Dict[str,Any], extras:Dict[Any,Any]={}
        )->Dict[Any,Any]:
    """Function to create a MEOW job dictionary."""
    job_dict = {
        #TODO compress event?
        JOB_ID: generate_job_id(),
        JOB_EVENT: event,
        JOB_TYPE: job_type,
        JOB_PATTERN: event[EVENT_RULE].pattern.name,
        JOB_RECIPE: event[EVENT_RULE].recipe.name,
        JOB_RULE: event[EVENT_RULE].name,
        JOB_STATUS: STATUS_QUEUED,
        JOB_CREATE_TIME: datetime.now(),
        JOB_REQUIREMENTS: event[EVENT_RULE].recipe.requirements
    }

    return {**extras, **job_dict}

def create_rules(patterns:Union[Dict[str,BasePattern],List[BasePattern]], 
        recipes:Union[Dict[str,BaseRecipe],List[BaseRecipe]],
        new_rules:List[BaseRule]=[])->Dict[str,BaseRule]:
    """Function to create any valid rules from a given collection of patterns 
    and recipes. All inbuilt rule types are considered, with additional 
    definitions provided through the 'new_rules' variable. Note that any 
    provided pattern and recipe dictionaries must be keyed with the 
    corresponding pattern and recipe names."""
    # Validation of inputs
    check_type(patterns, Dict, alt_types=[List], hint="create_rules.patterns")
    check_type(recipes, Dict, alt_types=[List], hint="create_rules.recipes")
    valid_list(new_rules, BaseRule, min_length=0)

    # Convert a pattern list to a dictionary
    if isinstance(patterns, list):
        valid_list(patterns, BasePattern, min_length=0)
        patterns = {pattern.name:pattern for pattern in patterns}
    else:
        # Validate the pattern dictionary
        valid_dict(patterns, str, BasePattern, strict=False, min_length=0)
        for k, v in patterns.items():
            if k != v.name:
                raise KeyError(
                    f"Key '{k}' indexes unexpected Pattern '{v.name}' "
                    "Pattern dictionaries must be keyed with the name of the "
                    "Pattern.")

    # Convert a recipe list into a dictionary
    if isinstance(recipes, list):
        valid_list(recipes, BaseRecipe, min_length=0)
        recipes = {recipe.name:recipe for recipe in recipes}
    else:
        # Validate the recipe dictionary
        valid_dict(recipes, str, BaseRecipe, strict=False, min_length=0)
        for k, v in recipes.items():
            if k != v.name:
                raise KeyError(
                    f"Key '{k}' indexes unexpected Recipe '{v.name}' "
                    "Recipe dictionaries must be keyed with the name of the "
                    "Recipe.")

    # Try to create a rule for each rule in turn
    generated_rules = {}
    for pattern in patterns.values():
        if pattern.recipe in recipes:
            try:
                rule = create_rule(pattern, recipes[pattern.recipe])
                generated_rules[rule.name] = rule
            except TypeError:
                pass
    return generated_rules

def create_rule(pattern:BasePattern, recipe:BaseRecipe, 
        new_rules:List[BaseRule]=[])->BaseRule:
    """Function to create a valid rule from a given pattern and recipe. All 
    inbuilt rule types are considered, with additional definitions provided 
    through the 'new_rules' variable."""
    check_type(pattern, BasePattern, hint="create_rule.pattern")
    check_type(recipe, BaseRecipe, hint="create_rule.recipe")
    valid_list(new_rules, BaseRule, min_length=0, hint="create_rule.new_rules")

    # TODO fix me
    # Imported here to avoid circular imports at top of file
    import rules
    all_rules = {
        (r.pattern_type, r.recipe_type):r for r in BaseRule.__subclasses__()
    }

    # Add in new rules
    for rule in new_rules:
        all_rules[(rule.pattern_type, rule.recipe_type)] = rule

    # Find appropriate rule type from pattern and recipe types
    key = (type(pattern).__name__, type(recipe).__name__)
    if (key) in all_rules:
        return all_rules[key](
            generate_rule_id(), 
            pattern, 
            recipe
        )
    # Raise error if not valid rule type can be found
    raise TypeError(f"No valid rule for Pattern '{pattern}' and Recipe "
        f"'{recipe}' could be found.")
