#!/bin/bash

# Output file name
output_file="output.txt"

# Check if the output file exists and clear it if necessary
if [ -f "$output_file" ]; then
    > "$output_file"  # Clear the file
fi

# Directory containing the python scripts
directory="./fanotify/"

# Array of intArg values
intArgs=(100 1000 10000 100000 1000000)

# Loop through each python script in the directory
for script in "$directory"/*.py; do
    # Get the script name without the directory path and extension
    script_name=$(basename "$script" .py)
    
    # Run createFiles.py with 5 different values of intArg
    for intArg in "${intArgs[@]}"; do
        python3 "$directory$script_name.py" "../timingTest/fileCdTestGiveArgs.py" "$intArg" >trace.log &
        create_files_pid=$!
        
         wait "$create_files_pid"

        # Run decodeOutput.py and capture the output
        output=$(python3 "fanotifyDecodeOutput.py" "trace.log")
        
        # Save the output to a file
        echo "Script: $script_name" >> "$output_file"
        echo "intArg: $intArg" >> "$output_file"
        echo "$output" >> "$output_file"
        echo "==================" >> "$output_file"
    done
done
