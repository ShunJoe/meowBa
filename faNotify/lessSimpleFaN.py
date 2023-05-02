import select
import os
import pyfanotify as fan
import subprocess
import sys
import time

if __name__ == '__main__':
    fanot = fan.Fanotify(init_fid=True)
    path = os.path.abspath('.')
    fanot.mark(path, ev_types=fan.FAN_CREATE | fan.FAN_MOVED_FROM | fan.FAN_ONDIR | fan.FAN_MODIFY, is_type='fs')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern=path+'/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)
    id = 0

    try:
        # Run the Python script specified as an argument
        script_path = sys.argv[1]
        subprocess.run(['python3', script_path])

        # Wait for events or timeout after 30 seconds
        while True:
            ready = poll.poll(30000)
            if not ready:
                print('No events received for 30 seconds, stopping program')
                break

            x = {}
            for i in cli.get_events():
                i.ev_types = fan.evt_to_str(i.ev_types)
                id += 1 
                x.setdefault(i.path, [i.pid, i.ev_types, id])
            if x:
                print(x)

    except KeyboardInterrupt:
        pass

    cli.close()
    fanot.stop()
