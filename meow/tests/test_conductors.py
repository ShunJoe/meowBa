
import os
import unittest

from datetime import datetime
from typing import Dict

from core.correctness.vars import JOB_TYPE_PYTHON, SHA256, JOB_PARAMETERS, \
    JOB_HASH, PYTHON_FUNC, JOB_ID, BACKUP_JOB_ERROR_FILE, JOB_EVENT, \
    META_FILE, PARAMS_FILE, JOB_STATUS, JOB_ERROR, JOB_TYPE, JOB_PATTERN, \
    STATUS_DONE, JOB_TYPE_PAPERMILL, JOB_RECIPE, JOB_RULE, JOB_CREATE_TIME, \
    JOB_REQUIREMENTS, EVENT_PATH, EVENT_RULE, EVENT_TYPE, \
    EVENT_TYPE_WATCHDOG, get_base_file, get_result_file, get_job_file
from conductors import LocalPythonConductor
from functionality.file_io import read_file, read_yaml, write_file, \
    write_notebook, write_yaml, lines_to_string, make_dir
from functionality.hashing import get_file_hash
from functionality.meow import create_watchdog_event, create_job, create_rule
from patterns import FileEventPattern
from recipes.jupyter_notebook_recipe import JupyterNotebookRecipe, \
    papermill_job_func
from recipes.python_recipe import PythonRecipe, python_job_func
from shared import setup, teardown, TEST_MONITOR_BASE, APPENDING_NOTEBOOK, \
    TEST_JOB_OUTPUT, TEST_JOB_QUEUE, COMPLETE_PYTHON_SCRIPT, \
    BAREBONES_PYTHON_SCRIPT, BAREBONES_NOTEBOOK

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

        lpc.execute(job_dir)

        output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])

        self.assertFalse(os.path.exists(job_dir))
        self.assertTrue(os.path.exists(output_dir))

        error_file = os.path.join(output_dir, BACKUP_JOB_ERROR_FILE)
        self.assertTrue(os.path.exists(error_file))

        error = read_file(error_file)
        self.assertEqual(error, 
            "Recieved incorrectly setup job.\n\n[Errno 2] No such file or "
            f"directory: 'test_job_queue_dir{os.path.sep}{job_dict[JOB_ID]}{os.path.sep}job.yml'")

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

    # Test LocalPythonConductor does not execute jobs with invalid metafile
    def testLocalPythonConductorInvalidMetafile(self)->None:
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

        meta_path = os.path.join(job_dir, META_FILE)
        write_file("This is not a metafile dict", meta_path)

        lpc.execute(job_dir)

        output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])

        self.assertFalse(os.path.exists(job_dir))
        self.assertTrue(os.path.exists(output_dir))

        error_file = os.path.join(output_dir, BACKUP_JOB_ERROR_FILE)
        self.assertTrue(os.path.exists(error_file))

        error = read_file(error_file)
        self.assertEqual(error, 
            "Recieved incorrectly setup job.\n\nExpected type(s) are "
            "'[typing.Dict]', got <class 'str'>")

    # Test LocalPythonConductor does not execute jobs with mangled metafile
    def testLocalPythonConductorMangledMetafile(self)->None:
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

        meta_path = os.path.join(job_dir, META_FILE)
        write_yaml({
            "This": "is",
            "a": "dictionary",
            "but": "not",
            "valid": "job",
            "definitons": "file"
        }, meta_path)

        lpc.execute(job_dir)

        output_dir = os.path.join(TEST_JOB_OUTPUT, job_dict[JOB_ID])

        self.assertFalse(os.path.exists(job_dir))
        self.assertTrue(os.path.exists(output_dir))

        error_file = os.path.join(output_dir, BACKUP_JOB_ERROR_FILE)
        self.assertTrue(os.path.exists(error_file))

        error = read_file(error_file)
        self.assertEqual(error, 
            "Recieved incorrectly setup job.\n\n\"Job require key "
            "'job_type'\"")

   # Test execute criteria function
    def testValidExecuteCriteria(self)->None:
        lpc = LocalPythonConductor()

        pattern_python = FileEventPattern(
            "pattern_python", "A", "recipe_python", "file_one")
        recipe_python = PythonRecipe(
            "recipe_python", BAREBONES_PYTHON_SCRIPT
        )

        pattern_papermill = FileEventPattern(
            "pattern_papermill", "A", "recipe_papermill", "file_one")
        recipe_papermill = JupyterNotebookRecipe(
            "recipe_papermill", BAREBONES_NOTEBOOK
        )

        python_rule = create_rule(pattern_python, recipe_python)
        papermill_rule = create_rule(pattern_papermill, recipe_papermill)

        status, _ = lpc.valid_execute_criteria({})
        self.assertFalse(status)

        status, _ = lpc.valid_execute_criteria("")
        self.assertFalse(status)

        status, _ = lpc.valid_execute_criteria({
            JOB_ID: "path",
            JOB_EVENT: "type",
            JOB_TYPE: "rule",
            JOB_PATTERN: "pattern",
            JOB_RECIPE: "recipe",
            JOB_RULE: "rule",
            JOB_STATUS: "status",
            JOB_CREATE_TIME: "create",
            JOB_REQUIREMENTS: "requirements"
        })
        self.assertFalse(status)

        status, s = lpc.valid_execute_criteria({
            JOB_ID: "path",
            JOB_EVENT: {
                EVENT_PATH: "path",
                EVENT_TYPE: EVENT_TYPE_WATCHDOG,
                EVENT_RULE: python_rule
            },
            JOB_TYPE: "type",
            JOB_PATTERN: python_rule.pattern.name,
            JOB_RECIPE: python_rule.recipe.name,
            JOB_RULE: python_rule.name,
            JOB_STATUS: "status",
            JOB_CREATE_TIME: datetime.now(),
            JOB_REQUIREMENTS: python_rule.recipe.requirements
        })
        self.assertFalse(status)

        status, s = lpc.valid_execute_criteria({
            JOB_ID: "path",
            JOB_EVENT: {
                EVENT_PATH: "path",
                EVENT_TYPE: EVENT_TYPE_WATCHDOG,
                EVENT_RULE: python_rule
            },
            JOB_TYPE: JOB_TYPE_PYTHON,
            JOB_PATTERN: python_rule.pattern.name,
            JOB_RECIPE: python_rule.recipe.name,
            JOB_RULE: python_rule.name,
            JOB_STATUS: "status",
            JOB_CREATE_TIME: datetime.now(),
            JOB_REQUIREMENTS: python_rule.recipe.requirements
        })
        self.assertTrue(status)

        status, s = lpc.valid_execute_criteria({
            JOB_ID: "path",
            JOB_EVENT: {
                EVENT_PATH: "path",
                EVENT_TYPE: EVENT_TYPE_WATCHDOG,
                EVENT_RULE: papermill_rule
            },
            JOB_TYPE: JOB_TYPE_PYTHON,
            JOB_PATTERN: papermill_rule.pattern.name,
            JOB_RECIPE: papermill_rule.recipe.name,
            JOB_RULE: papermill_rule.name,
            JOB_STATUS: "status",
            JOB_CREATE_TIME: datetime.now(),
            JOB_REQUIREMENTS: papermill_rule.recipe.requirements
        })
        self.assertTrue(status)

    # TODO test job status funcs
