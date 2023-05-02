import sys
import re

def decode_escaped_string(escaped_string):
    decoded_string = bytes(escaped_string, 'utf-8').decode('unicode_escape')
    return decoded_string

with open(sys.argv[1], 'r') as trace_file:
    for line in trace_file:
        match = re.search(r'"(.*?)"', line)
        if match:
            escaped_string = match.group(1)
            decoded_string = decode_escaped_string(escaped_string)
            line = line.replace(escaped_string, decoded_string)
        print(line.rstrip())