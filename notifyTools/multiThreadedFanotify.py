import select
import os
import pyfanotify as fan
import subprocess
import sys
import threading

def process_events(cli):
    while True:
        x = {}
        for i in cli.get_events():
            i.ev_types = fan.evt_to_str(i.ev_types)
            x.setdefault(i.path, [i.pid, i.ev_types])
        if x:
            print(x)
        
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

    subprocess.run(cmd)

if __name__ == '__main__':
    fanot = fan.Fanotify(init_fid=True)
    
    #setting the wacthed path to the current directory. 
    path = os.path.abspath('.')
    fanot.mark(path, ev_types=fan.FAN_CREATE | fan.FAN_ONDIR |fan.FAN_DELETE, is_type='fs')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern=path+'/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)

    # Start the event processing thread
    t = threading.Thread(target=process_events, args=(cli,))
    t.daemon = True
    t.start()

    try:
        # Run the command specified as arguments
        if len(sys.argv) < 2:
            print("Usage: python3 <script_name.py> [pytest [-k TEST_NAME] [test_file.py] | script.py | script.sh]")
            sys.exit(1)

        command_args = sys.argv[1:]
        run_command(command_args)

    except KeyboardInterrupt:
        pass

    cli.close()
    fanot.stop()

