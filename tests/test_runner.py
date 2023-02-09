
import io
import os
import unittest
 
from time import sleep

from conductors import LocalPythonConductor
from core.correctness.vars import get_result_file, \
    JOB_TYPE_PAPERMILL, JOB_ERROR, META_FILE, JOB_TYPE_PYTHON, JOB_CREATE_TIME
from core.functionality import make_dir, read_notebook, read_yaml, read_file
from core.meow import BaseMonitor, BaseHandler, BaseConductor
from core.runner import MeowRunner
from patterns.file_event_pattern import WatchdogMonitor, FileEventPattern
from recipes.jupyter_notebook_recipe import PapermillHandler, \
    JupyterNotebookRecipe
from recipes.python_recipe import PythonHandler, PythonRecipe
from shared import setup, teardown, \
    TEST_HANDLER_BASE, TEST_JOB_OUTPUT, TEST_MONITOR_BASE, \
    APPENDING_NOTEBOOK, COMPLETE_PYTHON_SCRIPT


class MeowTests(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()
        
    # Test MeowRunner creation
    def testMeowRunnerSetup(self)->None:

        monitor_one = WatchdogMonitor(TEST_MONITOR_BASE, {}, {})
        monitor_two = WatchdogMonitor(TEST_MONITOR_BASE, {}, {})
        monitors = [ monitor_one, monitor_two ]

        handler_one = PapermillHandler(TEST_HANDLER_BASE, TEST_JOB_OUTPUT)
        handler_two = PapermillHandler(TEST_HANDLER_BASE, TEST_JOB_OUTPUT)
        handlers = [ handler_one, handler_two ]

        conductor_one = LocalPythonConductor()
        conductor_two = LocalPythonConductor()
        conductors = [ conductor_one, conductor_two ]

        runner = MeowRunner(monitor_one, handler_one, conductor_one)

        self.assertIsInstance(runner.monitors, list)
        for m in runner.monitors:
            self.assertIsInstance(m, BaseMonitor)
        self.assertEqual(len(runner.monitors), 1)
        self.assertEqual(runner.monitors[0], monitor_one)

        self.assertIsInstance(runner.from_monitors, list)
        self.assertEqual(len(runner.from_monitors), 1)
        runner.monitors[0].to_runner.send("monitor test message")
        message = None
        if runner.from_monitors[0].poll(3):
            message = runner.from_monitors[0].recv()
        self.assertIsNotNone(message)
        self.assertEqual(message, "monitor test message")

        self.assertIsInstance(runner.handlers, list)
        for handler in runner.handlers:
            self.assertIsInstance(handler, BaseHandler)

        self.assertIsInstance(runner.from_handlers, list)
        self.assertEqual(len(runner.from_handlers), 1)
        runner.handlers[0].to_runner.send(
            "handler test message")
        message = None
        if runner.from_handlers[0].poll(3):
            message = runner.from_handlers[0].recv()
        self.assertIsNotNone(message)
        self.assertEqual(message, "handler test message")

        self.assertIsInstance(runner.conductors, list)        
        for conductor in runner.conductors:
            self.assertIsInstance(conductor, BaseConductor)

        runner = MeowRunner(monitors, handlers, conductors)

        self.assertIsInstance(runner.monitors, list)
        for m in runner.monitors:
            self.assertIsInstance(m, BaseMonitor)
        self.assertEqual(len(runner.monitors), len(monitors))
        self.assertIn(monitor_one, runner.monitors)
        self.assertIn(monitor_two, runner.monitors)

        self.assertIsInstance(runner.from_monitors, list)
        self.assertEqual(len(runner.from_monitors), len(monitors))
        for rm in runner.monitors:
            rm.to_runner.send("monitor test message")
        messages = [None] * len(monitors)
        for i, rfm in enumerate(runner.from_monitors):
            if rfm.poll(3):
                messages[i] = rfm.recv()
        for m in messages:
            self.assertIsNotNone(m)
            self.assertEqual(m, "monitor test message")

        self.assertIsInstance(runner.handlers, list)
        for handler in runner.handlers:
            self.assertIsInstance(handler, BaseHandler)

        self.assertIsInstance(runner.from_handlers, list)
        self.assertEqual(len(runner.from_handlers), len(handlers))
        for rh in runner.handlers:
            rh.to_runner.send("handler test message")
        message = None
        if runner.from_handlers[0].poll(3):
            message = runner.from_handlers[0].recv()
        self.assertIsNotNone(message)
        self.assertEqual(message, "handler test message")

        self.assertIsInstance(runner.conductors, list)
        for conductor in runner.conductors:
            self.assertIsInstance(conductor, BaseConductor)

    # Test single meow papermill job execution
    def testMeowRunnerPapermillExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from a test Pattern",
                "outfile":os.path.join("{VGRID}", "output", "{FILENAME}")
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        patterns = {
            pattern_one.name: pattern_one,
        }
        recipes = {
            recipe.name: recipe,
        }

        runner_debug_stream = io.StringIO("")

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PapermillHandler(
                TEST_HANDLER_BASE,
                TEST_JOB_OUTPUT,
            ),
            LocalPythonConductor(),
            print=runner_debug_stream,
            logging=3                
        )        
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("Initial Data")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))

        loops = 0
        job_id = None
        while loops < 15:
            sleep(1)
            runner_debug_stream.seek(0)
            messages = runner_debug_stream.readlines()

            for msg in messages:
                self.assertNotIn("ERROR", msg)
            
                if "INFO: Completed execution for job: '" in msg:
                    job_id = msg.replace(
                        "INFO: Completed execution for job: '", "")
                    job_id = job_id[:-2]
                    loops = 15
            loops += 1

        self.assertIsNotNone(job_id)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 1)
        self.assertIn(job_id, os.listdir(TEST_JOB_OUTPUT))

        runner.stop()

        job_dir = os.path.join(TEST_JOB_OUTPUT, job_id)
        self.assertEqual(len(os.listdir(job_dir)), 5)

        result = read_notebook(
            os.path.join(job_dir, get_result_file(JOB_TYPE_PAPERMILL)))
        self.assertIsNotNone(result)

        output_path = os.path.join(TEST_MONITOR_BASE, "output", "A.txt")
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, "r") as f:
            data = f.read()
        
        self.assertEqual(data, "Initial Data\nA line from a test Pattern")

    # Test meow papermill job chaining within runner
    def testMeowRunnerLinkedPapermillExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "extra":"A line from Pattern 1",
                "outfile":os.path.join("{VGRID}", "middle", "{FILENAME}")
            })
        pattern_two = FileEventPattern(
            "pattern_two", os.path.join("middle", "A.txt"), "recipe_one", "infile", 
            parameters={
                "extra":"A line from Pattern 2",
                "outfile":os.path.join("{VGRID}", "output", "{FILENAME}")
            })
        recipe = JupyterNotebookRecipe(
            "recipe_one", APPENDING_NOTEBOOK)

        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
        }
        recipes = {
            recipe.name: recipe,
        }

        runner_debug_stream = io.StringIO("")

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PapermillHandler(
                TEST_HANDLER_BASE,
                TEST_JOB_OUTPUT
            ),
            LocalPythonConductor(),
            print=runner_debug_stream,
            logging=3
        )        
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("Initial Data")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))

        loops = 0
        job_ids = []
        while len(job_ids) < 2 and loops < 15:
            sleep(1)
            runner_debug_stream.seek(0)
            messages = runner_debug_stream.readlines()

            for msg in messages:
                self.assertNotIn("ERROR", msg)
            
                if "INFO: Completed execution for job: '" in msg:
                    job_id = msg.replace(
                        "INFO: Completed execution for job: '", "")
                    job_id = job_id[:-2]
                    if job_id not in job_ids:
                        job_ids.append(job_id)
            loops += 1

        self.assertEqual(len(job_ids), 2)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 2)
        self.assertIn(job_ids[0], os.listdir(TEST_JOB_OUTPUT))
        self.assertIn(job_ids[1], os.listdir(TEST_JOB_OUTPUT))

        runner.stop()

        mid_job_dir = os.path.join(TEST_JOB_OUTPUT, job_id)
        self.assertEqual(len(os.listdir(mid_job_dir)), 5)

        result = read_notebook(
            os.path.join(mid_job_dir, get_result_file(JOB_TYPE_PAPERMILL)))
        self.assertIsNotNone(result)

        mid_output_path = os.path.join(TEST_MONITOR_BASE, "middle", "A.txt")
        self.assertTrue(os.path.exists(mid_output_path))
        
        with open(mid_output_path, "r") as f:
            data = f.read()
        
        self.assertEqual(data, "Initial Data\nA line from Pattern 1")

        final_job_dir = os.path.join(TEST_JOB_OUTPUT, job_id)
        self.assertEqual(len(os.listdir(final_job_dir)), 5)

        result = read_notebook(os.path.join(final_job_dir, 
            get_result_file(JOB_TYPE_PAPERMILL)))
        self.assertIsNotNone(result)

        final_output_path = os.path.join(TEST_MONITOR_BASE, "output", "A.txt")
        self.assertTrue(os.path.exists(final_output_path))
        
        with open(final_output_path, "r") as f:
            data = f.read()
        
        self.assertEqual(data, 
            "Initial Data\nA line from Pattern 1\nA line from Pattern 2")

    # Test single meow python job execution
    def testMeowRunnerPythonExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", os.path.join("start", "A.txt"), "recipe_one", "infile", 
            parameters={
                "num":10000,
                "outfile":os.path.join("{VGRID}", "output", "{FILENAME}")
            })
        recipe = PythonRecipe(
            "recipe_one", COMPLETE_PYTHON_SCRIPT
        )

        patterns = {
            pattern_one.name: pattern_one,
        }
        recipes = {
            recipe.name: recipe,
        }

        runner_debug_stream = io.StringIO("")

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                TEST_HANDLER_BASE,
                TEST_JOB_OUTPUT,
            ),
            LocalPythonConductor(),
            print=runner_debug_stream,
            logging=3                
        )        
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("25000")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))

        loops = 0
        job_id = None
        while loops < 15:
            sleep(1)
            runner_debug_stream.seek(0)
            messages = runner_debug_stream.readlines()

            for msg in messages:
                self.assertNotIn("ERROR", msg)
            
                if "INFO: Completed execution for job: '" in msg:
                    job_id = msg.replace(
                        "INFO: Completed execution for job: '", "")
                    job_id = job_id[:-2]
                    loops = 15
            loops += 1

        self.assertIsNotNone(job_id)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 1)
        self.assertIn(job_id, os.listdir(TEST_JOB_OUTPUT))

        runner.stop()

        job_dir = os.path.join(TEST_JOB_OUTPUT, job_id)
        print(os.listdir(job_dir))

        metafile = os.path.join(job_dir, META_FILE)
        status = read_yaml(metafile)

        self.assertNotIn(JOB_ERROR, status)

        result_path = os.path.join(job_dir, get_result_file(JOB_TYPE_PYTHON))
        self.assertTrue(os.path.exists(result_path))
        result = read_file(os.path.join(result_path))
        self.assertEqual(
            result, "--STDOUT--\n12505000.0\ndone\n\n\n--STDERR--\n\n")

        output_path = os.path.join(TEST_MONITOR_BASE, "output", "A.txt")
        self.assertTrue(os.path.exists(output_path))
        output = read_file(os.path.join(output_path))
        self.assertEqual(output, "12505000.0")
        
    # Test meow python job chaining within runner
    def testMeowRunnerLinkedPythonExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":250,
                "outfile":os.path.join("{VGRID}", "middle", "{FILENAME}")
            })
        pattern_two = FileEventPattern(
            "pattern_two", 
            os.path.join("middle", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":40,
                "outfile":os.path.join("{VGRID}", "output", "{FILENAME}")
            })
        recipe = PythonRecipe(
            "recipe_one", COMPLETE_PYTHON_SCRIPT
        )

        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
        }
        recipes = {
            recipe.name: recipe,
        }

        runner_debug_stream = io.StringIO("")

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                TEST_HANDLER_BASE,
                TEST_JOB_OUTPUT
            ),
            LocalPythonConductor(),
            print=runner_debug_stream,
            logging=3
        )        
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("100")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))

        loops = 0
        job_ids = []
        while len(job_ids) < 2 and loops < 15:
            sleep(1)
            runner_debug_stream.seek(0)
            messages = runner_debug_stream.readlines()

            for msg in messages:
                self.assertNotIn("ERROR", msg)
            
                if "INFO: Completed execution for job: '" in msg:
                    job_id = msg.replace(
                        "INFO: Completed execution for job: '", "")
                    job_id = job_id[:-2]
                    if job_id not in job_ids:
                        job_ids.append(job_id)
            loops += 1

        runner.stop()

        self.assertEqual(len(job_ids), 2)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 2)
        self.assertIn(job_ids[0], os.listdir(TEST_JOB_OUTPUT))
        self.assertIn(job_ids[1], os.listdir(TEST_JOB_OUTPUT))

        meta0 = os.path.join(TEST_JOB_OUTPUT, job_ids[0], META_FILE)
        status0 = read_yaml(meta0)
        create0 = status0[JOB_CREATE_TIME]
        meta1 = os.path.join(TEST_JOB_OUTPUT, job_ids[1], META_FILE)
        status1 = read_yaml(meta1)
        create1 = status1[JOB_CREATE_TIME]
        if create0 < create1:
            mid_job_id = job_ids[0]
            final_job_id = job_ids[1]
        else:
            mid_job_id = job_ids[1]
            final_job_id = job_ids[0]

        mid_job_dir = os.path.join(TEST_JOB_OUTPUT, mid_job_id)
        self.assertEqual(len(os.listdir(mid_job_dir)), 5)

        mid_metafile = os.path.join(mid_job_dir, META_FILE)
        mid_status = read_yaml(mid_metafile)
        self.assertNotIn(JOB_ERROR, mid_status)

        mid_result_path = os.path.join(
            mid_job_dir, get_result_file(JOB_TYPE_PYTHON))
        self.assertTrue(os.path.exists(mid_result_path))
        mid_result = read_file(os.path.join(mid_result_path))
        self.assertEqual(
            mid_result, "--STDOUT--\n7806.25\ndone\n\n\n--STDERR--\n\n")

        mid_output_path = os.path.join(TEST_MONITOR_BASE, "middle", "A.txt")
        self.assertTrue(os.path.exists(mid_output_path))
        mid_output = read_file(os.path.join(mid_output_path))
        self.assertEqual(mid_output, "7806.25")

        final_job_dir = os.path.join(TEST_JOB_OUTPUT, final_job_id)
        self.assertEqual(len(os.listdir(final_job_dir)), 5)

        final_metafile = os.path.join(final_job_dir, META_FILE)
        final_status = read_yaml(final_metafile)
        self.assertNotIn(JOB_ERROR, final_status)

        final_result_path = os.path.join(final_job_dir, get_result_file(JOB_TYPE_PYTHON))
        self.assertTrue(os.path.exists(final_result_path))
        final_result = read_file(os.path.join(final_result_path))
        self.assertEqual(
            final_result, "--STDOUT--\n2146.5625\ndone\n\n\n--STDERR--\n\n")

        final_output_path = os.path.join(TEST_MONITOR_BASE, "output", "A.txt")
        self.assertTrue(os.path.exists(final_output_path))
        final_output = read_file(os.path.join(final_output_path))
        self.assertEqual(final_output, "2146.5625")
       
    # TODO sweep execution test
    # TODO adding tests with numpy or other external dependency
    # TODO test getting job cannot handle
    # TODO test getting event cannot handle
    # TODO test with several matched monitors
    # TODO test with several mismatched monitors
    # TODO test with several matched handlers
    # TODO test with several mismatched handlers
    # TODO test with several matched conductors
    # TODO test with several mismatched conductors
