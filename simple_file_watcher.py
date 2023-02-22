#most of this from: https://towardsdatascience.com/implementing-a-file-watcher-in-python-73f8356a425d
from os import listdir 
from os.path import isfile, join, isdir
import time

#Function that returns files in a specifik directory
def fileInDirectory(my_dir: str):
        filesanddirs = [f for f in listdir(my_dir) if isfile(join(my_dir, f)) or isdir(join(my_dir, f))]
        return(filesanddirs)

#function comparing two lists
def listComparison(OriginalList: list, NewList: list):
    differencesList = ["+" + x for x in NewList if x not in OriginalList]  #Note if files get deleted, this will not highlight them
    removedList = [ "-" + x for x in OriginalList if x not in NewList] #if files get deleted
    return( removedList + differencesList)

def fileWatcher(my_dir: str, pollTime: float):
    try:
        previousFileList = fileInDirectory(my_dir)
        while True:
                      
            #time.sleep(pollTime)
            
            newFileList = fileInDirectory(my_dir)
            
            fileDiff = listComparison(previousFileList, newFileList)
            
            previousFileList = newFileList
            if len(fileDiff) == 0: continue
            print(fileDiff)
    except KeyboardInterrupt:
        print ('interupted!')
            

fileWatcher("./", 0.1)