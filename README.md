# meowBa
This is a repository for the Bachelor's project 'Is it feasible to identify outputs of an arbitrary process at run time without excessively slowing down workflows?'

It is based upon meow_base by David Marchant, hence why the folder meow_base is and exact replica of his repository's stable branch as of June 10th 2023.

/meow_baseFanotify and /meow_baseStrace are forks of meow_base wherein we have implemented tracers using fanotify and strace.

/notifyTools includes two multithreaded notification programs based on respectively inotify and fanotify, meant for timing tests.

/tests includes our testing scripts within timing tests and integrity tests.
