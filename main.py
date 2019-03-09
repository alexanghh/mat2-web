import os
import hashlib
import hmac
import mimetypes as mtype

from libmat2 import parser_factory

from flask import Flask, flash, request, redirect, url_for, render_template
from flask import send_from_directory, after_this_request
import jinja2

from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['CUSTOM_TEMPLATES_DIR'] = 'custom_templates'

app.jinja_loader = jinja2.ChoiceLoader([ # type: ignore
    jinja2.FileSystemLoader(app.config['CUSTOM_TEMPLATES_DIR']),
    app.jinja_loader,
    ])

def __hash_file(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(65536)  # read the file by chunk of 64k
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


@app.route('/download/<string:key>/<string:filename>')
def download_file(key:str, filename:str):
    if filename != secure_filename(filename):
        return redirect(url_for('upload_file'))

    filepath = secure_filename(filename)

    complete_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
    if not os.path.exists(complete_path):
        return redirect(url_for('upload_file'))
    if hmac.compare_digest(__hash_file(complete_path), key) is False:
        print('hash: %s, key: %s' % (__hash_file(complete_path), key))
        return redirect(url_for('upload_file'))

    @after_this_request
    def remove_file(response):
        os.remove(complete_path)
        return response
    return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.mkdir(app.config['UPLOAD_FOLDER'])

    mimetypes = set()
    for parser in parser_factory._get_parsers():
        mimetypes |= set(map(mtype.guess_extension, parser.mimetypes))
    # since `guess_extension` might return `None`, we need to filter it out
    mimetypes = sorted(filter(None, mimetypes))

    if request.method == 'POST':
        if 'file' not in request.files: # check if the post request has the file part
            flash('No file part')
            return redirect(request.url)
        uploaded_file = request.files['file']
        if not uploaded_file.filename:
            flash('No selected file')
            return redirect(request.url)
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(os.path.join(filepath))

        parser, mime = parser_factory.get_parser(filepath)
        if parser is None:
            flash('The type %s is not supported' % mime)
            return redirect(url_for('upload_file'))

        meta = parser.get_meta()

        if parser.remove_all() is not True:
            flash('Unable to clean ' % mime)
            return redirect(url_for('upload_file'))
        output_filename = os.path.basename(parser.output_filename)

        # Get metadata after cleanup 
        parser, _ = parser_factory.get_parser(parser.output_filename)
        meta_after = parser.get_meta()
        os.remove(filepath)

        key = __hash_file(os.path.join(app.config['UPLOAD_FOLDER'], output_filename))

        return render_template('download.html', mimetypes=mimetypes, meta=meta, filename=output_filename, meta_after=meta_after, key=key)

    max_file_size = int(app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024)
    return render_template('index.html', max_file_size=max_file_size, mimetypes=mimetypes)


if __name__ == '__main__':  # pragma: no cover
    app.run()
