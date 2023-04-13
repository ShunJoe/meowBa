
"""
This file contains definitions for the LocalBashConductor, in order to 
execute Bash jobs on the local resource.

Author(s): David Marchant
"""

import os
import shutil
import subprocess

from datetime import datetime
from typing import Any, Dict, Tuple

from meow_base.core.base_conductor import BaseConductor
from meow_base.core.meow import valid_job
from meow_base.core.vars import DEFAULT_JOB_QUEUE_DIR, \
    DEFAULT_JOB_OUTPUT_DIR, JOB_TYPE, JOB_TYPE_BASH, META_FILE, JOB_STATUS, \
    BACKUP_JOB_ERROR_FILE, STATUS_DONE, JOB_END_TIME, STATUS_FAILED, \
    JOB_ERROR, JOB_TYPE, DEFAULT_JOB_QUEUE_DIR, STATUS_RUNNING, \
    JOB_START_TIME, DEFAULT_JOB_OUTPUT_DIR, get_job_file
from meow_base.functionality.validation import valid_dir_path
from meow_base.functionality.file_io import make_dir, read_yaml, write_file, \
    write_yaml


class LocalBashConductor(BaseConductor):
    def __init__(self, job_queue_dir:str=DEFAULT_JOB_QUEUE_DIR, 
            job_output_dir:str=DEFAULT_JOB_OUTPUT_DIR, name:str="")->None:
        """LocalBashConductor Constructor. This should be used to execute 
        Bash jobs, and will then pass any internal job runner files to the 
        output directory. Note that if this handler is given to a MeowRunner
        object, the job_queue_dir and job_output_dir will be overwridden."""
        super().__init__(name=name)
        self._is_valid_job_queue_dir(job_queue_dir)
        self.job_queue_dir = job_queue_dir
        self._is_valid_job_output_dir(job_output_dir)
        self.job_output_dir = job_output_dir

    def valid_execute_criteria(self, job:Dict[str,Any])->Tuple[bool,str]:
        """Function to determine given an job defintion, if this conductor can 
        process it or not. This conductor will accept any Bash job type"""
        try:
            valid_job(job)
            msg = ""
            if job[JOB_TYPE] not in [JOB_TYPE_BASH]:
                msg = f"Job type was not {JOB_TYPE_BASH}."
            if msg:
                return False, msg
            else:
                return True, ""
        except Exception as e:
            return False, str(e)

    def execute(self, job_dir:str)->None:
        """Function to actually execute a Bash job. This will read job 
        defintions from its meta file, update the meta file and attempt to 
        execute. Some unspecific feedback will be given on execution failure, 
        but depending on what it is it may be up to the job itself to provide 
        more detailed feedback."""
        valid_dir_path(job_dir, must_exist=True)

        # Test our job parameters. Even if its gibberish, we still move to 
        # output
        abort = False
        try:
            meta_file = os.path.join(job_dir, META_FILE)
            job = read_yaml(meta_file)
            valid_job(job)

            # update the status file with running status
            job[JOB_STATUS] = STATUS_RUNNING
            job[JOB_START_TIME] = datetime.now()
            write_yaml(job, meta_file)

        except Exception as e:
            # If something has gone wrong at this stage then its bad, so we 
            # need to make our own error file
            error_file = os.path.join(job_dir, BACKUP_JOB_ERROR_FILE)
            write_file(f"Recieved incorrectly setup job.\n\n{e}", error_file)
            abort = True

        # execute the job
        if not abort:
            try:
                print(f"PWD: {os.getcwd()}")
                print(f"job_dir: {job_dir}")
                print(os.path.exists(os.path.join(job_dir, get_job_file(JOB_TYPE_BASH))))
                result = subprocess.call(
                    os.path.join(job_dir, get_job_file(JOB_TYPE_BASH)), 
                    cwd="."
                )

                # get up to date job data
                job = read_yaml(meta_file)

                if result == 0:
                    # Update the status file with the finalised status
                    job[JOB_STATUS] = STATUS_DONE
                    job[JOB_END_TIME] = datetime.now()
                    write_yaml(job, meta_file)

                else:
                    # Update the status file with the error status. Don't 
                    # overwrite any more specific error messages already 
                    # created
                    if JOB_STATUS not in job:
                        job[JOB_STATUS] = STATUS_FAILED
                    if JOB_END_TIME not in job:
                        job[JOB_END_TIME] = datetime.now()
                    if JOB_ERROR not in job:
                        job[JOB_ERROR] = f"Job execution returned non-zero."
                    write_yaml(job, meta_file)

            except Exception as e:
                # get up to date job data
                job = read_yaml(meta_file)

                # Update the status file with the error status. Don't overwrite
                # any more specific error messages already created
                if JOB_STATUS not in job:
                    job[JOB_STATUS] = STATUS_FAILED
                if JOB_END_TIME not in job:
                    job[JOB_END_TIME] = datetime.now()
                if JOB_ERROR not in job:
                    job[JOB_ERROR] = f"Job execution failed. {e}"
                write_yaml(job, meta_file)

        # Move the contents of the execution directory to the final output 
        # directory. 
        job_output_dir = \
            os.path.join(self.job_output_dir, os.path.basename(job_dir))
        shutil.move(job_dir, job_output_dir)

    def _is_valid_job_queue_dir(self, job_queue_dir)->None:
        """Validation check for 'job_queue_dir' variable from main 
        constructor."""
        valid_dir_path(job_queue_dir, must_exist=False)
        if not os.path.exists(job_queue_dir):
            make_dir(job_queue_dir)

    def _is_valid_job_output_dir(self, job_output_dir)->None:
        """Validation check for 'job_output_dir' variable from main 
        constructor."""
        valid_dir_path(job_output_dir, must_exist=False)
        if not os.path.exists(job_output_dir):
            make_dir(job_output_dir)
