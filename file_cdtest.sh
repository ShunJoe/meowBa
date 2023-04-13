#! /bin/bash
j=4
for ((i = 1; i <= j; i++)) do (
	mkdir "dir${i}" & mkdir "dir${i}${j}"
	> "file${i}" & > "file${i}${j}"
	sleep 1 & sleep 1
	rmdir "dir${i}" & rmdir "dir${i}${j}"
	rm "file${i}" & rm "file${i}${j}"
)
wait
done
