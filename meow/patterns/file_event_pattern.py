
"""
This file contains definitions for a MEOW pattern based off of file events, 
along with an appropriate monitor for said events.

Author(s): David Marchant
"""
import glob
import threading
import sys
import os

from copy import deepcopy
from fnmatch import translate
from re import match
from time import time, sleep
from typing import Any, Union, Dict, List
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from meow_base.core.base_recipe import BaseRecipe
from meow_base.core.base_monitor import BaseMonitor
from meow_base.core.base_pattern import BasePattern
from meow_base.core.rule import Rule
from meow_base.functionality.validation import check_type, valid_string, \
    valid_dict, valid_list, valid_dir_path
from meow_base.core.vars import VALID_RECIPE_NAME_CHARS, \
    VALID_VARIABLE_NAME_CHARS, FILE_EVENTS, FILE_CREATE_EVENT, \
    FILE_MODIFY_EVENT, FILE_MOVED_EVENT, DEBUG_INFO, DIR_EVENTS, \
    FILE_RETROACTIVE_EVENT, SHA256, VALID_PATH_CHARS, FILE_CLOSED_EVENT, \
    DIR_RETROACTIVE_EVENT
from meow_base.functionality.debug import setup_debugging, print_debug
from meow_base.functionality.hashing import get_hash
from meow_base.functionality.meow import create_rule, create_watchdog_event

# Events that are monitored by default
_DEFAULT_MASK = [
    FILE_CREATE_EVENT,
    FILE_MODIFY_EVENT,
    FILE_MOVED_EVENT,
    FILE_RETROACTIVE_EVENT,
    FILE_CLOSED_EVENT
]

class FileEventPattern(BasePattern):
    # The path at which events will trigger this pattern
    triggering_path:str
    # The variable name given to the triggering file within recipe code
    triggering_file:str
    # Which types of event the pattern responds to
    event_mask:List[str]
    def __init__(self, name:str, triggering_path:str, recipe:str, 
            triggering_file:str, event_mask:List[str]=_DEFAULT_MASK, 
            parameters:Dict[str,Any]={}, outputs:Dict[str,Any]={}, 
            sweep:Dict[str,Any]={}):
        """FileEventPattern Constructor. This is used to match against file 
        system events, as caught by the python watchdog module."""
        super().__init__(name, recipe, parameters, outputs, sweep)
        self._is_valid_triggering_path(triggering_path)
        self.triggering_path = triggering_path
        self._is_valid_triggering_file(triggering_file)
        self.triggering_file = triggering_file
        self._is_valid_event_mask(event_mask)
        self.event_mask = event_mask

    def _is_valid_triggering_path(self, triggering_path:str)->None:
        """Validation check for 'triggering_path' variable from main 
        constructor."""
        valid_string(
            triggering_path, 
            VALID_PATH_CHARS+'*', 
            min_length=1, 
            hint="FileEventPattern.triggering_path"
        )
        if len(triggering_path) < 1:
            raise ValueError (
                f"triggiering path '{triggering_path}' is too short. " 
                "Minimum length is 1"
        )

    def _is_valid_triggering_file(self, triggering_file:str)->None:
        """Validation check for 'triggering_file' variable from main 
        constructor."""
        valid_string(
            triggering_file, 
            VALID_VARIABLE_NAME_CHARS,
            hint="FileEventPattern.triggering_file"
        )

    def _is_valid_recipe(self, recipe:str)->None:
        """Validation check for 'recipe' variable from main constructor. 
        Called within parent BasePattern constructor."""
        valid_string(
            recipe, 
            VALID_RECIPE_NAME_CHARS,
            hint="FileEventPattern.recipe"
        )

    def _is_valid_parameters(self, parameters:Dict[str,Any])->None:
        """Validation check for 'parameters' variable from main constructor. 
        Called within parent BasePattern constructor."""
        valid_dict(
            parameters, 
            str, 
            Any, 
            strict=False, 
            min_length=0, 
            hint="FileEventPattern.parameters"
        )
        for k in parameters.keys():
            valid_string(
                k, 
                VALID_VARIABLE_NAME_CHARS,
                hint=f"FileEventPattern.parameters[{k}]"
            )

    def _is_valid_output(self, outputs:Dict[str,str])->None:
        """Validation check for 'output' variable from main constructor. 
        Called within parent BasePattern constructor."""
        valid_dict(
            outputs, 
            str, 
            str, 
            strict=False, 
            min_length=0,
            hint="FileEventPattern.outputs"
        )
        for k in outputs.keys():
            valid_string(
                k, 
                VALID_VARIABLE_NAME_CHARS,
                hint=f"FileEventPattern.outputs[{k}]"
            )

    def _is_valid_event_mask(self, event_mask)->None:
        """Validation check for 'event_mask' variable from main constructor."""
        valid_list(
            event_mask, 
            str, 
            min_length=1, 
            hint="FileEventPattern.event_mask"
        )
        for mask in event_mask:
            if mask not in FILE_EVENTS + DIR_EVENTS:
                raise ValueError(f"Invalid event mask '{mask}'. Valid are: "
                    f"{FILE_EVENTS + DIR_EVENTS}")

    def _is_valid_sweep(self, sweep: Dict[str,Union[int,float,complex]]) -> None:
        """Validation check for 'sweep' variable from main constructor."""
        return super()._is_valid_sweep(sweep)


