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

# Demo instance

There is a demo instance deployed a [mat2-web.dustri.org](https://mat2-web.dustri.org).
Please don't upload any sensitive files on it.

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
# apt install uwsgi uwsgi-plugin-python3 git mat2
# apt install nginx-light  # if you prefer nginx
# apt install apache2 libapache2-mod-proxy-uwsgi  # if you prefer Apache2
# cd /var/www/
# git clone https://0xacab.org/jvoisin/mat2-web.git
# mkdir ./mat2-web/uploads/
# chown -R www-data:www-data ./mat2-web
```

Since uwsgi isn't fun to configure, feel free to copy [this file](https://0xacab.org/jvoisin/mat2-web/tree/master/config/uwsgi.config)
to `/etc/uwsgi/apps-enabled/mat2-web.ini` and [this one](https://0xacab.org/jvoisin/mat2-web/tree/master/config/nginx.config)
to `/etc/nginx/site-enabled/mat2-web`.

Nginx is the recommended web engine, but you can also use Apache if you prefer,
by copying [this file](https://0xacab.org/jvoisin/mat2-web/tree/master/config/apache2.config)
to your `/etc/apache2/sites-enabled/mat2-web` file.

Finally, restart `uwsgi` and your web server:

```
systemctl restart uwsgi
systemctl restart nginx/apache/…
```

It should now be working.

# Threat model

- An attacker in possession of the very same file that a user wants to clean,
	along with its names, can perform a denial of service by continually
	requesting this file, and getting it before the user.
- An attacker in possession of only the name of a file that a user wants to
	clean can't perform a denial of service attack, since the path to download
	the cleaned file is not only dependant of the name, but also the content.
- The server should do its very best to delete files as soon as possible.

# Licenses

- mat2-web is under MIT
- The [raleway](https://github.com/impallari/Raleway/) font is under OFL1.1
- [normalize.css](https://github.com/necolas/normalize.css/) is under MIT
- [skeleton](http://getskeleton.com/) is under MIT
