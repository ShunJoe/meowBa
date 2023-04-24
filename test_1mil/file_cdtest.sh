j=10

seq 1 $j | parallel -j 4 '
    i={}
    mkdir "dir${i}" "dir${i}copy"
    touch "file${i}" "file${i}copy"
    rm "file${i}" "file${i}copy"
    rmdir "dir${i}" "dir${i}copy"
'
