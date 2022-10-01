#!/bin/bash

touch /shutdown_signal

cp ./shutdown_service/shutdown.sh /shutdown.sh
cp ./shutdown_service/shutdown.service /etc/systemd/system/shutdown.service
chmod 766 /shutdown.sh
chmod 666 /shutdown_signal

systemctl start shutdown
systemctl enable shutdown