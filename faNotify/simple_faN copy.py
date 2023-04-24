import select
import os
import pyfanotify as fan

if __name__ == '__main__':
    fanot = fan.Fanotify(init_fid=True)
    path = '/mnt/test'
    fanot.mark(path, ev_types=fan.FAN_CREATE | fan.FAN_MOVED_FROM | fan.FAN_ONDIR |fan.FAN_MODIFY, is_type='mt')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern=path+'/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)
    id = 0
    try:
        while poll.poll():
            x = {}
            for i in cli.get_events():
                i.ev_types = fan.evt_to_str(i.ev_types)
                id = id +1 
                x.setdefault(i.path, [i.pid, i.ev_types, id])
            if x:
                print(x)
    except:
        print('STOP')

    cli.close()
    fanot.stop()