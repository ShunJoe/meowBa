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


# Use regular expression to find all variations of keyword followed by numbers or keyword<number>copy

#This is hardcoded to count the number of registrered file events when running inotify on 
# the python script 'fileCdTest.py'. That script can be found at testing/timingTest.

#Finding the files created
create_file_pattern = r'FAN_CREATE \('
create_file = re.compile(create_file_pattern)
create_file_matches = re.findall(create_file, text)
#create_file_pattern_copy = r'CREATE.*\'Filecopy\d+\''
#create_file_copy = re.compile(create_file_pattern_copy)
#create_file_matches_copy = re.findall(create_file_copy, updated_text)
#create_file_matches = create_file_match + create_file_matches_copy


#Finding created directories
create_dir_pattern = r'FAN_CREATE\s\|\sFAN_ONDIR \('
create_dir = re.compile(create_dir_pattern)
create_dir_matches = re.findall(create_dir, text)
#create_dir_pattern_copy = r'CREATE.*\'copydir\d+\''
#create_dir_copy = re.compile(create_dir_pattern_copy)
#create_dir_copy_matches = re.findall(create_dir_copy, updated_text)
#create_dir_matches = create_dir_match + create_dir_copy_matches

#Finding the files deleted
del_file_pattern = r'FAN_DELETE \('
del_file = re.compile(del_file_pattern)
del_file_matches= re.findall(del_file, text)
#del_file_pattern_copy =  r'DELETE.*\'filecopy\d+\''
#del_file_copy = re.compile(del_file_pattern_copy)
#del_file_matches_copy = re.findall(del_file_copy, updated_text)
#del_file_matches = del_file_matches_copy + del_file_match

##Finding deleted directories
rm_dir_pattern = r'FAN_DELETE\s\|\sFAN_ONDIR \('
rm_dir = re.compile(rm_dir_pattern)
rm_dir_matches = re.findall(rm_dir, text)
#rm_dir_pattern_copy = r'DELETE.*\'copydir\d+\''
#rm_dir_copy = re.compile(rm_dir_pattern_copy)
#rm_dir_copy_matches = re.findall(rm_dir_copy, updated_text)
#rm_dir_matches = rm_dir_match + rm_dir_copy_matches

#Printing the result
print(f"There are {len(create_file_matches)} of FILE CREATION and {len(del_file_matches)} of FILE DELETE. \n There are {len(create_dir_matches)} of DIR CREATE and {len(rm_dir_matches)} of DIR RM in {filename}")
