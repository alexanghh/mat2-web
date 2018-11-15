```
                  _   ___                     _     
                 | | |__ \                   | |    
  _ __ ___   __ _| |_   ) |_______      _____| |__    Trashing your meta,
 | '_ ` _ \ / _` | __| / /______\ \ /\ / / _ \ '_ \     keeping your data,
 | | | | | | (_| | |_ / /_       \ V  V /  __/ |_) |      within your browser.
 |_| |_| |_|\__,_|\__|____|       \_/\_/ \___|_.__/ 
 ```

This is an online version of [mat2](https://0xacab.org/jvoisin/mat2).
Keep in mind that this is a beta version, don't rely on it for anything
serious, yet.

# How to deploy it?

Since mat2 isn't available in debian stable yet, you might want to add this to
/etc/apt/preferences.d/ to be able to install `mat2` via apt.

```
Package: *
Pin: release o=Debian,a=unstable
Pin-Priority: 10
```

Then:

```
# apt install git nginx-light uwsgi uwsgi-plugin-python3 mat2 --no-install-recommends
# cd /var/www/
# git clone https://0xacab.org/jvoisin/mat2-web.git
# mkdir ./mat2-web/uploads/
# chown -R www-data:www-data ./mat2-web
# service uwsgi start
# service nginx start
```

Since uwsgi isn't fun to configure, feel free to slap this into your
`/etc/uwsgi/apps-enabled/mat2-web.ini`:

```
[uwsgi]
module=main
chdir = /var/www/mat2-web/
callable = app
wsgi-file = main.py
master = true
workers = 1

uid = www-data
gid = www-data

# kill stalled processes
harakiri = 30
die-on-term = true

socket = mat2-web.sock
chmod-socket = 774
plugins = python3
```

and this into your `/etc/nginx/site-enabled/mat2-web`:

```
        location / { try_files $uri @yourapplication; }
        location @yourapplication {
                include uwsgi_params;
                uwsgi_pass unix:/var/www/mat2-web/mat2-web.sock;
        }
```

It should now be working.