class WatchdogMonitor(BaseMonitor):
    # A handler object, to catch events
    event_handler:PatternMatchingEventHandler
    # The watchdog observer object
    monitor:Observer
    # The base monitored directory
    base_dir:str
    # Config option, above which debug messages are ignored
    debug_level:int
    # Where print messages are sent
    _print_target:Any
    #A lock to solve race conditions on '_patterns'
    _patterns_lock:threading.Lock
    #A lock to solve race conditions on '_recipes'
    _recipes_lock:threading.Lock
    #A lock to solve race conditions on '_rules'
    _rules_lock:threading.Lock

    def __init__(self, base_dir:str, patterns:Dict[str,FileEventPattern], 
            recipes:Dict[str,BaseRecipe], autostart=False, settletime:int=1, 
            name:str="", print:Any=sys.stdout, logging:int=0)->None:
        """WatchdogEventHandler Constructor. This uses the watchdog module to 
        monitor a directory and all its sub-directories. Watchdog will provide 
        the monitor with an caught events, with the monitor comparing them 
        against its rules, and informing the runner of match."""
        super().__init__(patterns, recipes, name=name)
        self._is_valid_base_dir(base_dir)
        self.base_dir = base_dir
        check_type(settletime, int, hint="WatchdogMonitor.settletime")
        self._print_target, self.debug_level = setup_debugging(print, logging)       
        self._patterns_lock = threading.Lock()
        self._recipes_lock = threading.Lock()
        self._rules_lock = threading.Lock()
        self.event_handler = WatchdogEventHandler(self, settletime=settletime)
        self.monitor = Observer()
        self.monitor.schedule(
            self.event_handler,
            self.base_dir,
            recursive=True
        )
        print_debug(self._print_target, self.debug_level, 
            "Created new WatchdogMonitor instance", DEBUG_INFO)

        if autostart:
            self.start()

    def start(self)->None:
        """Function to start the monitor."""
        print_debug(self._print_target, self.debug_level, 
            "Starting WatchdogMonitor", DEBUG_INFO)
        self._apply_retroactive_rules()
        self.monitor.start()

    def stop(self)->None:
        """Function to stop the monitor."""
        print_debug(self._print_target, self.debug_level, 
            "Stopping WatchdogMonitor", DEBUG_INFO)
        self.monitor.stop()

    def match(self, event)->None:
        """Function to determine if a given event matches the current rules."""
        src_path = event.src_path

        prepend = "dir_" if event.is_directory else "file_" 
        event_types = [prepend+i for i in event.event_type]

        # Remove the base dir from the path as trigger paths are given relative
        # to that
        handle_path = src_path.replace(self.base_dir, '', 1)
        # Also remove leading slashes, so we don't go off of the root directory
        while handle_path.startswith(os.path.sep):
            handle_path = handle_path[1:]

        self._rules_lock.acquire()
        try:
            for rule in self._rules.values():
                
                # Skip events not within the event mask
                if any(i in event_types for i in rule.pattern.event_mask) \
                        != True:
                    continue
                                
                # Use regex to match event paths against rule paths
                target_path = rule.pattern.triggering_path
                recursive_regexp = translate(target_path)
                if os.name == 'nt':
                    direct_regexp = recursive_regexp.replace(
                        '.*', '[^'+ os.path.sep + os.path.sep +']*')
                else:
                    direct_regexp = recursive_regexp.replace(
                        '.*', '[^'+ os.path.sep +']*')
                recursive_hit = match(recursive_regexp, handle_path)
                direct_hit = match(direct_regexp, handle_path)

                # If matched, the create a watchdog event
                if direct_hit or recursive_hit:
                    meow_event = create_watchdog_event(
                        event.src_path,
                        rule,
                        self.base_dir,
                        get_hash(event.src_path, SHA256) 
                    )
                    print_debug(self._print_target, self.debug_level,  
                        f"Event at {src_path} hit rule {rule.name}", 
                        DEBUG_INFO)
                    # Send the event to the runner
                    self.to_runner.send(meow_event)

        except Exception as e:
            self._rules_lock.release()
            raise e

        self._rules_lock.release()

    def add_pattern(self, pattern:FileEventPattern)->None:
        """Function to add a pattern to the current definitions. Any rules 
        that can be possibly created from that pattern will be automatically 
        created."""
        check_type(pattern, FileEventPattern, hint="add_pattern.pattern")
        self._patterns_lock.acquire()
        try:
            if pattern.name in self._patterns:
                raise KeyError(f"An entry for Pattern '{pattern.name}' "
                    "already exists. Do you intend to update instead?")
            self._patterns[pattern.name] = pattern
        except Exception as e:
            self._patterns_lock.release()
            raise e            
        self._patterns_lock.release()

        self._identify_new_rules(new_pattern=pattern)

    def update_pattern(self, pattern:FileEventPattern)->None:
        """Function to update a pattern in the current definitions. Any rules 
        created from that pattern will be automatically updated."""
        check_type(pattern, FileEventPattern, hint="update_pattern.pattern")
        self.remove_pattern(pattern.name)
        self.add_pattern(pattern)

    def remove_pattern(self, pattern: Union[str,FileEventPattern])->None:
        """Function to remove a pattern from the current definitions. Any rules 
        that will be no longer valid will be automatically removed."""
        check_type(
            pattern, 
            str, 
            alt_types=[FileEventPattern], 
            hint="remove_pattern.pattern"
        )
        lookup_key = pattern
        if isinstance(lookup_key, FileEventPattern):
            lookup_key = pattern.name
        self._patterns_lock.acquire()
        try:
            if lookup_key not in self._patterns:
                raise KeyError(f"Cannot remote Pattern '{lookup_key}' as it "
                    "does not already exist")
            self._patterns.pop(lookup_key)
        except Exception as e:
            self._patterns_lock.release()
            raise e 
        self._patterns_lock.release()

        if isinstance(pattern, FileEventPattern):
            self._identify_lost_rules(lost_pattern=pattern.name)
        else:
            self._identify_lost_rules(lost_pattern=pattern)
        
    def get_patterns(self)->Dict[str,FileEventPattern]:
        """Function to get a dict of the currently defined patterns of the 
        monitor. Note that the result is deep-copied, and so can be manipulated
        without directly manipulating the internals of the monitor."""
        to_return = {}
        self._patterns_lock.acquire()
        try:
            to_return = deepcopy(self._patterns)
        except Exception as e:
            self._patterns_lock.release()
            raise e
        self._patterns_lock.release()
        return to_return

    def add_recipe(self, recipe: BaseRecipe)->None:
        """Function to add a recipe to the current definitions. Any rules 
        that can be possibly created from that recipe will be automatically 
        created."""
        check_type(recipe, BaseRecipe, hint="add_recipe.recipe")
        self._recipes_lock.acquire()
        try:
            if recipe.name in self._recipes:
                raise KeyError(f"An entry for Recipe '{recipe.name}' already "
                    "exists. Do you intend to update instead?")
            self._recipes[recipe.name] = recipe
        except Exception as e:
            self._recipes_lock.release()
            raise e
        self._recipes_lock.release()

        self._identify_new_rules(new_recipe=recipe)

    def update_recipe(self, recipe: BaseRecipe)->None:
        """Function to update a recipe in the current definitions. Any rules 
        created from that recipe will be automatically updated."""
        check_type(recipe, BaseRecipe, hint="update_recipe.recipe")
        self.remove_recipe(recipe.name)
        self.add_recipe(recipe)
    
    def remove_recipe(self, recipe:Union[str,BaseRecipe])->None:
        """Function to remove a recipe from the current definitions. Any rules 
        that will be no longer valid will be automatically removed."""
        check_type(
            recipe, 
            str, 
            alt_types=[BaseRecipe], 
            hint="remove_recipe.recipe"
        )
        lookup_key = recipe
        if isinstance(lookup_key, BaseRecipe):
            lookup_key = recipe.name
        self._recipes_lock.acquire()
        try:
            # Check that recipe has not already been deleted
            if lookup_key not in self._recipes:
                raise KeyError(f"Cannot remote Recipe '{lookup_key}' as it "
                    "does not already exist")
            self._recipes.pop(lookup_key)
        except Exception as e:
            self._recipes_lock.release()
            raise e
        self._recipes_lock.release()

        if isinstance(recipe, BaseRecipe):
            self._identify_lost_rules(lost_recipe=recipe.name)
        else:
            self._identify_lost_rules(lost_recipe=recipe)

    def get_recipes(self)->Dict[str,BaseRecipe]:
        """Function to get a dict of the currently defined recipes of the 
        monitor. Note that the result is deep-copied, and so can be manipulated
        without directly manipulating the internals of the monitor."""
        to_return = {}
        self._recipes_lock.acquire()
        try:
            to_return = deepcopy(self._recipes)
        except Exception as e:
            self._recipes_lock.release()
            raise e
        self._recipes_lock.release()
        return to_return
    
    def get_rules(self)->Dict[str,Rule]:
        """Function to get a dict of the currently defined rules of the 
        monitor. Note that the result is deep-copied, and so can be manipulated
        without directly manipulating the internals of the monitor."""
        to_return = {}
        self._rules_lock.acquire()
        try:
            to_return = deepcopy(self._rules)
        except Exception as e:
            self._rules_lock.release()
            raise e
        self._rules_lock.release()
        return to_return

    def _identify_new_rules(self, new_pattern:FileEventPattern=None, 
            new_recipe:BaseRecipe=None)->None:
        """Function to determine if a new rule can be created given a new 
        pattern or recipe, in light of other existing patterns or recipes in 
        the monitor."""

        if new_pattern:
            self._patterns_lock.acquire()
            self._recipes_lock.acquire()
            try:
                # Check in case pattern has been deleted since function called
                if new_pattern.name not in self._patterns:
                    self._patterns_lock.release()
                    self._recipes_lock.release()
                    return
                # If pattern specifies recipe that already exists, make a rule
                if new_pattern.recipe in self._recipes:
                    self._create_new_rule(
                        new_pattern,
                        self._recipes[new_pattern.recipe],
                    )
            except Exception as e:
                self._patterns_lock.release()
                self._recipes_lock.release()
                raise e
            self._patterns_lock.release()
            self._recipes_lock.release()

        if new_recipe:
            self._patterns_lock.acquire()
            self._recipes_lock.acquire()
            try:
                # Check in case recipe has been deleted since function called
                if new_recipe.name not in self._recipes:
                    self._patterns_lock.release()
                    self._recipes_lock.release()
                    return
                # If recipe is specified by existing pattern, make a rule
                for pattern in self._patterns.values():
                    if pattern.recipe == new_recipe.name:
                        self._create_new_rule(
                            pattern,
                            new_recipe,
                        )
            except Exception as e:
                self._patterns_lock.release()
                self._recipes_lock.release()
                raise e
            self._patterns_lock.release()
            self._recipes_lock.release()

    def _identify_lost_rules(self, lost_pattern:str=None, 
            lost_recipe:str=None)->None:
        """Function to remove rules that should be deleted in response to a 
        pattern or recipe having been deleted."""
        to_delete = []
        self._rules_lock.acquire()
        try:
            # Identify any offending rules
            for name, rule in self._rules.items():
                if lost_pattern and rule.pattern.name == lost_pattern:
                    to_delete.append(name)
                if lost_recipe and rule.recipe.name == lost_recipe:
                    to_delete.append(name)
            # Now delete them
            for delete in to_delete:
                if delete in self._rules.keys():
                    self._rules.pop(delete)
        except Exception as e:
            self._rules_lock.release()
            raise e
        self._rules_lock.release()

    def _create_new_rule(self, pattern:FileEventPattern, 
            recipe:BaseRecipe)->None:
        """Function to create a new rule from a given pattern and recipe. This 
        will only be called to create rules at runtime, as rules are 
        automatically created at initialisation using the  same 'create_rule' 
        function called here."""
        rule = create_rule(pattern, recipe)
        self._rules_lock.acquire()
        try:
            if rule.name in self._rules:
                raise KeyError("Cannot create Rule with name of "
                    f"'{rule.name}' as already in use")
            self._rules[rule.name] = rule
        except Exception as e:
            self._rules_lock.release()
            raise e
        self._rules_lock.release()

        self._apply_retroactive_rule(rule)
        
    def _is_valid_base_dir(self, base_dir:str)->None:
        """Validation check for 'base_dir' variable from main constructor. Is 
        automatically called during initialisation."""
        valid_dir_path(base_dir, must_exist=True)

    def _is_valid_patterns(self, patterns:Dict[str,FileEventPattern])->None:
        """Validation check for 'patterns' variable from main constructor. Is 
        automatically called during initialisation."""
        valid_dict(patterns, str, FileEventPattern, min_length=0, strict=False)

    def _is_valid_recipes(self, recipes:Dict[str,BaseRecipe])->None:
        """Validation check for 'recipes' variable from main constructor. Is 
        automatically called during initialisation."""
        valid_dict(recipes, str, BaseRecipe, min_length=0, strict=False)

    def _apply_retroactive_rules(self)->None:
        """Function to determine if any rules should be applied to the existing 
        file structure, were the file structure created/modified now."""
        for rule in self._rules.values():
            self._apply_retroactive_rule(rule)

    def _apply_retroactive_rule(self, rule:Rule)->None:
        """Function to determine if a rule should be applied to the existing 
        file structure, were the file structure created/modified now."""
        self._rules_lock.acquire()
        try:
            # Check incase rule deleted since this function first called
            if rule.name not in self._rules:
                self._rules_lock.release()
                return

            if FILE_RETROACTIVE_EVENT in rule.pattern.event_mask \
                    or DIR_RETROACTIVE_EVENT in rule.pattern.event_mask:
                # Determine what paths are potentially triggerable and gather
                # files at those paths
                testing_path = os.path.join(
                    self.base_dir, rule.pattern.triggering_path)

                globbed = glob.glob(testing_path)

                # For each file create a fake event.
                for globble in globbed:

                    meow_event = create_watchdog_event(
                        globble,
                        rule,
                        self.base_dir,
                        get_hash(globble, SHA256)
                    )
                    print_debug(self._print_target, self.debug_level,  
                        f"Retroactive event for file at at {globble} hit rule "
                        f"{rule.name}", DEBUG_INFO)
                    # Send it to the runner
                    self.to_runner.send(meow_event)

        except Exception as e:
            self._rules_lock.release()
            raise e
        self._rules_lock.release()


