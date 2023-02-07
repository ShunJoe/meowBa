
"""
This file contains definitions for a MEOW recipe based off of python code,
along with an appropriate handler for said events.

Author(s): David Marchant
"""
import os
import sys

from typing import Any, Tuple

from core.correctness.validation import check_script, valid_string, \
    valid_dict, valid_event, valid_existing_dir_path, setup_debugging
from core.correctness.vars import VALID_VARIABLE_NAME_CHARS, PYTHON_FUNC, \
    DEBUG_INFO, EVENT_TYPE_WATCHDOG, JOB_HASH, PYTHON_EXECUTION_BASE, \
    EVENT_RULE, EVENT_PATH, JOB_TYPE_PYTHON, WATCHDOG_HASH, JOB_PARAMETERS, \
    PYTHON_OUTPUT_DIR, JOB_ID, WATCHDOG_BASE, META_FILE, \
    PARAMS_FILE, JOB_STATUS, STATUS_QUEUED, EVENT_TYPE, EVENT_RULE, \
    get_job_file, get_base_file, get_result_file
from core.functionality import print_debug, create_job, replace_keywords, \
    make_dir, write_yaml, write_file, lines_to_string, read_file_lines
from core.meow import BaseRecipe, BaseHandler


class PythonRecipe(BaseRecipe):
    def __init__(self, name:str, recipe:list[str], parameters:dict[str,Any]={}, 
            requirements:dict[str,Any]={}):
        """PythonRecipe Constructor. This is used to execute python analysis 
        code."""
        super().__init__(name, recipe, parameters, requirements)

    def _is_valid_recipe(self, recipe:list[str])->None:
        """Validation check for 'recipe' variable from main constructor. 
        Called within parent BaseRecipe constructor."""
        check_script(recipe)

    def _is_valid_parameters(self, parameters:dict[str,Any])->None:
        """Validation check for 'parameters' variable from main constructor. 
        Called within parent BaseRecipe constructor."""
        valid_dict(parameters, str, Any, strict=False, min_length=0)
        for k in parameters.keys():
            valid_string(k, VALID_VARIABLE_NAME_CHARS)

    def _is_valid_requirements(self, requirements:dict[str,Any])->None:
        """Validation check for 'requirements' variable from main constructor. 
        Called within parent BaseRecipe constructor."""
        valid_dict(requirements, str, Any, strict=False, min_length=0)
        for k in requirements.keys():
            valid_string(k, VALID_VARIABLE_NAME_CHARS)

class PythonHandler(BaseHandler):
    # TODO move me to base handler
    # handler directory to setup jobs in
    handler_base:str
    # TODO move me to conductor?
    # Final location for job output to be placed
    output_dir:str
    # Config option, above which debug messages are ignored
    debug_level:int
    # Where print messages are sent
    _print_target:Any
    def __init__(self, handler_base:str, output_dir:str, print:Any=sys.stdout, 
            logging:int=0)->None:
        """PythonHandler Constructor. This creates jobs to be executed as 
        python functions. This does not run as a continuous thread to 
        handle execution, but is invoked according to a factory pattern using 
        the handle function."""
        super().__init__()
        self._is_valid_handler_base(handler_base)
        self.handler_base = handler_base
        self._is_valid_output_dir(output_dir)
        self.output_dir = output_dir
        self._print_target, self.debug_level = setup_debugging(print, logging)
        print_debug(self._print_target, self.debug_level, 
            "Created new PythonHandler instance", DEBUG_INFO)

    def handle(self, event:dict[str,Any])->None:
        """Function called to handle a given event."""
        print_debug(self._print_target, self.debug_level, 
            f"Handling event {event[EVENT_PATH]}", DEBUG_INFO)

        rule = event[EVENT_RULE]

        # Assemble job parameters dict from pattern variables
        yaml_dict = {}
        for var, val in rule.pattern.parameters.items():
            yaml_dict[var] = val
        for var, val in rule.pattern.outputs.items():
            yaml_dict[var] = val
        yaml_dict[rule.pattern.triggering_file] = event[EVENT_PATH]

        # If no parameter sweeps, then one job will suffice
        if not rule.pattern.sweep:
            self.setup_job(event, yaml_dict)
        else:
            # If parameter sweeps, then many jobs created
            values_list = rule.pattern.expand_sweeps()
            for values in values_list:
                for value in values:
                    yaml_dict[value[0]] = value[1]
                self.setup_job(event, yaml_dict)

    def valid_handle_criteria(self, event:dict[str,Any])->Tuple[bool,str]:
        """Function to determine given an event defintion, if this handler can 
        process it or not. This handler accepts events from watchdog with 
        Python recipes"""
        try:
            valid_event(event)
            if event[EVENT_TYPE] == EVENT_TYPE_WATCHDOG \
                    and type(event[EVENT_RULE].recipe) == PythonRecipe:
                return True, ""
        except Exception as e:
            pass
        return False, str(e)

    def _is_valid_handler_base(self, handler_base)->None:
        """Validation check for 'handler_base' variable from main 
        constructor."""
        valid_existing_dir_path(handler_base)

    def _is_valid_output_dir(self, output_dir)->None:
        """Validation check for 'output_dir' variable from main 
        constructor."""
        valid_existing_dir_path(output_dir, allow_base=True)

    def setup_job(self, event:dict[str,Any], yaml_dict:dict[str,Any])->None:
        """Function to set up new job dict and send it to the runner to be 
        executed."""
        meow_job = create_job(
            JOB_TYPE_PYTHON, 
            event, 
            extras={
                JOB_PARAMETERS:yaml_dict,
                JOB_HASH: event[WATCHDOG_HASH],
                PYTHON_FUNC:python_job_func,
                PYTHON_OUTPUT_DIR:self.output_dir,
                PYTHON_EXECUTION_BASE:self.handler_base
            }
        )
        print_debug(self._print_target, self.debug_level,  
            f"Creating job from event at {event[EVENT_PATH]} of type "
            f"{JOB_TYPE_PYTHON}.", DEBUG_INFO)

        # replace MEOW keyworks within variables dict
        yaml_dict = replace_keywords(
            meow_job[JOB_PARAMETERS],
            meow_job[JOB_ID],
            event[EVENT_PATH],
            event[WATCHDOG_BASE]
        )

        # Create a base job directory
        job_dir = os.path.join(
            meow_job[PYTHON_EXECUTION_BASE], meow_job[JOB_ID])
        make_dir(job_dir)

        # write a status file to the job directory
        meta_file = os.path.join(job_dir, META_FILE)
        write_yaml(meow_job, meta_file)

        # write an executable script to the job directory
        base_file = os.path.join(job_dir, get_base_file(JOB_TYPE_PYTHON))
        write_file(lines_to_string(event[EVENT_RULE].recipe.recipe), base_file)

        # write a parameter file to the job directory
        param_file = os.path.join(job_dir, PARAMS_FILE)
        write_yaml(yaml_dict, param_file)

        meow_job[JOB_STATUS] = STATUS_QUEUED

        # update the status file with queued status
        write_yaml(meow_job, meta_file)
        
        # Send job directory, as actual definitons will be read from within it
        self.to_runner.send(job_dir)

