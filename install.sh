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

# this breaks stuff, no services get run at boot
# ln -sf /etc/init.d/pilights /etc/rc0.d/K01pilights
# ln -sf /etc/init.d/pilights /etc/rc1.d/K01pilights
# ln -sf /etc/init.d/pilights /etc/rc6.d/K01pilights
# 
# ln -sf /etc/init.d/pilights /etc/rc3.d/S03pilights
# ln -sf /etc/init.d/pilights /etc/rc4.d/S03pilights
# ln -sf /etc/init.d/pilights /etc/rc5.d/S03pilights
# 
# ln -sf /etc/init.d/pilights /etc/rcS.d/S17pilights