class WatchdogEventHandler(PatternMatchingEventHandler):
    # The monitor class running this handler
    monitor:WatchdogMonitor
    # A time to wait per event path, during which extra events are discared
    _settletime:int
    # TODO clean this struct occasionally
    # A Dict of recent job timestamps
    _recent_jobs:Dict[str, Any]
    # A lock to solve race conditions on '_recent_jobs'
    _recent_jobs_lock:threading.Lock
    def __init__(self, monitor:WatchdogMonitor, settletime:int=1):
        """WatchdogEventHandler Constructor. This inherits from watchdog 
        PatternMatchingEventHandler, and is used to catch events, then filter 
        out excessive events at the same location."""
        super().__init__()
        self.monitor = monitor
        self._settletime = settletime
        self._recent_jobs = {}
        self._recent_jobs_lock = threading.Lock()

    def threaded_handler(self, event):
        """Function to determine if the given event shall be sent on to the 
        monitor. After each event we wait for '_settletime', to catch 
        subsequent events at the same location, so as to not swamp the system 
        with repeated events."""
 
        self._recent_jobs_lock.acquire()
        try:
            if event.src_path in self._recent_jobs: 
                if event.time_stamp > self._recent_jobs[event.src_path][0]:
                    self._recent_jobs[event.src_path][0] = event.time_stamp
                    self._recent_jobs[event.src_path][1].add(event.event_type)
                else:
                    self._recent_jobs_lock.release()
                    return
            else:
                self._recent_jobs[event.src_path] = \
                    [event.time_stamp, {event.event_type}]

            # If we have a closed event then short-cut the wait and send event
            # immediately        
            if event.event_type == FILE_CLOSED_EVENT:
                self.monitor.match(event)
                self._recent_jobs_lock.release()
                return

        except Exception as ex:
            self._recent_jobs_lock.release()
            raise Exception(ex)
        self._recent_jobs_lock.release()

        sleep(self._settletime)

        self._recent_jobs_lock.acquire()
        try:
            if event.src_path in self._recent_jobs \
                    and event.time_stamp < self._recent_jobs[event.src_path][0]:
                self._recent_jobs_lock.release()
                return
        except Exception as ex:
            self._recent_jobs_lock.release()
            raise Exception(ex)
        event.event_type = self._recent_jobs[event.src_path][1]
        self._recent_jobs_lock.release()

        self.monitor.match(event)

    def handle_event(self, event):
        """Handler function, called by all specific event functions. Will 
        attach a timestamp to the event immediately, and attempt to start a 
        threaded_handler so that the monitor can resume monitoring as soon as 
        possible."""
        event.time_stamp = time()

        waiting_for_threaded_resources = True
        while waiting_for_threaded_resources:
            try:
                worker = threading.Thread(
                    target=self.threaded_handler,
                    args=[event])
                worker.daemon = True
                worker.start()
                waiting_for_threaded_resources = False
            except threading.ThreadError:
                sleep(1)
    
    def on_created(self, event):
        """Function called when a file created event occurs."""
        self.handle_event(event)

    def on_modified(self, event):
        """Function called when a file modified event occurs."""
        self.handle_event(event)

    def on_moved(self, event):
        """Function called when a file moved event occurs."""
        self.handle_event(event)

    def on_deleted(self, event):
        """Function called when a file deleted event occurs."""
        self.handle_event(event)
    
    def on_closed(self, event):
        """Function called when a file closed event occurs."""
        self.handle_event(event)
