import select
import os
import pyfanotify as fan

if __name__ == '__main__':
    fanot = fan.Fanotify(init_fid=True)
    path = os.path.abspath('..')
    fanot.mark(path, ev_types=fan.FAN_CREATE | fan.FAN_MOVED_FROM | fan.FAN_ONDIR, is_type='fs')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern=path+'/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)
    try:
        while poll.poll():
            x = {}
            for i in cli.get_events():
                i.ev_types = fan.evt_to_str(i.ev_types)
                x.setdefault(i.path, [i.pid, i.ev_types])
            if x:
                print(x)
    except:
        print('STOP')

    cli.close()
    fanot.stop()