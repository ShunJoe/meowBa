import re
import sys

if len(sys.argv) < 2:
    print("Usage: python count_variations.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

#Sometimes more than one event is caught per line w. fanotify so we find all these instances and insert a new line. 
#Otherwise we have issues with the regex later. 
with open(filename, 'r') as file:
    text = file.read()

updated_text = text.replace(", b'", ", b'\n")

# Use regular expression to find all variations of keyword followed by numbers or keyword<number>copy

#This is hardcoded to count the number of registrered file events when running inotify on 
# the python script 'fileCdTest.py'. That script can be found at testing/timingTest.

#Finding the files created
create_file_pattern = r'file\d+\''
create_file = re.compile(create_file_pattern)
create_file_match = re.findall(create_file, updated_text)
create_file_pattern_copy = r'\'file\d+copy\''
create_file_copy = re.compile(create_file_pattern_copy)
create_file_matches_copy = re.findall(create_file_copy, updated_text)
create_file_matches = create_file_match + create_file_matches_copy


#Finding created directories
create_dir_pattern = r'\'dir\d+\''
create_dir = re.compile(create_dir_pattern)
create_dir_match = re.findall(create_dir, updated_text)
create_dir_pattern_copy = r'\'dir\d+copy\''
create_dir_copy = re.compile(create_dir_pattern_copy)
create_dir_copy_matches = re.findall(create_dir_copy, updated_text)
create_dir_matches = create_dir_match + create_dir_copy_matches

#Printing the result
print(f"There are {len(create_file_matches)} of FILE CREATION \n There are {len(create_dir_matches)} of DIR CREATE in {filename}")
