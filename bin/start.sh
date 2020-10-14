#!/bin/sh
. /var/pythonVM3/bin/activate
#uwsgi --reload /tmp/shop.pid # the --ini option is used to specify a file
#deactivate
uwsgi --ini /flask/flask_Demo/bin/mysite_uwsgi.ini  # the --ini option is used to specify a file
deactivate
