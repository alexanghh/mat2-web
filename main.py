import os

import libmat2
from libmat2 import parser_factory

from flask import Flask, flash, request, redirect, url_for, render_template
from flask import send_from_directory, after_this_request

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['SECRET_KEY'] = '1337'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files: # check if the post request has the file part
            flash('No file part')
            return redirect(request.url)
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(os.path.join(filepath))

        parser, mime = parser_factory.get_parser(filepath)
        if parser is None:
            flash('The type %s is not supported' % mime)
            return redirect(url_for('upload_file'))
        elif parser.remove_all() is not True:
            flash('Unable to clean ' % mime)
            return redirect(url_for('upload_file'))
        os.remove(filename)

        @after_this_request
        def remove_file(response):
            os.remove(parser.output_filename)
            return response

        return send_from_directory(app.config['UPLOAD_FOLDER'], parser.output_filename)

    mimetypes = 'image/jpeg, image/png'
    return render_template('index.html', mimetypes=mimetypes)


app.run()
