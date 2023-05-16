import subprocess

def run_strace(command):
    strace_command = ["strace", "-e", "trace=file", "-f", "-o", "strace.log", "python3"]
    strace_command.extend(command.split())
    process = subprocess.Popen(strace_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"strace failed with error: {stderr.decode()}")
    else:
        print(f"strace completed successfully. Check strace.log for the output.")

run_strace("../test_1mil/fileCdTest.py")