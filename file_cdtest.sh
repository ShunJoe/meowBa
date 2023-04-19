#! /bin/bash
j=10000
for ((i = 1; i <= j; i++)) do (
	mkdir "dir${i}"
	> "file${i}"
	sleep 1
	rmdir "dir${i}"
	rm "file${i}"
)
done
