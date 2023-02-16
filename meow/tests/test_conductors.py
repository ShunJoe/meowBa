
import os
import unittest

from typing import Dict

from core.correctness.vars import JOB_TYPE_PYTHON, SHA256, JOB_PARAMETERS, \
    JOB_HASH, PYTHON_FUNC, JOB_ID, \
    META_FILE, PARAMS_FILE, JOB_STATUS, JOB_ERROR, \
    STATUS_DONE, JOB_TYPE_PAPERMILL, get_base_file, get_result_file, \
    get_job_file
from core.functionality import get_file_hash, create_watchdog_event, \
    create_job, make_dir, write_yaml, write_notebook, read_yaml, write_file, \
    lines_to_string
from core.meow import create_rule
from conductors import LocalPythonConductor
from patterns import FileEventPattern
from recipes.jupyter_notebook_recipe import JupyterNotebookRecipe, \
    papermill_job_func
from recipes.python_recipe import PythonRecipe, python_job_func
from shared import setup, teardown, TEST_MONITOR_BASE, APPENDING_NOTEBOOK, \
    TEST_JOB_OUTPUT, TEST_JOB_QUEUE, COMPLETE_PYTHON_SCRIPT


def failing_func():
    raise Exception("bad function")
 

class MeowTests(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()
        
    # Test LocalPythonConductor creation and job types
    def testLocalPythonConductorCreation(self)->None:
        LocalPythonConductor()

    # Test LocalPythonConductor executes valid python jobs
    def testLocalPythonConductorValidPythonJob(self)->None:
        lpc = LocalPythonConductor(
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        file_path = os.path.join(TEST_MONITOR_BASE, "test")
        result_path = os.path.join(TEST_MONITOR_BASE, "output")

        with open(file_path, "w") as f:
            f.write("150")

        file_hash = get_file_hash(file_path, SHA256)

        pattern = FileEventPattern(
            "pattern", 
            file_path, 
            "recipe_one", 
            "infile", 
            parameters={
                "num":450,
                "outfile":result_path
            })
        recipe = PythonRecipe(
            "recipe_one", COMPLETE_PYTHON_SCRIPT)

        rule = create_rule(pattern, recipe)

        params_dict = {
            "num":450,
            "infile":file_path,
            "outfile":result_path
        }

        job_dict = create_job(
            JOB_TYPE_PYTHON,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:params_dict,
                JOB_HASH: file_hash,
                PYTHON_FUNC:python_job_func
            }
        )

        job_dir = os.path.join(TEST_JOB_QUEUE, job_dict[JOB_ID])
        make_dir(job_dir)

        param_file = os.path.join(job_dir, PARAMS_FILE)
        write_yaml(params_dict, param_file)

        meta_path = os.path.join(job_dir, META_FILE)
        write_yaml(job_dict, meta_path)

        base_file = os.path.join(job_dir, get_base_file(JOB_TYPE_PYTHON))
        write_file(lines_to_string(COMPLETE_PYTHON_SCRIPT), base_file)

        lpc.execute(job_dir)

        self.assertFalse(os.path.exists(job_dir))
        
        job_output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])
        self.assertTrue(os.path.exists(job_output_dir))

        meta_path = os.path.join(job_output_dir, META_FILE)
        self.assertTrue(os.path.exists(meta_path))
        status = read_yaml(meta_path)
        self.assertIsInstance(status, Dict)
        self.assertIn(JOB_STATUS, status)
        self.assertEqual(status[JOB_STATUS], STATUS_DONE)

        self.assertNotIn(JOB_ERROR, status)
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_base_file(JOB_TYPE_PYTHON))))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, PARAMS_FILE)))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_job_file(JOB_TYPE_PYTHON))))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_result_file(JOB_TYPE_PYTHON))))

        self.assertTrue(os.path.exists(result_path))

     # Test LocalPythonConductor executes valid papermill jobs
    def testLocalPythonConductorValidPapermillJob(self)->None:
        lpc = LocalPythonConductor(
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        file_path = os.path.join(TEST_MONITOR_BASE, "test")
        result_path = os.path.join(TEST_MONITOR_BASE, "output", "test")

        with open(file_path, "w") as f:
            f.write("Data")

        file_hash = get_file_hash(file_path, SHA256)

        pattern = FileEventPattern(
            "pattern", 
            file_path, 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from a test Pattern",
                "outfile":result_path
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        rule = create_rule(pattern, recipe)

        params_dict = {
            "extra":"extra",
            "infile":file_path,
            "outfile":result_path
        }

        job_dict = create_job(
            JOB_TYPE_PAPERMILL,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:params_dict,
                JOB_HASH: file_hash,
                PYTHON_FUNC:papermill_job_func
            }
        )

        job_dir = os.path.join(TEST_JOB_QUEUE, job_dict[JOB_ID])
        make_dir(job_dir)

        param_file = os.path.join(job_dir, PARAMS_FILE)
        write_yaml(params_dict, param_file)

        meta_path = os.path.join(job_dir, META_FILE)
        write_yaml(job_dict, meta_path)

        base_file = os.path.join(job_dir, get_base_file(JOB_TYPE_PAPERMILL))
        write_notebook(APPENDING_NOTEBOOK, base_file)

        lpc.execute(job_dir)

        job_dir = os.path.join(TEST_JOB_QUEUE, job_dict[JOB_ID])
        self.assertFalse(os.path.exists(job_dir))
        
        job_output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])
        self.assertTrue(os.path.exists(job_output_dir))

        meta_path = os.path.join(job_output_dir, META_FILE)
        self.assertTrue(os.path.exists(meta_path))
        status = read_yaml(meta_path)
        self.assertIsInstance(status, Dict)
        self.assertIn(JOB_STATUS, status)
        self.assertEqual(status[JOB_STATUS], STATUS_DONE)

        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_base_file(JOB_TYPE_PAPERMILL))))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, PARAMS_FILE)))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_job_file(JOB_TYPE_PAPERMILL))))
        self.assertTrue(os.path.exists(
            os.path.join(job_output_dir, get_result_file(JOB_TYPE_PAPERMILL))))

        self.assertTrue(os.path.exists(result_path))

    # Test LocalPythonConductor does not execute jobs with bad arguments
    def testLocalPythonConductorBadArgs(self)->None:
        lpc = LocalPythonConductor(
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        file_path = os.path.join(TEST_MONITOR_BASE, "test")
        result_path = os.path.join(TEST_MONITOR_BASE, "output", "test")

        with open(file_path, "w") as f:
            f.write("Data")

        file_hash = get_file_hash(file_path, SHA256)

        pattern = FileEventPattern(
            "pattern", 
            file_path, 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from a test Pattern",
                "outfile":result_path
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        rule = create_rule(pattern, recipe)

        params_dict = {
            "extra":"extra",
            "infile":file_path,
            "outfile":result_path
        }

        bad_job_dict = create_job(
            JOB_TYPE_PAPERMILL,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:params_dict,
                JOB_HASH: file_hash,
            }
        )

        bad_job_dir = os.path.join(TEST_JOB_QUEUE, bad_job_dict[JOB_ID])
        make_dir(bad_job_dir)

        bad_param_file = os.path.join(bad_job_dir, PARAMS_FILE)
        write_yaml(params_dict, bad_param_file)

        bad_meta_path = os.path.join(bad_job_dir, META_FILE)
        write_yaml(bad_job_dict, bad_meta_path)

        bad_base_file = os.path.join(bad_job_dir, 
            get_base_file(JOB_TYPE_PAPERMILL))
        write_notebook(APPENDING_NOTEBOOK, bad_base_file)

        lpc.execute(bad_job_dir)

        bad_output_dir = os.path.join(TEST_JOB_OUTPUT, bad_job_dict[JOB_ID])
        self.assertFalse(os.path.exists(bad_job_dir))
        self.assertTrue(os.path.exists(bad_output_dir))

        bad_meta_path = os.path.join(bad_output_dir, META_FILE)
        self.assertTrue(os.path.exists(bad_meta_path))

        bad_job = read_yaml(bad_meta_path)
        self.assertIsInstance(bad_job, dict)
        self.assertIn(JOB_ERROR, bad_job)

        # Ensure execution can continue after one failed job
        good_job_dict = create_job(
            JOB_TYPE_PAPERMILL,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:params_dict,
                JOB_HASH: file_hash,
                PYTHON_FUNC:papermill_job_func
            }
        )

        good_job_dir = os.path.join(TEST_JOB_QUEUE, good_job_dict[JOB_ID])
        make_dir(good_job_dir)

        good_param_file = os.path.join(good_job_dir, PARAMS_FILE)
        write_yaml(params_dict, good_param_file)

        good_meta_path = os.path.join(good_job_dir, META_FILE)
        write_yaml(good_job_dict, good_meta_path)

        good_base_file = os.path.join(good_job_dir, 
            get_base_file(JOB_TYPE_PAPERMILL))
        write_notebook(APPENDING_NOTEBOOK, good_base_file)

        lpc.execute(good_job_dir)

        good_job_dir = os.path.join(TEST_JOB_QUEUE, good_job_dict[JOB_ID])
        self.assertFalse(os.path.exists(good_job_dir))
        
        good_job_output_dir = os.path.join(TEST_JOB_OUTPUT, good_job_dict[JOB_ID])
        self.assertTrue(os.path.exists(good_job_output_dir))
        self.assertTrue(os.path.exists(
            os.path.join(good_job_output_dir, META_FILE)))

        self.assertTrue(os.path.exists(
            os.path.join(good_job_output_dir, get_base_file(JOB_TYPE_PAPERMILL))))
        self.assertTrue(os.path.exists(
            os.path.join(good_job_output_dir, PARAMS_FILE)))
        self.assertTrue(os.path.exists(
            os.path.join(good_job_output_dir, get_job_file(JOB_TYPE_PAPERMILL))))
        self.assertTrue(os.path.exists(
            os.path.join(good_job_output_dir, get_result_file(JOB_TYPE_PAPERMILL))))

        self.assertTrue(os.path.exists(result_path))

    # Test LocalPythonConductor does not execute jobs with missing metafile
    def testLocalPythonConductorMissingMetafile(self)->None:
        lpc = LocalPythonConductor(
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        file_path = os.path.join(TEST_MONITOR_BASE, "test")
        result_path = os.path.join(TEST_MONITOR_BASE, "output", "test")

        with open(file_path, "w") as f:
            f.write("Data")

        file_hash = get_file_hash(file_path, SHA256)

        pattern = FileEventPattern(
            "pattern", 
            file_path, 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from a test Pattern",
                "outfile":result_path
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        rule = create_rule(pattern, recipe)

        job_dict = create_job(
            JOB_TYPE_PAPERMILL,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:{
                    "extra":"extra",
                    "infile":file_path,
                    "outfile":result_path
                },
                JOB_HASH: file_hash,
                PYTHON_FUNC:failing_func,
            }
        )

        job_dir = os.path.join(TEST_JOB_QUEUE, job_dict[JOB_ID])
        make_dir(job_dir)

        with self.assertRaises(FileNotFoundError):
            lpc.execute(job_dir)

    # Test LocalPythonConductor does not execute jobs with bad functions
    def testLocalPythonConductorBadFunc(self)->None:
        lpc = LocalPythonConductor(
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        file_path = os.path.join(TEST_MONITOR_BASE, "test")
        result_path = os.path.join(TEST_MONITOR_BASE, "output", "test")

        with open(file_path, "w") as f:
            f.write("Data")

        file_hash = get_file_hash(file_path, SHA256)

        pattern = FileEventPattern(
            "pattern", 
            file_path, 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from a test Pattern",
                "outfile":result_path
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        rule = create_rule(pattern, recipe)

        params = {
            "extra":"extra",
            "infile":file_path,
            "outfile":result_path
        }

        job_dict = create_job(
            JOB_TYPE_PAPERMILL,
            create_watchdog_event(
                file_path,
                rule,
                TEST_MONITOR_BASE,
                file_hash
            ),
            extras={
                JOB_PARAMETERS:params,
                JOB_HASH: file_hash,
                PYTHON_FUNC:failing_func,
            }
        )

        job_dir = os.path.join(TEST_JOB_QUEUE, job_dict[JOB_ID])
        make_dir(job_dir)

        param_file = os.path.join(job_dir, PARAMS_FILE)
        write_yaml(params, param_file)

        meta_path = os.path.join(job_dir, META_FILE)
        write_yaml(job_dict, meta_path)

        lpc.execute(job_dir)

        output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])
        self.assertFalse(os.path.exists(job_dir))
        self.assertTrue(os.path.exists(output_dir))

        meta_path = os.path.join(output_dir, META_FILE)
        self.assertTrue(os.path.exists(meta_path))

        job = read_yaml(meta_path)
        self.assertIsInstance(job, dict)
        self.assertIn(JOB_ERROR, job)

    # TODO test job status funcs
    # TODO test mangled status file reads
    # TODO test missing input files
