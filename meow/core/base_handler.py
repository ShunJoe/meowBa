
"""
This file contains the base MEOW handler defintion. This should be inherited 
from for all handler instances.

Author(s): David Marchant
"""

from typing import Any, Tuple, Dict

from core.correctness.vars import get_drt_imp_msg, VALID_CHANNELS
from core.correctness.validation import check_implementation


class BaseHandler:
    # A channel for sending messages to the runner. Note that this will be 
    # overridden by a MeowRunner, if a handler instance is passed to it, and so
    # does not need to be initialised within the handler itself.
    to_runner: VALID_CHANNELS
    # Directory where queued jobs are initially written to. Note that this 
    # will be overridden by a MeowRunner, if a handler instance is passed to 
    # it, and so does not need to be initialised within the handler itself.
    job_queue_dir:str
    def __init__(self)->None:
        """BaseHandler Constructor. This will check that any class inheriting 
        from it implements its validation functions."""
        check_implementation(type(self).handle, BaseHandler)
        check_implementation(type(self).valid_handle_criteria, BaseHandler)

    def __new__(cls, *args, **kwargs):
        """A check that this base class is not instantiated itself, only 
        inherited from"""
        if cls is BaseHandler:
            msg = get_drt_imp_msg(BaseHandler)
            raise TypeError(msg)
        return object.__new__(cls)

    def valid_handle_criteria(self, event:Dict[str,Any])->Tuple[bool,str]:
        """Function to determine given an event defintion, if this handler can 
        process it or not. Must be implemented by any child process."""
        pass

    def handle(self, event:Dict[str,Any])->None:
        """Function to handle a given event. Must be implemented by any child 
        process."""
        pass
