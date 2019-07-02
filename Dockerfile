FROM python:3.7
ADD . /mat2-web
WORKDIR /mat2-web
RUN apt-get update
RUN apt install -y python3-gi python3-gi-cairo gir1.2-poppler-0.18 \
gir1.2-gdkpixbuf-2.0 libimage-exiftool-perl libgirepository1.0-dev
RUN pip install -r requirements.txt
CMD flask run --host=0.0.0.0