# Papermill job execution code, to be run within the conductor
def python_job_func(job):
    # Requires own imports as will be run in its own execution environment
    import sys
    import os
    from datetime import datetime
    from io import StringIO
    from core.functionality import write_yaml, read_yaml, \
        get_file_hash, parameterize_python_script
    from core.correctness.vars import JOB_EVENT, JOB_ID, \
        EVENT_PATH, META_FILE, PARAMS_FILE, \
        JOB_STATUS, JOB_HASH, SHA256, STATUS_SKIPPED, JOB_END_TIME, \
        JOB_ERROR, STATUS_FAILED, PYTHON_EXECUTION_BASE, get_base_file, \
        get_job_file, get_result_file

    # Identify job files
    job_dir = os.path.join(job[PYTHON_EXECUTION_BASE], job[JOB_ID])
    meta_file = os.path.join(job_dir, META_FILE)
    base_file = os.path.join(job_dir, get_base_file(JOB_TYPE_PYTHON))
    job_file = os.path.join(job_dir, get_job_file(JOB_TYPE_PYTHON))
    result_file = os.path.join(job_dir, get_result_file(JOB_TYPE_PYTHON))
    param_file = os.path.join(job_dir, PARAMS_FILE)

    yaml_dict = read_yaml(param_file)

    # Check the hash of the triggering file, if present. This addresses 
    # potential race condition as file could have been modified since 
    # triggering event
    if JOB_HASH in job:
        # get current hash
        triggerfile_hash = get_file_hash(job[JOB_EVENT][EVENT_PATH], SHA256)
        # If hash doesn't match, then abort the job. If its been modified, then
        # another job will have been scheduled anyway.
        if not triggerfile_hash \
                or triggerfile_hash != job[JOB_HASH]:
            job[JOB_STATUS] = STATUS_SKIPPED
            job[JOB_END_TIME] = datetime.now()
            msg = "Job was skipped as triggering file " + \
                f"'{job[JOB_EVENT][EVENT_PATH]}' has been modified since " + \
                "scheduling. Was expected to have hash " + \
                f"'{job[JOB_HASH]}' but has '{triggerfile_hash}'."
            job[JOB_ERROR] = msg
            write_yaml(job, meta_file)
            return

    # Create a parameterised version of the executable script
    try:
        base_script = read_file_lines(base_file)
        job_script = parameterize_python_script(
            base_script, yaml_dict
        )
        write_file(lines_to_string(job_script), job_file)
    except Exception as e:
        job[JOB_STATUS] = STATUS_FAILED
        job[JOB_END_TIME] = datetime.now()
        msg = f"Job file {job[JOB_ID]} was not created successfully. {e}"
        job[JOB_ERROR] = msg
        write_yaml(job, meta_file)
        return

    # Execute the parameterised script
    std_stdout = sys.stdout
    std_stderr = sys.stderr
    try:
        redirected_output = sys.stdout = StringIO()
        redirected_error = sys.stderr = StringIO()

        exec(open(job_file).read())        

        write_file(("--STDOUT--\n"
            f"{redirected_output.getvalue()}\n"
            "\n"
            "--STDERR--\n"
            f"{redirected_error.getvalue()}\n"
            ""), 
            result_file)

    except Exception as e:
        sys.stdout = std_stdout
        sys.stderr = std_stderr

        job[JOB_STATUS] = STATUS_FAILED
        job[JOB_END_TIME] = datetime.now()
        msg = f"Result file {result_file} was not created successfully. {e}"
        job[JOB_ERROR] = msg
        write_yaml(job, meta_file)
        return

    sys.stdout = std_stdout
    sys.stderr = std_stderr
