#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <sys/fanotify.h>
#include <libgen.h>
#include <sys/wait.h>

#define EVENT_SIZE  (sizeof (struct fanotify_event_metadata))
#define EVENT_BUF_LEN     (1024 * (EVENT_SIZE + 16))

void* process_events(void *fdp) {
    struct fanotify_event_metadata event[EVENT_BUF_LEN];
    int length, i = 0;
    int fd = *((int*)fdp);

    while(1) {
        i = 0;
        length = read(fd, event, EVENT_BUF_LEN);
        
        if (length < 0) {
            perror ("read");
        }  
        
        while (i < length) {
            struct fanotify_event_metadata *metadata = (struct fanotify_event_metadata *) &event[i];
            printf ("Received event: pid=%u path=%s\n", metadata->pid, metadata->file_name);
            i += EVENT_SIZE;
        }
    }
}

int main(int argc, char *argv[]) {
    int fd, poll_num;
    char buf;
    nfds_t nfds;
    struct pollfd fds[2];

    /* Check Python script is supplied */
    if (argc != 2) {
        fprintf(stderr, "Usage: %s PYTHON_SCRIPT\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char script_dir[1024];
    strncpy(script_dir, argv[1], sizeof(script_dir));
    dirname(script_dir);

    /* Create the file descriptor for accessing the fanotify API */
    fd = fanotify_init(FAN_CLOEXEC | FAN_NONBLOCK, O_RDONLY | O_LARGEFILE);
    if (fd == -1) {
        perror ("fanotify_init");
        exit(EXIT_FAILURE);
    }

    /* Mark the mount for:
       - file and directory events
       - don't follow soft links */
    if (fanotify_mark(fd, FAN_MARK_ADD | FAN_MARK_MOUNT,
                      FAN_CLOSE_WRITE | FAN_EVENT_ON_CHILD, AT_FDCWD,
                      script_dir) == -1) {
        perror ("fanotify_mark");
        exit(EXIT_FAILURE);
    }

    /* Prepare for polling */
    nfds = 1;
    fds[0].fd = fd;
    fds[0].events = POLLIN;

    /* This is the loop to wait for incoming events */
    printf("Listening for events.\n");

    pthread_t thread;
    int rc;
    rc = pthread_create(&thread, NULL, process_events, (void *)&fd);
    if (rc) {
        printf("Error:unable to create thread, %d\n", rc);
        exit(-1);
    }

    /* Execute the Python script */
    pid_t pid = fork();
    if (pid == 0) { // Child process
        execlp("python3", "python3", argv[1], (char*) NULL);
    } else if (pid < 0) { // Fork failed
        printf("Fork failed!\n");
        exit(-1);
    }

    /* Wait for incoming events */
    poll_num = poll(fds, nfds, -1);
    if (poll_num == -1) {
        if (errno == EINTR)     /* Interrupted by a signal */
            continue;           /* Restart poll() */
        
        perror("poll");        /* Unexpected error */
        exit(EXIT_FAILURE);
    }

    int status;
    waitpid(pid, &status, 0); // Wait for Python script to finish

    pthread_cancel(thread);
    pthread_join(thread, NULL);

    printf("Exiting.\n");
    close(fd);
    exit(EXIT_SUCCESS);
}
