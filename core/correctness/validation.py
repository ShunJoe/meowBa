
"""
This file contains various validation functions to be used throughout the 
package.

Author(s): David Marchant
"""
from datetime import datetime
from inspect import signature
from os.path import sep, exists, isfile, isdir, dirname
from typing import Any, _SpecialForm, Union, Tuple, Type, Dict, List, \
    get_origin, get_args

from core.correctness.vars import VALID_PATH_CHARS, get_not_imp_msg, \
    EVENT_TYPE, EVENT_PATH, JOB_EVENT, JOB_TYPE, JOB_ID, JOB_PATTERN, \
    JOB_RECIPE, JOB_RULE, JOB_STATUS, JOB_CREATE_TIME, EVENT_RULE, \
    WATCHDOG_BASE, WATCHDOG_HASH

# Required keys in event dict
EVENT_KEYS = {
    EVENT_TYPE: str,
    EVENT_PATH: str,
    # TODO sort this
    # Should be a Rule but can't import here due to circular dependencies
    EVENT_RULE: Any
}

WATCHDOG_EVENT_KEYS = {
    WATCHDOG_BASE: str,
    WATCHDOG_HASH: str,    
    **EVENT_KEYS
}

# Required keys in job dict
JOB_KEYS = {
    JOB_TYPE: str,
    JOB_EVENT: Dict,
    JOB_ID: str,
    JOB_PATTERN: Any,
    JOB_RECIPE: Any,
    JOB_RULE: str,
    JOB_STATUS: str,
    JOB_CREATE_TIME: datetime,
}

def check_type(variable:Any, expected_type:Type, alt_types:List[Type]=[], 
        or_none:bool=False)->None:
    """Checks if a given variable is of the expected type. Raises TypeError or
    ValueError as appropriate if any issues are encountered."""

    # Get a list of all allowed types
    type_list = [expected_type]
    if get_origin(expected_type) is Union:
        type_list = list(get_args(expected_type))
    type_list = type_list + alt_types
#    # If we have any types from typing, then update to allow checks against 
#    # their base types too
#    for t in type_list:
#        if get_origin(t):
#            type_list.append(get_origin(t))

    # Only accept None if explicitly allowed
    if variable is None:
        if or_none == False:
            raise TypeError(
                f'Not allowed None for variable. Expected {expected_type}.'
            )
        else:
            return

    # If any type is allowed, then we can stop checking
    if expected_type == Any:
        return

    # Check that variable type is within the accepted type list
    if not isinstance(variable, tuple(type_list)):
        raise TypeError(
            'Expected type(s) are %s, got %s'
            % (get_args(expected_type), type(variable))
        )

def check_callable(call:Any)->None:
    """Checks if a given variable is a callable function. Raises TypeError if 
    not."""
    if not callable(call):
        raise TypeError(f"Given object '{call}' is not a callable function")

def check_implementation(child_func, parent_class):
    """Checks if the given function has been overridden from the one inherited
    from the parent class. Raises a NotImplementedError if this is the case."""
    # Check parent first implements func to measure against
    if not hasattr(parent_class, child_func.__name__):
        raise AttributeError(
            f"Parent class {parent_class} does not implement base function "
            f"{child_func.__name__} for children to override.")
    parent_func = getattr(parent_class, child_func.__name__)

    # Check child implements function with correct name
    if (child_func == parent_func):
        msg = get_not_imp_msg(parent_class, parent_func)
        raise NotImplementedError(msg)

    # Check that child implements function with correct signature
    child_sig = signature(child_func).parameters
    parent_sig = signature(parent_func).parameters
    if child_sig.keys() != parent_sig.keys():
        msg = get_not_imp_msg(parent_class, parent_func)
        raise NotImplementedError(msg)

def check_script(script:Any):
    """Checks if a given variable is a valid script. Raises TypeError if 
    not."""
    # TODO investigate more robust check here
    check_type(script, list)
    for line in script:
        check_type(line, str)

def valid_string(variable:str, valid_chars:str, min_length:int=1)->None:
    """Checks that all characters in a given string are present in a provided
    list of characters. Will raise an ValueError if unexpected character is
    encountered."""
    check_type(variable, str)
    check_type(valid_chars, str)

    # Check string is long enough
    if len(variable) < min_length:
        raise ValueError (
            f"String '{variable}' is too short. Minimum length is {min_length}"
        )

    # Check each char is acceptable
    for char in variable:
        if char not in valid_chars:
            raise ValueError(
                "Invalid character '%s'. Only valid characters are: "
                "%s" % (char, valid_chars)
            )

