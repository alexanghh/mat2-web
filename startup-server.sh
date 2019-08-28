#!/bin/bash
/etc/init.d/nginx restart
uwsgi --ini /etc/uwsgi/apps-enabled/mat2-web.ini