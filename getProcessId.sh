#! /usr/bin/bash 

truncate -s 0  proc_id.txt
ps -ef | grep "$1"  >> proc_id.txt

#check success of operation
is_done='echo $?'

#if [$is_done -eq 0]
#then 
echo "Process id recovered"
#elif [$is_done -gt 0]
#then
#echo "process id procurement failed"
#fi

