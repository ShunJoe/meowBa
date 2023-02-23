#! /bin/bash

for ((i = 1; i <= 1; i++)) do (
	mkdir "dir${i}"
	#sleep 0.1
	> "file${i}"
	rmdir "dir${i}"
	rm "file${i}"
)
done
