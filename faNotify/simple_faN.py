import select

import pyfanotify as fan


def foo(t):
    print(f'calling `foo` every {t} seconds')


if __name__ == '__main__':
    foo_timeout = 10000
    fanot = fan.Fanotify(fn=foo, fn_args=(foo_timeout,), fn_timeout=foo_timeout)
    fanot.mark('/home', is_type='mp')
    fanot.start()

    cli = fan.FanotifyClient(fanot, path_pattern='/home/ibli/Documents/GitHub/meowBa/*')
    poll = select.poll()
    poll.register(cli.sock.fileno(), select.POLLIN)
    try:
        while poll.poll():
            x = {}
            for i in cli.get_events():
                i.ev_types = fan.evt_to_str(i.ev_types)
                x.setdefault(i.path, []).append(i)
            if x:
                print(x)
    except:
        print('STOP')

    cli.close()
    fanot.stop()