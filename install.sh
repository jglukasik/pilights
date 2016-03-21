#!/bin/bash
set -e

DIR="/home/pi/pilights/"

# Install websocket application
cp "$DIR/bin/pilights.py" /usr/sbin/pilights

# Install web server
rm -rf /var/www/frontend
cp -r "$DIR/www/" /var/www/frontend/

# Install init script
cp "$DIR/etc/pilights" /etc/init.d/pilights

# Create runlevel simlinks
update-rc.d -f pilights defaults
