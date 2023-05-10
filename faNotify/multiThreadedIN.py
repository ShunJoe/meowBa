import os
import subprocess
import sys
import threading
import inotify.adapters

def process_events(cli):
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        print("Path: {}, File: {}, Event types: {}".format(path, filename, type_names))

if __name__ == '__main__':
    i = inotify.adapters.Inotify()

    path = os.path.abspath('.')
    i.add_watch(path, mask=(inotify.constants.IN_CREATE |
                        inotify.constants.IN_DELETE |
                        inotify.constants.IN_DELETE_SELF |
                        inotify.constants.IN_MOVED_FROM |
                        inotify.constants.IN_MOVED_TO |
                        inotify.constants.IN_ISDIR))
    # Start the event processing thread
    t = threading.Thread(target=process_events, args=(i,))
    t.daemon = True
    t.start()

    try:
        # Run the Python script specified as an argument
        
        if len(sys.argv) < 2:
            print("Usage: python3 <script_name.py> [script.py | script.sh]")
            sys.exit(1)

        script_path = sys.argv[1]
        if script_path.endswith('.py'):
            subprocess.run(['python3', script_path])
        elif script_path.endswith('.sh'):
            subprocess.run(['bash', script_path])
        else:
            print("Invalid script file. Only .py and .sh files are supported.")
            sys.exit(1)
        
        # script_path = sys.argv[1]
        # subprocess.run(['python3', script_path])

    except KeyboardInterrupt:
        pass

    i.remove_watch(path)
