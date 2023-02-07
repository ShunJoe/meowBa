
import io
import unittest
import os

from datetime import datetime
from typing import Any, Union

from core.correctness.validation import check_type, check_implementation, \
    valid_string, valid_dict, valid_list, valid_existing_file_path, \
    valid_existing_dir_path, valid_non_existing_path, valid_event, valid_job, \
    setup_debugging, valid_watchdog_event, check_callable
from core.correctness.vars import VALID_NAME_CHARS, SHA256, EVENT_TYPE, \
    EVENT_PATH, JOB_TYPE, JOB_EVENT, JOB_ID, JOB_PATTERN, JOB_RECIPE, \
    JOB_RULE, JOB_STATUS, JOB_CREATE_TIME, EVENT_RULE, WATCHDOG_BASE, \
    WATCHDOG_HASH
from core.functionality import make_dir
from shared import setup, teardown, TEST_MONITOR_BASE

class CorrectnessTests(unittest.TestCase):
    def setUp(self)->None:
        super().setUp()
        setup()

    def tearDown(self)->None:
        super().tearDown()
        teardown()
        
    # Test check_type accepts valid types
    def testCheckTypeValid(self)->None:
        check_type(1, int)
        check_type(0, int)
        check_type(False, bool)
        check_type(True, bool)

    # Test check_type accepts Any type
    def testCheckTypeValidAny(self)->None:
        check_type(1, Any)

    # Test check_type accepts Union of types
    def testCheckTypeValidUnion(self)->None:
        check_type(1, Union[int,str])
        with self.assertRaises(TypeError):
            check_type(Union[int, str], Union[int,str])
        
    # Test check_type raises on mismatched type
    def testCheckTypeMistyped(self)->None:
        with self.assertRaises(TypeError):
            check_type(1, str)

    # Test or_none arg for check_type
    def testCheckTypeOrNone(self)->None:
        check_type(None, int, or_none=True)
        with self.assertRaises(TypeError):
            check_type(None, int, or_none=False)

    # Test valid_string with valid chars
    def testValidStringValid(self)->None:
        valid_string("David_Marchant", VALID_NAME_CHARS)

    # Test valid_string with empty input
    def testValidStringEmptyString(self)->None:
        valid_string("", VALID_NAME_CHARS, min_length=0)

    # Test valid_string with no valid chars
    def testValidStringNoValidChars(self)->None:
        with self.assertRaises(ValueError):
            valid_string("David_Marchant", "")

    # Test valid_string with wrong types
    def testValidStringMistypedInput(self)->None:
        with self.assertRaises(TypeError):
            valid_string(1, VALID_NAME_CHARS)
        with self.assertRaises(TypeError):
            valid_string("David_Marchant", 1)

    # Test valid_string with invalid chars
    def testValidStringMissingChars(self)->None:
        with self.assertRaises(ValueError):
            valid_string("David Marchant", VALID_NAME_CHARS)

    # Test valid_string with not long enough input
    def testValidStringInsufficientLength(self)->None:
        with self.assertRaises(ValueError):
            valid_string("", VALID_NAME_CHARS)
            valid_string("David Marchant", VALID_NAME_CHARS, min_length=50)

    # Test valid_dict with not long enough input
    def testValidDictMinimum(self)->None:
        valid_dict({"a": 0, "b": 1}, str, int, strict=False)

    # Test valid_dict with invalid key types
    def testValidDictAnyKeyType(self)->None:
        valid_dict({"a": 0, "b": 1}, Any, int, strict=False)

    # Test valid_dict with invalid value types
    def testValidDictAnyValueType(self)->None:
        valid_dict({"a": 0, "b": 1}, str, Any, strict=False)

    # Test valid_dict with required keys
    def testValidDictAllRequiredKeys(self)->None:
        valid_dict({"a": 0, "b": 1}, str, int, required_keys=["a", "b"])

    # Test valid_dict with required and optional keys
    def testValidDictAllRequiredOrOptionalKeys(self)->None:
        valid_dict(
            {"a": 0, "b": 1}, str, int, required_keys=["a"], 
            optional_keys=["b"])

    # Test valid_dict with extra keys
    def testValidDictExtraKeys(self)->None:
        valid_dict(
            {"a": 0, "b": 1, "c": 2}, str, int, required_keys=["a"], 
            optional_keys=["b"], strict=False)

    # Test valid_dict with missing required keys
    def testValidDictMissingRequiredKeys(self)->None:
        with self.assertRaises(KeyError):
            valid_dict(
                {"a": 0, "b": 1}, str, int, required_keys=["a", "b", "c"])

    # Test strict checking of valid_dict
    def testValidDictOverlyStrict(self)->None:
        with self.assertRaises(ValueError):
            valid_dict({"a": 0, "b": 1}, str, int, strict=True)

    # Test valid_list with sufficent lengths
    def testValidListMinimum(self)->None:
        valid_list([1, 2, 3], int)
        valid_list(["1", "2", "3"], str)
        valid_list([1], int)

    # Test valid_list with alternate types
    def testValidListAltTypes(self)->None:
        valid_list([1, "2", 3], int, alt_types=[str])

    # Test valid_list with wrong type
    def testValidListMismatchedNotList(self)->None:
        with self.assertRaises(TypeError):
            valid_list((1, 2, 3), int)

    # Test valid_list with mismatch value types
    def testValidListMismatchedType(self)->None:
        with self.assertRaises(TypeError):
            valid_list([1, 2, 3], str)

    # Test valid_list with insufficient length
    def testValidListMinLength(self)->None:
        with self.assertRaises(ValueError):
            valid_list([1, 2, 3], str, min_length=10)

    # Test check_implementation doesn't raise on implemented
    def testCheckImplementationMinimum(self)->None:
        class Parent:
            def func():
                pass

        class Child(Parent):
            def func():
                pass

        check_implementation(Child.func, Parent)

    # Test check_implementation does raise on not implemented
    def testCheckImplementationUnaltered(self)->None:
        class Parent:
            def func():
                pass

        class Child(Parent):
            pass
        
        with self.assertRaises(NotImplementedError):
            check_implementation(Child.func, Parent)

    # Test check_implementation does raise on differing signature
    def testCheckImplementationDifferingSig(self)->None:
        class Parent:
            def func():
                pass

        class Child(Parent):
            def func(var):
                pass
        
        with self.assertRaises(NotImplementedError):
            check_implementation(Child.func, Parent)

    # Test check_implementation doesn't raise on Any type in signature
    def testCheckImplementationAnyType(self)->None:
        class Parent:
            def func(var:Any):
                pass

        class Child(Parent):
            def func(var:str):
                pass
        
        check_implementation(Child.func, Parent)

    # Test valid_existing_file_path can find files, or not
    def testValidExistingFilePath(self)->None:
        file_path = os.path.join(TEST_MONITOR_BASE, "file.txt")
        with open(file_path, 'w') as hashed_file:
            hashed_file.write("Some data\n")

        valid_existing_file_path(file_path)

        with self.assertRaises(FileNotFoundError):        
            valid_existing_file_path("not_existing_"+file_path, SHA256)

        dir_path = os.path.join(TEST_MONITOR_BASE, "dir")
        make_dir(dir_path)

        with self.assertRaises(ValueError):        
            valid_existing_file_path(dir_path, SHA256)
    
    # Test valid_existing_dir_path can find directories, or not
    def testValidExistingDirPath(self)->None:
        valid_existing_dir_path(TEST_MONITOR_BASE)

        dir_path = os.path.join(TEST_MONITOR_BASE, "dir")

        with self.assertRaises(FileNotFoundError):        
            valid_existing_dir_path("not_existing_"+dir_path, SHA256)

        file_path = os.path.join(TEST_MONITOR_BASE, "file.txt")
        with open(file_path, 'w') as hashed_file:
            hashed_file.write("Some data\n")

        with self.assertRaises(ValueError):        
            valid_existing_dir_path(file_path, SHA256)

    # Test valid_non_existing_path can find existing paths, or not
    def testValidNonExistingPath(self)->None:
        valid_non_existing_path("does_not_exist")

        make_dir("first")
        with self.assertRaises(ValueError):
            valid_non_existing_path("first")

        make_dir("first/second")
        with self.assertRaises(ValueError):
            valid_non_existing_path("first/second")

    # TODO modify so tests for actual rule values
    # Test valid_event can check given event dictionary
    def testEventValidation(self)->None:
        valid_event({
            EVENT_TYPE: "test", 
            EVENT_PATH: "path", 
            EVENT_RULE: "rule"
        })
        valid_event({
            EVENT_TYPE: "anything", 
            EVENT_PATH: "path", 
            EVENT_RULE: "rule",
            "a": 1
        })

        with self.assertRaises(KeyError):
            valid_event({EVENT_TYPE: "test"})

        with self.assertRaises(KeyError):
            valid_event({"EVENT_TYPE": "test"})

        with self.assertRaises(KeyError):
            valid_event({})

    # Test valid_job can check given job dictionary
    def testJobValidation(self)->None:
        valid_job({
            JOB_TYPE: "test", 
            JOB_EVENT: {},
            JOB_ID: "id",
            JOB_PATTERN: "pattern",
            JOB_RECIPE: "recipe",
            JOB_RULE: "rule",
            JOB_STATUS: "status",
            JOB_CREATE_TIME: datetime.now()
        })

        with self.assertRaises(KeyError):
            valid_job({JOB_TYPE: "test"})

        with self.assertRaises(KeyError):
            valid_job({"JOB_TYPE": "test"})

        with self.assertRaises(KeyError):
            valid_job({})

    # Test setup_debugging will create writeable location
    def testSetupDebugging(self)->None:
        stream = io.StringIO("")

        target, level = setup_debugging(stream, 1)

        self.assertIsInstance(target, io.StringIO)
        self.assertIsInstance(level, int)

        with self.assertRaises(TypeError):
            setup_debugging("stream", 1)

        with self.assertRaises(TypeError):
            setup_debugging(stream, "1")

    # Test watchdog event dict
    def testWatchdogEventValidation(self)->None:
        valid_watchdog_event({
            EVENT_TYPE: "test", 
            EVENT_PATH: "path", 
            EVENT_RULE: "rule",
            WATCHDOG_HASH: "hash",
            WATCHDOG_BASE: "base"
        })

        with self.assertRaises(KeyError):
            valid_watchdog_event({
                EVENT_TYPE: "test", 
                EVENT_PATH: "path", 
                EVENT_RULE: "rule"
            })

        with self.assertRaises(KeyError):
            valid_watchdog_event({
                EVENT_TYPE: "anything", 
                EVENT_PATH: "path", 
                EVENT_RULE: "rule",
                "a": 1
            })

        with self.assertRaises(KeyError):
            valid_event({EVENT_TYPE: "test"})

        with self.assertRaises(KeyError):
            valid_event({"EVENT_TYPE": "test"})

        with self.assertRaises(KeyError):
            valid_event({})

    # Test check_callable 
    def testCheckCallable(self)->None:
        check_callable(make_dir)
        
        with self.assertRaises(TypeError):
            check_callable("a")
