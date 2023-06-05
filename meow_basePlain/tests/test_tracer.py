import importlib
import os
import unittest
import time

from multiprocessing import Pipe
from random import shuffle
from shutil import copy
from warnings import warn

from meow_base.core.base_conductor import BaseConductor
from meow_base.core.base_handler import BaseHandler
from meow_base.core.base_monitor import BaseMonitor
from meow_base.conductors import LocalPythonConductor
from meow_base.core.vars import JOB_TYPE_PAPERMILL, JOB_ERROR, \
    META_FILE, JOB_TYPE_PYTHON, JOB_CREATE_TIME, CREATED_FILES, JOB_RECIPE
from meow_base.core.runner import MeowRunner
from meow_base.functionality.file_io import make_dir, read_file, \
    read_notebook, read_yaml, write_file, lines_to_string
from meow_base.functionality.meow import create_parameter_sweep
from meow_base.functionality.requirements import create_python_requirements
from meow_base.patterns.file_event_pattern import WatchdogMonitor, \
    FileEventPattern
from meow_base.recipes.jupyter_notebook_recipe import PapermillHandler, \
    JupyterNotebookRecipe
from meow_base.recipes.python_recipe import PythonHandler, PythonRecipe
from meow_base.tests.shared import TEST_JOB_QUEUE, TEST_JOB_OUTPUT, TEST_MONITOR_BASE, \
    MAKER_RECIPE, APPENDING_NOTEBOOK, COMPLETE_PYTHON_SCRIPT, TEST_DIR, \
    FILTER_RECIPE, POROSITY_CHECK_NOTEBOOK, SEGMENT_FOAM_NOTEBOOK, \
    GENERATOR_NOTEBOOK, FOAM_PORE_ANALYSIS_NOTEBOOK, IDMC_UTILS_PYTHON_SCRIPT, \
    TEST_DATA, GENERATE_PYTHON_SCRIPT, BAREBONES_PYTHON_SCRIPT, MAKE_4FILES_PYTHON_SCRIPT,\
    MAKE_4FILES_PYTHON_MULTITHREADED_SCRIPT, \
    setup, teardown, backup_before_teardown, count_non_locks


