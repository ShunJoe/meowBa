"""
This file contains functions for reading and writing different types of files.

Author(s): David Marchant
"""

import json
import yaml

from os import makedirs, remove, rmdir, walk
from os.path import exists, isfile, join
from typing import Any, Dict, List

from core.correctness.validation import valid_path


def make_dir(path:str, can_exist:bool=True, ensure_clean:bool=False):
    """
    Creates a new directory at the given path.

    :param path: (str) The directory path.

    :param can_exist: (boolean) [optional] A toggle for if a previously
    existing directory at the path will throw an error or not. Default is
    true (e.g. no error is thrown if the path already exists)

    :param ensure_clean: (boolean) [optional] A toggle for if a previously
    existing directory at the path will be replaced with a new emtpy directory.
    Default is False.

    :return: No return
    """
    if exists(path):
        if isfile(path):
            raise ValueError(
                f"Cannot make directory in {path} as it already exists and is "
                "a file")
        if ensure_clean:
            rmtree(path)
                
    makedirs(path, exist_ok=can_exist)

def rmtree(directory:str):
    """
    Remove a directory and all its contents. 
    Should be faster than shutil.rmtree
    
    :param: (str) The firectory to empty and remove

    :return: No return
    """
    if not exists(directory):
        return
    for root, dirs, files in walk(directory, topdown=False):
        for file in files:
            remove(join(root, file))
        for dir in dirs:
            rmtree(join(root, dir))
    rmdir(directory)

def read_file(filepath:str):
    with open(filepath, 'r') as file:
        return file.read()

def read_file_lines(filepath:str):
    with open(filepath, 'r') as file:
        return file.readlines()

def write_file(source:str, filename:str):
    with open(filename, 'w') as file:
        file.write(source)

def read_yaml(filepath:str):
    """
    Reads a file path as a yaml object.

    :param filepath: (str) The file to read.

    :return: (object) An object read from the file.
    """
    with open(filepath, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.Loader)

def write_yaml(source:Any, filename:str):
    """
    Writes a given objcet to a yaml file.

    :param source: (any) A python object to be written.

    :param filename: (str) The filename to be written to.

    :return: No return
    """
    with open(filename, 'w') as param_file:
        yaml.dump(source, param_file, default_flow_style=False)

def read_notebook(filepath:str):
    valid_path(filepath, extension="ipynb")
    with open(filepath, 'r') as read_file:
        return json.load(read_file)

def write_notebook(source:Dict[str,Any], filename:str):
    """
    Writes the given notebook source code to a given filename.

    :param source: (dict) The notebook source dictionary.

    :param filename: (str) The filename to write to.

    :return: No return
    """
    with open(filename, 'w') as job_file:
        json.dump(source, job_file)

def lines_to_string(lines:List[str])->str:
    """Function to convert a list of str lines, into one continuous string 
    separated by newline characters"""
    return "\n".join(lines)
