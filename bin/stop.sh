#!/bin/sh
. /var/pythonVM3/bin/activate
uwsgi --stop /run/shop.pid # the --ini option is used to specify a file
deactivate
