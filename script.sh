#!/bin/bash

while read line
do
  if [[ $line =~ ^-?[0-9]+$ ]]
  then
    sleep $line
  else
    curl --data-urlencode "group-id=$1" --data-urlencode "msg=$line" 'http://localhost:8000/group-msg'
  fi
done < /dev/stdin

