#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/fanotify.h>
#include <unistd.h>
#include <pthread.h>
#include<string.h>
#define BUF_SIZE 256

volatile int startBash = 0; 
volatile int bashDone = 0; 

void* fanotifyProcessing(void* argv1) {
    const char* argv11 = (const char*)argv1;
    int fd, ret, event_fd, mount_fd;
    ssize_t len, path_len;
    char path[PATH_MAX];
    char procfd_path[PATH_MAX];
    char events_buf[BUF_SIZE];
    struct file_handle *file_handle;
    struct fanotify_event_metadata *metadata;
    struct fanotify_event_info_fid *fid;
    const char *file_name;
    struct stat sb;
    mount_fd = open(argv11, O_DIRECTORY | O_RDONLY);
    if (mount_fd == -1) {
        perror(argv11);
        exit(EXIT_FAILURE);
    }
    /* Create an fanotify file descriptor with FAN_REPORT_DFID_NAME as
       a flag so that program can receive fid events with directory
       entry name. */
    fd = fanotify_init(FAN_CLASS_NOTIF | FAN_REPORT_DFID_NAME, 0);
    if (fd == -1) {
        perror("fanotify_init");
        exit(EXIT_FAILURE);
    }
    /* Place a mark on the filesystem object supplied in argv[1]. */
    ret = fanotify_mark(fd, FAN_MARK_ADD | FAN_MARK_ONLYDIR,
                        FAN_CREATE | FAN_DELETE| FAN_ONDIR ,
                        AT_FDCWD, argv11);
    if (ret == -1) {
        perror("fanotify_mark");
        exit(EXIT_FAILURE);
    }
 
    printf("Listening for events.\n");
    while(1) {
        startBash = 1;
         /* Read events from the event queue into a buffer. */
        len = read(fd, events_buf, sizeof(events_buf));
        if (len == -1 && errno != EAGAIN) {
            perror("read");
            exit(EXIT_FAILURE);
        }
        /* Process all events within the buffer. */
        for (metadata = (struct fanotify_event_metadata *) events_buf;
                FAN_EVENT_OK(metadata, len);
                metadata = FAN_EVENT_NEXT(metadata, len)) {
            fid = (struct fanotify_event_info_fid *) (metadata + 1);
            file_handle = (struct file_handle *) fid->handle;
            /* Ensure that the event info is of the correct type. */
            if (fid->hdr.info_type == FAN_EVENT_INFO_TYPE_FID ||
                fid->hdr.info_type == FAN_EVENT_INFO_TYPE_DFID) {
                file_name = NULL;
            } else if (fid->hdr.info_type == FAN_EVENT_INFO_TYPE_DFID_NAME) {
                file_name = file_handle->f_handle +
                            file_handle->handle_bytes;
            } else {
                fprintf(stderr, "Received unexpected event info type. ");
                exit(EXIT_FAILURE);
            }
            if (metadata->mask == FAN_CREATE) {
                printf("FAN_CREATE (file created): ");
            }
            if (metadata->mask == (FAN_CREATE | FAN_ONDIR)) {
                printf("FAN_CREATE | FAN_ONDIR (subdirectory created): ");
            }
            if (metadata->mask == FAN_DELETE) {
                printf("FAN_DELETE (file deleted): ");
            }
            if (metadata->mask == (FAN_DELETE | FAN_ONDIR)) {
                printf("FAN_DELETE | FAN_ONDIR (subdirectory deleted) ");
            }
        /* metadata->fd is set to FAN_NOFD when the group identifies
            objects by file handles.  To obtain a file descriptor for
            the file object corresponding to an event you can use the
            struct file_handle that's provided within the
            fanotify_event_info_fid in conjunction with the
            open_by_handle_at(2) system call.  A check for ESTALE is
            done to accommodate for the situation where the file handle
            for the object was deleted prior to this system call. */
            event_fd = open_by_handle_at(mount_fd, file_handle, O_RDONLY);
            if (event_fd == -1) {
                if (errno == ESTALE) {
                    printf("File handle is no longer valid. "
                            "File has been deleted\n");
                    continue;
                } else {
                    perror("open_by_handle_at");
                    exit(EXIT_FAILURE);
                }
            }
            snprintf(procfd_path, sizeof(procfd_path), "/proc/self/fd/%d",
                    event_fd);
            /* Retrieve and print the path of the modified entry. */
            path_len = readlink(procfd_path, path, sizeof(path) - 1);
            if (path_len == -1) {
                perror("readlink");
                exit(EXIT_FAILURE);
            }
            path[path_len] = '\0';
            printf("\tDirectory '%s' has been modified.", path);
            if (file_name) {
                ret = fstatat(event_fd, file_name, &sb, 0);
                if (ret == -1) {
                    if (errno != ENOENT) {
                        perror("fstatat");
                        exit(EXIT_FAILURE);
                    }
                    printf("\tEntry '%s' does not exist.", file_name);
                } else if ((sb.st_mode & S_IFMT) == S_IFDIR) {
                    printf("\tEntry '%s' is a subdirectory.", file_name);
                } else {
                    printf("\tEntry '%s' is not a subdirectory.",
                            file_name);
                }
                
            }
            printf("\n");
            close(metadata->fd);
            close((int)event_fd);
        }
    }
    printf("All events processed successfully. Fanotify process exiting.\n");
    return NULL;
}

int main(int argc, char *argv[]) {
    
    if (argc != 3) {
        fprintf(stderr, "Invalid number of command line arguments.\n Usage <path> <bash script>");
        exit(EXIT_FAILURE);
    }
    

    pthread_t thread;
    const char* dirToWatch = argv[1];  // Path to dir to watch

    
    /*Executing fanotify to give events*/
    if (pthread_create(&thread, NULL, fanotifyProcessing, (void*)dirToWatch) != 0) {
        fprintf(stderr, "Failed to create a new thread.\n");
        exit(EXIT_FAILURE);
    }
   
    /* Execute script when process event thread is ready */  
    while (startBash == 0) {
        sleep(1);
    }
    const char* scriptPath = argv[2];
    const char* scriptType;

    // Extract the file extension from the script path
    const char* extension = strrchr(scriptPath, '.');
    if (extension != NULL) {
        // Skip the dot character
        extension++;
        
        if (strcmp(extension, "sh") == 0) {
            scriptType = "bash";
        } else if (strcmp(extension, "py") == 0) {
            scriptType = "python";
        } else {
            printf("Unsupported script type.\n");
            return EXIT_FAILURE;
        }
    } else {
        printf("Invalid script path.\n");
        return EXIT_FAILURE;
    }

    int exitStatus;

    if (strcmp(scriptType, "bash") == 0) {
        exitStatus = system(scriptPath);
    } else if (strcmp(scriptType, "python") == 0) {
        char command[256];
        snprintf(command, sizeof(command), "python3 %s", scriptPath);
        exitStatus = system(command);
    } else {
        printf("Invalid script type.\n");
        return EXIT_FAILURE;
    }

    if (exitStatus == -1) {
        printf("Failed to execute the script.\n");
        return EXIT_FAILURE;
    }
    sleep(5);
    printf("Terminating program \n");
    exit(EXIT_SUCCESS);
}