#all of this from: https://towardsdatascience.com/implementing-a-file-watcher-in-python-73f8356a425d
from os import listdir 
from os.path import isfile, join 
import time

#Function that returns files in a specifik directory
def fileInDirectory(my_dir: str):
        onlyfiles = [f for f in listdir(my_dir) if isfile(join(my_dir, f))]
        return(onlyfiles)

#function comparing two lists
def listComparison(OriginalList: list, NewList: list):
    differencesList = [x for x in NewList if x not in OriginalList] #Note if files get deleted, this will not highlight them
    return(differencesList)

def fileWatcher(my_dir: str, pollTime: int):
    while True:
        if 'watching' not in locals(): #Check if this is the first time the function has run
            previousFileList = fileInDirectory(my_dir)
            watching = 1
            print('First Time')
            print(previousFileList)
        
        time.sleep(pollTime)
        
        newFileList = fileInDirectory(my_dir)
        
        fileDiff = listComparison(previousFileList, newFileList)
        
        previousFileList = newFileList
        if len(fileDiff) == 0: continue
        print(fileDiff)

fileWatcher("./", 1)