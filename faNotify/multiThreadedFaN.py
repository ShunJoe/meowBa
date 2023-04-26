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

if __name__ == '__main__':
    fanot = fan.Fanotify(init_fid=True)
    path = os.path.abspath('.')
    fanot.mark(path, ev_types=fan.FAN_CREATE | fan.FAN_MOVED_FROM | fan.FAN_ONDIR | fan.FAN_MODIFY, is_type='fs')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern=path+'/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)

    # Start the event processing thread
    t = threading.Thread(target=process_events, args=(cli,))
    t.daemon = True
    t.start()

    try:
        # Run the Python script specified as an argument
        script_path = sys.argv[1]
        subprocess.run(['python3', script_path])

    except KeyboardInterrupt:
        pass

    cli.close()
    fanot.stop()
