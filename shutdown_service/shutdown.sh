#!/bin/bash

echo "waiting" > /var/run/shutdown_signal
while sleep 5; do
  signal=$(cat /shutdown_signal)
  if [ "$signal" == "true" ]; then 
    echo "done" > /shutdown_signal
    shutdown -h now
  fi
done