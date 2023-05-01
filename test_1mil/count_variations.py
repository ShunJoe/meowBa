import re
import sys

if len(sys.argv) < 2:
    print("Usage: python count_variations.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r') as file:
    text = file.read()

# Use regular expression to find all variations of keyword followed by numbers or keyword<number>copy
pattern = r'\b(file\d+|filecopy\d+|dir\d+|copydir\d+)\b'
matches = re.findall(pattern, text)

del_pattern = r'\b(moved_from)\b'
del_matches = re.findall(del_pattern, text)

create_pattern = r'\b(create)\b'
create_matches = re.findall(create_pattern, text)

# Use set to count the number of unique variations
unique_variations = set(matches)
num_variations = len(unique_variations)


print(f"There are {num_variations} in {filename}. There are {len(del_matches)} of DELETE and {len(create_matches)} of CREATE")