def valid_dict(variable:Dict[Any, Any], key_type:Type, value_type:Type, 
        required_keys:List[Any]=[], optional_keys:List[Any]=[], 
        strict:bool=True, min_length:int=1)->None:
    """Checks that a given dictionary is valid. Key and Value types are 
    enforced, as are required and optional keys. Will raise ValueError, 
    TypeError or KeyError depending on the problem encountered."""
    # Validate inputs
    check_type(variable, Dict)
    check_type(key_type, Type, alt_types=[_SpecialForm])
    check_type(value_type, Type, alt_types=[_SpecialForm])
    check_type(required_keys, list)
    check_type(optional_keys, list)
    check_type(strict, bool)

    # Check dict meets minimum length
    if len(variable) < min_length:
        raise ValueError(f"Dictionary '{variable}' is below minimum length of "
            f"{min_length}")

    # Check key and value types
    for k, v in variable.items():
        if key_type != Any and not isinstance(k, key_type):
            raise TypeError(f"Key {k} had unexpected type '{type(k)}' "
                f"rather than expected '{key_type}' in dict '{variable}'")
        if value_type != Any and not isinstance(v, value_type):
            raise TypeError(f"Value {v} had unexpected type '{type(v)}' "
                f"rather than expected '{value_type}' in dict '{variable}'")

    # Check all required keys present
    for rk in required_keys:
        if rk not in variable.keys():
            raise KeyError(f"Missing required key '{rk}' from dict "
                f"'{variable}'")
    
    # If strict checking, enforce that only required and optional keys are 
    # present
    if strict:
        for k in variable.keys():
            if k not in required_keys and k not in optional_keys:
                raise ValueError(f"Unexpected key '{k}' should not be present "
                    f"in dict '{variable}'")

def valid_list(variable:List[Any], entry_type:Type,
        alt_types:List[Type]=[], min_length:int=1)->None:
    """Checks that a given list is valid. Value types are checked and a 
    ValueError or TypeError is raised if a problem is encountered."""
    check_type(variable, List)

    # Check length meets minimum
    if len(variable) < min_length:
        raise ValueError(f"List '{variable}' is too short. Should be at least "
            f"of length {min_length}")
    
    # Check type of each value
    for entry in variable:
        check_type(entry, entry_type, alt_types=alt_types)

def valid_path(variable:str, allow_base:bool=False, extension:str="", 
        min_length:int=1):
    """Check that a given string expresses a valid path."""
    valid_string(variable, VALID_PATH_CHARS, min_length=min_length)
    
    # Check we aren't given a root path
    if not allow_base and variable.startswith(sep):
        raise ValueError(f"Cannot accept path '{variable}'. Must be relative.")
    
    # Check path contains a valid extension
    if extension and not variable.endswith(extension):
        raise ValueError(f"Path '{variable}' does not have required "
            f"extension '{extension}'.")

def valid_existing_file_path(variable:str, allow_base:bool=False, 
        extension:str=""):
    """Check the given string is a path to an existing file."""
    # Check that the string is a path
    valid_path(variable, allow_base=allow_base, extension=extension)
    # Check the path exists
    if not exists(variable):
        raise FileNotFoundError(
            f"Requested file path '{variable}' does not exist.")
    # Check it is a file
    if not isfile(variable):
        raise ValueError(
            f"Requested file '{variable}' is not a file.")

def valid_existing_dir_path(variable:str, allow_base:bool=False):
    """Check the given string is a path to an existing directory."""
    # Check that the string is a path
    valid_path(variable, allow_base=allow_base, extension="")
    # Check the path exists
    if not exists(variable):
        raise FileNotFoundError(
            f"Requested dir path '{variable}' does not exist.")
    # Check it is a directory
    if not isdir(variable):
        raise ValueError(
            f"Requested dir '{variable}' is not a directory.")

def valid_non_existing_path(variable:str, allow_base:bool=False):
    """Check the given string is a path to something that does not exist."""
    # Check that the string is a path
    valid_path(variable, allow_base=allow_base, extension="")
    # Check the path does not exist
    if exists(variable):
        raise ValueError(f"Requested path '{variable}' already exists.")
    # Check that any intermediate directories exist
    if dirname(variable) and not exists(dirname(variable)):
        raise ValueError(
            f"Route to requested path '{variable}' does not exist.")

def setup_debugging(print:Any=None, logging:int=0)->Tuple[Any,int]:
    """Create a place for debug messages to be sent. Always returns a place, 
    along with a logging level."""
    check_type(logging, int)
    if print is None:
        return None, 0
    else:
        if not isinstance(print, object):
            raise TypeError(f"Invalid print location provided")
        writeable = getattr(print, "write", None)
        if not writeable or not callable(writeable):
            raise TypeError(f"Print object does not implement required "
                "'write' function")

    return print, logging

def valid_meow_dict(meow_dict:Dict[str,Any], msg:str, 
        keys:Dict[str,Type])->None:
    """Check given dictionary expresses a meow construct. This won't do much 
    directly, but is called by more specific validation functions."""
    check_type(meow_dict, Dict)
    # Check we have all the required keys, and they are all of the expected 
    # type
    for key, value_type in keys.items():
        if not key in meow_dict.keys():
            raise KeyError(f"{msg} require key '{key}'")
        check_type(meow_dict[key], value_type)

def valid_event(event:Dict[str,Any])->None:
    """Check that a given dict expresses a meow event."""
    valid_meow_dict(event, "Event", EVENT_KEYS)

def valid_job(job:Dict[str,Any])->None:
    """Check that a given dict expresses a meow job."""
    valid_meow_dict(job, "Job", JOB_KEYS)

def valid_watchdog_event(event:Dict[str,Any])->None:
    valid_meow_dict(event, "Watchdog event", WATCHDOG_EVENT_KEYS)