class TracerTest(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()

    #setup the MEOW runner for python execution: 
    def testTracerPythonExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", os.path.join("start", "A.txt"), "recipe_one", "infile", 
            parameters={
                "num":10000,
                "outfile":os.path.join("{BASE}", "output", "{FILENAME}")
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

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                job_queue_dir=TEST_JOB_QUEUE
            ),
            LocalPythonConductor(pause_time=2),
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )

        # Intercept messages between the conductor and runner for testing
        conductor_to_test_conductor, conductor_to_test_test = Pipe(duplex=True)
        test_to_runner_runner, test_to_runner_test = Pipe(duplex=True)

        runner.conductors[0].to_runner_job = conductor_to_test_conductor

        for i in range(len(runner.job_connections)):
            _, obj = runner.job_connections[i]

            if obj == runner.conductors[0]:
                runner.job_connections[i] = (test_to_runner_runner, runner.job_connections[i][1])
      
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("25000")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))

        loops = 0
        while loops < 5:
            # Initial prompt
            if conductor_to_test_test.poll(5):
                msg = conductor_to_test_test.recv()
            else:
                raise Exception("Timed out")        
            self.assertEqual(msg, 1)
            test_to_runner_test.send(msg)

            # Reply
            if test_to_runner_test.poll(5):
                msg = test_to_runner_test.recv()
            else:
                raise Exception("Timed out")        
            job_dir = msg
            conductor_to_test_test.send(msg)

            if isinstance(job_dir, str):
                # Prompt again once complete
                if conductor_to_test_test.poll(5):
                    msg = conductor_to_test_test.recv()
                else:
                    raise Exception("Timed out")        
                self.assertEqual(msg, 1)
                loops = 5

            loops += 1

        job_dir = job_dir.replace(TEST_JOB_QUEUE, TEST_JOB_OUTPUT)

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 1)
        self.assertTrue(os.path.exists(job_dir))
        runner.stop()

        #Checking the .yaml metafile exists and that no error occured
        metafile = os.path.join(job_dir, META_FILE)
        status = read_yaml(metafile)
        self.assertNotIn(JOB_ERROR, status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list = status[CREATED_FILES]
        self.assertIsInstance(created_files_list, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        created_files_test = ['output', 'A.txt', 'output.log']
        self.assertCountEqual(created_files_list, created_files_test)
        

    def testTracerLinkedPythonExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":250,
                "outfile":os.path.join("{BASE}", "final", "{FILENAME}")
            })
        pattern_two = FileEventPattern(
            "pattern_two", 
            os.path.join("final", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":40,
                "outfile":os.path.join("{BASE}", "output", "{FILENAME}")
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

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                job_queue_dir=TEST_JOB_QUEUE
            ),
            LocalPythonConductor(pause_time=2),
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )        

        # Intercept messages between the conductor and runner for testing
        conductor_to_test_conductor, conductor_to_test_test = Pipe(duplex=True)
        test_to_runner_runner, test_to_runner_test = Pipe(duplex=True)

        runner.conductors[0].to_runner_job = conductor_to_test_conductor

        for i in range(len(runner.job_connections)):
            _, obj = runner.job_connections[i]

            if obj == runner.conductors[0]:
                runner.job_connections[i] = (test_to_runner_runner, runner.job_connections[i][1])
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("100")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))


        loops = 0
        job_ids = []
        while loops < 15:
            # Initial prompt
            if conductor_to_test_test.poll(5):
                msg = conductor_to_test_test.recv()
            else:
                raise Exception("Timed out")        
            self.assertEqual(msg, 1)
            test_to_runner_test.send(msg)

            # Reply
            if test_to_runner_test.poll(5):
                msg = test_to_runner_test.recv()
            else:
                raise Exception("Timed out")        
            conductor_to_test_test.send(msg)

            if len(job_ids) == 2:
                break

            if isinstance(msg, str):
                job_ids.append(msg.replace(TEST_JOB_QUEUE+os.path.sep, ''))

            loops += 1
        runner.stop()

        #Checking that there are 2 jobs and that they got a directory
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
            start_job_id = job_ids[0]
            final_job_id = job_ids[1]
        else:
            start_job_id = job_ids[1]
            final_job_id = job_ids[0]

        start_job_dir = os.path.join(TEST_JOB_OUTPUT, start_job_id)

        #This also checks that the strace output file was succesfully removed when the runner stops. 
        self.assertEqual(count_non_locks(start_job_dir), 4)

        #Checking the .yaml metafile exists and that no error occured
        start_metafile = os.path.join(start_job_dir, META_FILE)
        start_status = read_yaml(start_metafile)
        self.assertNotIn(JOB_ERROR, start_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list0 = start_status[CREATED_FILES]
        self.assertIsInstance(created_files_list0, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        #This job should create an output.log file and then create a directory 'final' in which it puts 'A.txt'
        created_files_start = ['final', 'A.txt', 'output.log']
        self.assertCountEqual(created_files_list0, created_files_start)

        start_result_path = os.path.join(
            start_job_dir, "output.log")
        self.assertTrue(os.path.exists(start_result_path))
        start_result = read_file(os.path.join(start_result_path))
        self.assertEqual(
            start_result, "7806.25\ndone\n")

        start_output_path = os.path.join(TEST_MONITOR_BASE, "final", "A.txt")
        self.assertTrue(os.path.exists(start_output_path))
        start_output = read_file(os.path.join(start_output_path))
        self.assertEqual(start_output, "7806.25")

        final_job_dir = os.path.join(TEST_JOB_OUTPUT, final_job_id)
        self.assertEqual(count_non_locks(final_job_dir), 4)

        final_metafile = os.path.join(final_job_dir, META_FILE)
        final_status = read_yaml(final_metafile)
        self.assertNotIn(JOB_ERROR, final_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list1 = final_status[CREATED_FILES]
        self.assertIsInstance(created_files_list1, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        #This creates a directory 'output' in which it places 'A.txt'. 
        created_files_final = ['output', 'output.log', 'A.txt']
        self.assertCountEqual(created_files_list1, created_files_final)

        final_result_path = os.path.join(final_job_dir, "output.log")
        self.assertTrue(os.path.exists(final_result_path))
        final_result = read_file(os.path.join(final_result_path))
        self.assertEqual(
            final_result, "2146.5625\ndone\n")

        final_output_path = os.path.join(TEST_MONITOR_BASE, "output", "A.txt")
        self.assertTrue(os.path.exists(final_output_path))
        final_output = read_file(os.path.join(final_output_path))
        self.assertEqual(final_output, "2146.5625")
    
    def testTracerLinkedPythonExecutionDifferentOutputs(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":250,
                "outfile":os.path.join("{BASE}", "middle", "{FILENAME}")
            })
        pattern_two = FileEventPattern(
            "pattern_two", 
            os.path.join("middle", "A.txt"), 
            "recipe_two", 
            "infile",
            parameters={
                "current_directory": os.getcwd()
            })
        
        recipe1 = PythonRecipe(
            "recipe_one", COMPLETE_PYTHON_SCRIPT
        )

        recipe2 = PythonRecipe(
            "recipe_two", MAKE_4FILES_PYTHON_SCRIPT
        )
        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
        }
        recipes = {
            recipe1.name: recipe1,
            recipe2.name: recipe2
        }

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                job_queue_dir=TEST_JOB_QUEUE
            ),
            LocalPythonConductor(pause_time=2),
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )        

        # Intercept messages between the conductor and runner for testing
        conductor_to_test_conductor, conductor_to_test_test = Pipe(duplex=True)
        test_to_runner_runner, test_to_runner_test = Pipe(duplex=True)

        runner.conductors[0].to_runner_job = conductor_to_test_conductor

        for i in range(len(runner.job_connections)):
            _, obj = runner.job_connections[i]

            if obj == runner.conductors[0]:
                runner.job_connections[i] = (test_to_runner_runner, runner.job_connections[i][1])
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("100")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))


        loops = 0
        job_ids = []
        while loops < 15:
            # Initial prompt
            if conductor_to_test_test.poll(5):
                msg = conductor_to_test_test.recv()
            else:
                raise Exception("Timed out")        
            self.assertEqual(msg, 1)
            test_to_runner_test.send(msg)

            # Reply
            if test_to_runner_test.poll(5):
                msg = test_to_runner_test.recv()
            else:
                raise Exception("Timed out")        
            conductor_to_test_test.send(msg)

            if len(job_ids) == 2:
                break

            if isinstance(msg, str):
                job_ids.append(msg.replace(TEST_JOB_QUEUE+os.path.sep, ''))

            loops += 1
        runner.stop()

        #Checking that there are 2 jobs and that they got a directory
        self.assertEqual(len(job_ids), 2)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 2)
        self.assertIn(job_ids[0], os.listdir(TEST_JOB_OUTPUT))
        self.assertIn(job_ids[1], os.listdir(TEST_JOB_OUTPUT))


        meta0 = os.path.join(TEST_JOB_OUTPUT, job_ids[0], META_FILE)
        status0 = read_yaml(meta0)
        recipe_job0 = status0[JOB_RECIPE]
        meta1 = os.path.join(TEST_JOB_OUTPUT, job_ids[1], META_FILE)
        status1 = read_yaml(meta1)
        recipe_job1 = status1[JOB_RECIPE]
        #If job0 is recipe one it has 4 files in the .yaml 'created_files'. If not, there should be 8. 
        if recipe_job0 == 'recipe_one':
            job_with_4_output_files_id = job_ids[0]
            job_with_8_output_files_id = job_ids[1]
        else:
            job_with_4_output_files_id = job_ids[1]
            job_with_8_output_files_id = job_ids[0]
        
        

        job_with_4_output_files_dir = os.path.join(TEST_JOB_OUTPUT, job_with_4_output_files_id)


        #Checking the .yaml metafile exists and that no error occured
        job_4_output_files_metafile = os.path.join(job_with_4_output_files_dir, META_FILE)
        job_4_output_files_status = read_yaml(job_4_output_files_metafile)
        self.assertNotIn(JOB_ERROR, job_4_output_files_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list0 = job_4_output_files_status[CREATED_FILES]
        self.assertIsInstance(created_files_list0, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        created_files_test_first_job = ['output.log', 'middle', 'A.txt']
        self.assertCountEqual(created_files_list0, created_files_test_first_job)

        

        job_with_4_files_dir = os.path.join(TEST_JOB_OUTPUT, job_with_8_output_files_id)

        job_with_4_files_metafile = os.path.join(job_with_4_files_dir, META_FILE)
        job_with_4_files_status = read_yaml(job_with_4_files_metafile)
        self.assertNotIn(JOB_ERROR, job_with_4_files_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list1 = job_with_4_files_status[CREATED_FILES]
        self.assertIsInstance(created_files_list1, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        job_with_4_files_outputs = ['output.log','file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']
        self.assertCountEqual(created_files_list1, job_with_4_files_outputs)

    def testTracerMultiThreadedFileCreationPythonExecution(self)->None:
        pattern_one = FileEventPattern(
            "pattern_one", 
            os.path.join("start", "A.txt"), 
            "recipe_one", 
            "infile", 
            parameters={
                "num":250,
                "outfile":os.path.join("{BASE}", "middle", "{FILENAME}")
            })
        pattern_two = FileEventPattern(
            "pattern_two", 
            os.path.join("middle", "A.txt"), 
            "recipe_two", 
            "infile",
            parameters={
                "current_directory": os.getcwd()
            })
        
        recipe1 = PythonRecipe(
            "recipe_one", COMPLETE_PYTHON_SCRIPT
        )

        recipe2 = PythonRecipe(
            "recipe_two", MAKE_4FILES_PYTHON_MULTITHREADED_SCRIPT
        )
        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
        }
        recipes = {
            recipe1.name: recipe1,
            recipe2.name: recipe2
        }

        runner = MeowRunner(
            WatchdogMonitor(
                TEST_MONITOR_BASE,
                patterns,
                recipes,
                settletime=1
            ), 
            PythonHandler(
                job_queue_dir=TEST_JOB_QUEUE
            ),
            LocalPythonConductor(pause_time=2),
            job_queue_dir=TEST_JOB_QUEUE,
            job_output_dir=TEST_JOB_OUTPUT
        )        

        # Intercept messages between the conductor and runner for testing
        conductor_to_test_conductor, conductor_to_test_test = Pipe(duplex=True)
        test_to_runner_runner, test_to_runner_test = Pipe(duplex=True)

        runner.conductors[0].to_runner_job = conductor_to_test_conductor

        for i in range(len(runner.job_connections)):
            _, obj = runner.job_connections[i]

            if obj == runner.conductors[0]:
                runner.job_connections[i] = (test_to_runner_runner, runner.job_connections[i][1])
   
        runner.start()

        start_dir = os.path.join(TEST_MONITOR_BASE, "start")
        make_dir(start_dir)
        self.assertTrue(start_dir)
        with open(os.path.join(start_dir, "A.txt"), "w") as f:
            f.write("100")

        self.assertTrue(os.path.exists(os.path.join(start_dir, "A.txt")))


        loops = 0
        job_ids = []
        while loops < 15:
            # Initial prompt
            if conductor_to_test_test.poll(5):
                msg = conductor_to_test_test.recv()
            else:
                raise Exception("Timed out")        
            self.assertEqual(msg, 1)
            test_to_runner_test.send(msg)

            # Reply
            if test_to_runner_test.poll(5):
                msg = test_to_runner_test.recv()
            else:
                raise Exception("Timed out")        
            conductor_to_test_test.send(msg)

            if len(job_ids) == 2:
                break

            if isinstance(msg, str):
                job_ids.append(msg.replace(TEST_JOB_QUEUE+os.path.sep, ''))

            loops += 1
        runner.stop()

        #Checking that there are 2 jobs and that they got a directory
        self.assertEqual(len(job_ids), 2)
        self.assertEqual(len(os.listdir(TEST_JOB_OUTPUT)), 2)
        self.assertIn(job_ids[0], os.listdir(TEST_JOB_OUTPUT))
        self.assertIn(job_ids[1], os.listdir(TEST_JOB_OUTPUT))


        meta0 = os.path.join(TEST_JOB_OUTPUT, job_ids[0], META_FILE)
        status0 = read_yaml(meta0)
        recipe_job0 = status0[JOB_RECIPE]
        meta1 = os.path.join(TEST_JOB_OUTPUT, job_ids[1], META_FILE)
        status1 = read_yaml(meta1)
        recipe_job1 = status1[JOB_RECIPE]
        #If job0 is recipe one it has 4 files in the .yaml 'created_files'. If not, there should be 8. 
        if recipe_job0 == 'recipe_one':
            job_with_4_output_files_id = job_ids[0]
            job_with_8_output_files_id = job_ids[1]
        else:
            job_with_4_output_files_id = job_ids[1]
            job_with_8_output_files_id = job_ids[0]
        
        

        job_with_4_output_files_dir = os.path.join(TEST_JOB_OUTPUT, job_with_4_output_files_id)


        #Checking the .yaml metafile exists and that no error occured
        job_4_output_files_metafile = os.path.join(job_with_4_output_files_dir, META_FILE)
        job_4_output_files_status = read_yaml(job_4_output_files_metafile)
        self.assertNotIn(JOB_ERROR, job_4_output_files_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list0 = job_4_output_files_status[CREATED_FILES]
        self.assertIsInstance(created_files_list0, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        created_files_test_4_outputs = ['A.txt', 'output.log', 'middle']
        self.assertCountEqual(created_files_list0, created_files_test_4_outputs)

        

        job_with_8_output_files_dir = os.path.join(TEST_JOB_OUTPUT, job_with_8_output_files_id)

        job_with_8_output_files_metafile = os.path.join(job_with_8_output_files_dir, META_FILE)
        job_with_8_output_files_status = read_yaml(job_with_8_output_files_metafile)
        self.assertNotIn(JOB_ERROR, job_with_8_output_files_status)

        #Checking that the YAML object CREATED_FILES from vars.py is a list
        created_files_list1 = job_with_8_output_files_status[CREATED_FILES]
        self.assertIsInstance(created_files_list1, list)

        #Checking that the list contains the expected files. Order of the files in the lists is not important:  
        created_files_test_8_outputs = ['output.log', 'file1.txt', 'file2.txt', 'file3.txt', 'file4.txt']
        self.assertCountEqual(created_files_list1, created_files_test_8_outputs)
