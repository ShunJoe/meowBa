import os
import threading
#import _thread as thread

def file_events (froom, to):
    parent_dir = os.getcwd()
    for i in range(froom,to):
        dir = "dir" + str(i)
        path = os.path.join(parent_dir,dir)
        #make dir
        try: 
            os.mkdir(path)
        except OSError:
            print("mkdir failure: " + path)


        #make file
        try:
            f = open("file" + str(i), "x")
        except OSError:
            print("makefile failure:  file" + str(i))

        #rm file
        path1 = os.path.join(parent_dir, "file" + str(i))
        try:
            os.remove(path1)
        except OSError: 
            print("remove file failed: file" + str(i))

        #rm dir
        try: 
            os.removedirs(path)
        except: 
            print("failed to remove dir: dir" + str(i))

if __name__ == "__main__":
    try:
        t1 = threading.Thread(target=file_events, args=(0,100))
        t2 = threading.Thread(target=file_events, args=(100,200))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except:
        print("Error: Unable to start thread")
