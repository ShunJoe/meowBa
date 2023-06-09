import os
import subprocess
import sys
import threading
import inotify.adapters

def process_events(i):
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        print("Path: {}, File: {}, Event types: {}".format(path, filename, type_names))

def run_command(args):
    if args[0] == "pytest":
        cmd = ['pytest'] + args[1:]
    elif args[0].endswith('.py'):
        cmd = ['python3'] + args
    elif args[0].endswith('.sh'):
        cmd = ['bash'] + args
    else:
        print("Invalid command. Only pytest, .py, and .sh are supported.")
        sys.exit(1)

    if '>' in args:
        index = args.index('>')
        cmd = cmd[:index]

    subprocess.run(cmd)

if __name__ == '__main__':
    i = inotify.adapters.Inotify()

    path = os.path.abspath('.')
    i.add_watch(path, mask=inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_FROM | inotify.constants.IN_ISDIR | inotify.constants.IN_MODIFY | inotify.constants.IN_DELETE)

    # Start the event processing thread
    t = threading.Thread(target=process_events, args=(i,))
    t.daemon = True
    t.start()

    try:
        # Run the command specified as arguments
        if len(sys.argv) < 2:
            print("Usage: python3 <script_name.py> [pytest [-k TEST_NAME] [test_file.py] | script.py | script.sh] ")
            sys.exit(1)

        command_args = sys.argv[1:]
        run_command(command_args)

    except KeyboardInterrupt:
        pass

    i.remove_watch(path)
    
