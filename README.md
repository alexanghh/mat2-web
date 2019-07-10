```
                 _   ___                     _     
                | | |__ \                   | |    
 _ __ ___   __ _| |_   ) | ___ __      _____| |__   Trashing your meta,
| '_ ` _ \ / _` | __| / / |___|\ \ /\ / / _ \ '_ \    keeping your data,
| | | | | | (_| | |_ / /_       \ V  V /  __/ |_) |     within your browser.
|_| |_| |_|\__,_|\__|____|       \_/\_/ \___|_.__/ 
```

This is an online version of [mat2](https://0xacab.org/jvoisin/mat2).
Keep in mind that this is a beta version, don't rely on it for anything
serious, yet.

# Demo instance

There is a demo instance deployed a [mat2-web.dustri.org](https://mat2-web.dustri.org).
Please don't upload any sensitive files to it.

# How to deploy it?

mat2 is available in [Debian stable](https://packages.debian.org/stable/mat2).

```
# apt install uwsgi uwsgi-plugin-python3 git mat2
# apt install nginx-light  # if you prefer nginx
# apt install apache2 libapache2-mod-proxy-uwsgi  # if you prefer Apache2
# cd /var/www/
# git clone https://0xacab.org/jvoisin/mat2-web.git
# mkdir ./mat2-web/uploads/
# chown -R www-data:www-data ./mat2-web
```

Since [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) isn't fun to
configure, feel free to copy
[this file](https://0xacab.org/jvoisin/mat2-web/tree/master/config/uwsgi.config)
to `/etc/uwsgi/apps-enabled/mat2-web.ini` and
[this one](https://0xacab.org/jvoisin/mat2-web/tree/master/config/nginx.config)
to `/etc/nginx/site-enabled/mat2-web`.

Nginx is the recommended web engine, but you can also use Apache if you prefer,
by copying [this file](https://0xacab.org/jvoisin/mat2-web/tree/master/config/apache2.config)
to your `/etc/apache2/sites-enabled/mat2-web` file.

Then configure the environment variable: `MAT2_ALLOW_ORIGIN_WHITELIST=https://myhost1.org https://myhost2.org`
Note that you can add multiple hosts from which you want to accept API requests. These need to be separated by
a space.
**IMPORTANT:** The default value if the variable is not set is: `Access-Control-Allow-Origin: *`

Finally, restart uWSGI and your web server:

```
systemctl restart uwsgi
systemctl restart nginx/apache/…
```

It should now be working.

You should add `find /var/www/mat2-web/uploads/ -type f -mtime +1 -exec rm {} \;`
in a crontab to remove files that people might have uploaded but never
downloaded.

# Deploy via Ansible

If you happen to be using [Ansible](https://www.ansible.com/), there's an
Ansible role to deploy mat2-web on Debian, thanks to the amazing
[systemli](https://www.systemli.org/en/index.html) people:
[ansible-role-mat2-web](https://github.com/systemli/ansible-role-mat2-web)

The role installs mat2-web as a uWSGI service, and runs it as a dedicated
system user, installs bubblewrap to sandbox mat2 and creates a garbage
collector cronjob to remove leftover files. Besides, it can create a
[dm-crypt](https://en.wikipedia.org/wiki/Dm-crypt) volume with random key for
the uploads folder, to ensure that the uploaded files won't be recoverable
between reboots.

# Development
Install docker and docker-compose and then run `docker-compose up` to setup
the docker dev environment. Mat2-web is now accessible on your host machine at `localhost:5000`.
Every code change triggers a restart of the app. 
If you want to add/remove dependencies you have to rebuild the container.

# RESTful API

## Upload Endpoint

**Endpoint:** `/api/upload`

**HTTP Verbs:**  POST

**Body:** 
```json
{
	"file_name": "my-filename.jpg",
	"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
}
```

The `file_name` parameter takes the file name.
The `file` parameter is the base64 encoded file which will be cleaned.

**Example Response:**
```json
{
    "output_filename": "fancy.cleaned.jpg",
    "key": "81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161",
    "meta": {
        "BitDepth": 8,
        "ColorType": "RGB with Alpha",
        "Compression": "Deflate/Inflate",
        "Filter": "Adaptive",
        "Interlace": "Noninterlaced"
    },
    "meta_after": {},
    "download_link": "http://localhost:5000/download/81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161/fancy.cleaned.jpg"
}
```

## Supported Extensions Endpoint

**Endpoint:** `/api/extension`

**HTTP Verbs:**  GET

**Example Response (shortened):**
```json
[
    ".asc",
    ".avi",
    ".bat",
    ".bmp",
    ".brf",
    ".c",
    ".css",
    ".docx",
    ".epub"
]
```

# Custom templates

You can override the default templates from `templates/` by putting replacements
into the directory path that's configured in `app.config['CUSTOM_TEMPLATES_DIR']`
(default `custom_templates/`).

# Threat model

- An attacker in possession of the very same file that a user wants to clean,
	along with its names, can perform a denial of service by continually
	requesting this file, and getting it before the user.
- An attacker in possession of only the name of a file that a user wants to
	clean can't perform a denial of service attack, since the path to download
	the cleaned file is not only dependent of the name, but also the content.
- The server should do its very best to delete files as soon as possible.

# Licenses

- mat2-web is under MIT
- The [raleway](https://github.com/impallari/Raleway/) font is under OFL1.1
- [normalize.css](https://github.com/necolas/normalize.css/) is under MIT
- [skeleton](http://getskeleton.com/) is under MIT
