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

#Finding the files created
create_file_pattern = r'FAN_CREATE \('
create_file = re.compile(create_file_pattern)
create_file_matches = re.findall(create_file, text)

#Finding created directories
create_dir_pattern = r'FAN_CREATE\s\|\sFAN_ONDIR \('
create_dir = re.compile(create_dir_pattern)
create_dir_matches = re.findall(create_dir, text)

#Finding the files deleted
del_file_pattern = r'FAN_DELETE \('
del_file = re.compile(del_file_pattern)
del_file_matches= re.findall(del_file, text)

##Finding deleted directories
rm_dir_pattern = r'FAN_DELETE\s\|\sFAN_ONDIR \('
rm_dir = re.compile(rm_dir_pattern)
rm_dir_matches = re.findall(rm_dir, text)

#Printing the result
print(f"There are {len(create_file_matches)} of FILE CREATION and {len(del_file_matches)} of FILE DELETE. \n There are {len(create_dir_matches)} of DIR CREATE and {len(rm_dir_matches)} of DIR RM in {filename}")
