import re
import sys

if len(sys.argv) < 2:
    print("Usage: python count_variations.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r') as file:
    text = file.read()

# Use regular expression to find all variations of keyword followed by numbers or keyword<number>copy
#pattern = r'\b(file\d+|filecopy\d+|dir\d+|copydir\d+)\b'
#matches = re.findall(pattern, text)

#Finding file creations
create_file_pattern = r'openat\(AT_FDCWD, "file\d+"'
create_file = re.compile(create_file_pattern)
create_file_match = re.findall(create_file, text)
create_file_pattern_copy = r'openat\(AT_FDCWD, "filecopy\d+"'
create_file_copy = re.compile(create_file_pattern_copy)
create_file_matches_copy = re.findall(create_file_copy, text)
create_file_matches = create_file_match + create_file_matches_copy

#Finding file deletion
del_file_pattern = r'unlink\("file\d+"'
del_file = re.compile(del_file_pattern)
del_file_match= re.findall(del_file, text)
del_file_pattern_copy = r'unlink\("filecopy\d+"'
del_file_copy = re.compile(del_file_pattern_copy)
del_file_matches_copy = re.findall(del_file_copy, text)
del_file_matches = del_file_matches_copy + del_file_match

#Finding dir creation
create_dir_pattern = r'mkdir\("dir\d+"'
create_dir = re.compile(create_dir_pattern)
create_dir_match = re.findall(create_dir, text)
create_dir_pattern_copy = r'mkdir\("copydir\d+"'
create_dir_copy = re.compile(create_dir_pattern_copy)
create_dir_copy_matches = re.findall(create_dir_copy, text)
create_dir_matches = create_dir_match + create_dir_copy_matches

#Finding dir deletion
rm_dir_pattern = r'rmdir\("dir\d+"'
rm_dir = re.compile(rm_dir_pattern)
rm_dir_match = re.findall(rm_dir, text)
rm_dir_pattern_copy = r'rmdir\("copydir\d+"'
rm_dir_copy = re.compile(rm_dir_pattern_copy)
rm_dir_copy_matches = re.findall(rm_dir_copy, text)
rm_dir_matches = rm_dir_match + rm_dir_copy_matches

print(f"There are {len(create_file_matches)} of FILE CREATION and {len(del_file_matches)} of FILE DELETE. \n There are {len(create_dir_matches)} of DIR CREATE and {len(rm_dir_matches)} of DIR RM in {filename}")
