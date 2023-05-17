import re
import sys

if len(sys.argv) < 2:
    print("Usage: python count_variations.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r') as file:
    text = file.read()

# Use regular expression to find all variations of keyword followed by numbers or keyword<number>copy

#This is hardcoded to count the number of registrered file events when running inotify on 
# the python script 'fileCdTest.py'. That script can be found at testing/timingTest.

#Finding the files created
create_file_pattern = r'File: file\d+, Event types: \[\'IN_CREATE\'\]'
create_file = re.compile(create_file_pattern)
create_file_match = re.findall(create_file, text)
create_file_pattern_copy = r'File: filecopy\d+, Event types: \[\'IN_CREATE\'\]'
create_file_copy = re.compile(create_file_pattern_copy)
create_file_matches_copy = re.findall(create_file_copy, text)
create_file_matches = create_file_match + create_file_matches_copy

#Finding the files deleted
del_file_pattern = r'File: file\d+, Event types: \[\'IN_DELETE\'\]'
del_file = re.compile(del_file_pattern)
del_file_match= re.findall(del_file, text)
del_file_pattern_copy = r'File: filecopy\d+, Event types: \[\'IN_DELETE\'\]'
del_file_copy = re.compile(del_file_pattern_copy)
del_file_matches_copy = re.findall(del_file_copy, text)
del_file_matches = del_file_matches_copy + del_file_match

#Finding created directories
create_dir_pattern = r'File: dir\d+, Event types: \[\'IN_CREATE\', \'IN_ISDIR\'\]'
create_dir = re.compile(create_dir_pattern)
create_dir_match = re.findall(create_dir, text)
create_dir_pattern_copy = r'File: copydir\d+, Event types: \[\'IN_CREATE\', \'IN_ISDIR\'\]'
create_dir_copy = re.compile(create_dir_pattern_copy)
create_dir_copy_matches = re.findall(create_dir_copy, text)
create_dir_matches = create_dir_match + create_dir_copy_matches

#Finding deleted directories
rm_dir_pattern = r'File: dir\d+, Event types: \[\'IN_DELETE\', \'IN_ISDIR\'\]'
rm_dir = re.compile(rm_dir_pattern)
rm_dir_match = re.findall(rm_dir, text)
rm_dir_pattern_copy = r'File: dir\d+, Event types: \[\'IN_DELETE\', \'IN_ISDIR\'\]'
rm_dir_copy = re.compile(rm_dir_pattern_copy)
rm_dir_copy_matches = re.findall(rm_dir_copy, text)
rm_dir_matches = rm_dir_match + rm_dir_copy_matches

#Printing the result
print(f"There are {len(create_file_matches)} of FILE CREATION and {len(del_file_matches)} of FILE DELETE. \n There are {len(create_dir_matches)} of DIR CREATE and {len(rm_dir_matches)} of DIR RM in {filename}")
