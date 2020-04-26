import hmac
import os

from flask import Blueprint, render_template, url_for, current_app, after_this_request, send_from_directory, request, \
    flash
from werkzeug.utils import secure_filename, redirect

from matweb import file_removal_scheduler, utils

routes = Blueprint('routes', __name__)


@routes.route('/info')
def info():
    utils.get_supported_extensions()
    return render_template(
        'info.html', extensions=utils.get_supported_extensions()
    )


@routes.route('/download/<string:key>/<string:secret>/<string:filename>')
def download_file(key: str, secret: str, filename: str):
    if filename != secure_filename(filename):
        return redirect(url_for('routes.upload_file'))

    complete_path, filepath = utils.get_file_paths(filename, current_app.config['UPLOAD_FOLDER'])
    file_removal_scheduler.run_file_removal_job(current_app.config['UPLOAD_FOLDER'])

    if not os.path.exists(complete_path):
        return redirect(url_for('routes.upload_file'))
    if hmac.compare_digest(utils.hash_file(complete_path, secret), key) is False:
        return redirect(url_for('routes.upload_file'))

    @after_this_request
    def remove_file(response):
        if os.path.exists(complete_path):
            os.remove(complete_path)
        return response
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filepath, as_attachment=True)


@routes.route('/', methods=['GET', 'POST'])
def upload_file():
    utils.check_upload_folder(current_app.config['UPLOAD_FOLDER'])
    mime_types = utils.get_supported_extensions()

    if request.method == 'POST':
        if 'file' not in request.files:  # check if the post request has the file part
            flash('No file part')
            return redirect(request.url)

        uploaded_file = request.files['file']
        if not uploaded_file.filename:
            flash('No selected file')
            return redirect(request.url)

        filename, filepath = utils.save_file(uploaded_file, current_app.config['UPLOAD_FOLDER'])
        parser, mime = utils.get_file_parser(filepath)

        if parser is None:
            flash('The type %s is not supported' % mime)
            return redirect(url_for('routes.upload_file'))

        meta = parser.get_meta()

        if parser.remove_all() is not True:
            flash('Unable to clean %s' % mime)
            return redirect(url_for('routes.upload_file'))

        key, secret, meta_after, output_filename = utils.cleanup(parser, filepath, current_app.config['UPLOAD_FOLDER'])

        return render_template(
            'download.html',
            mimetypes=mime_types,
            meta=meta,
            download_uri=url_for('routes.download_file', key=key, secret=secret, filename=output_filename),
            meta_after=meta_after,
        )

    max_file_size = int(current_app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024)
    return render_template('index.html', max_file_size=max_file_size, mimetypes=mime_types)