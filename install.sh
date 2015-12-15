#!/bin/bash
set -e

DIR="/home/pi/pilights/"

# This script installs the pilight application and webserver
cp "$DIR/bin/pilights.py" /usr/sbin/pilights
cp -r "$DIR/www/" /var/www/pilights
