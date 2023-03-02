
"""
This file contains the base MEOW conductor defintion. This should be inherited 
from for all conductor instances.

Author(s): David Marchant
"""

from typing import Any, Tuple, Dict

from core.correctness.vars import get_drt_imp_msg
from core.correctness.validation import check_implementation


class BaseConductor:
    # Directory where queued jobs are initially written to. Note that this 
    # will be overridden by a MeowRunner, if a handler instance is passed to 
    # it, and so does not need to be initialised within the handler itself.
    job_queue_dir:str
    # Directory where completed jobs are finally written to. Note that this 
    # will be overridden by a MeowRunner, if a handler instance is passed to 
    # it, and so does not need to be initialised within the handler itself.
    job_output_dir:str
    def __init__(self)->None:
        """BaseConductor Constructor. This will check that any class inheriting
        from it implements its validation functions."""
        check_implementation(type(self).execute, BaseConductor)
        check_implementation(type(self).valid_execute_criteria, BaseConductor)

    def __new__(cls, *args, **kwargs):
        """A check that this base class is not instantiated itself, only 
        inherited from"""
        if cls is BaseConductor:
            msg = get_drt_imp_msg(BaseConductor)
            raise TypeError(msg)
        return object.__new__(cls)

    def valid_execute_criteria(self, job:Dict[str,Any])->Tuple[bool,str]:
        """Function to determine given an job defintion, if this conductor can 
        process it or not. Must be implemented by any child process."""
        pass

    def execute(self, job_dir:str)->None:
        """Function to execute a given job directory. Must be implemented by 
        any child process."""
        pass
