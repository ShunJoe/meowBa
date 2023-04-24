#! /bin/bash
j=100000
for ((i = 1; i <= j; i++)) do (
	mkdir "dir${i}" & mkdir "dir${i}copy"
	> "file${i}" & > "file${i}copy"
	rmdir "dir${i}" & rmdir "dir${i}copy"
	rm "file${i}" & rm "file${i}copy"
)
wait
done