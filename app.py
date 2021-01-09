import json
import sys
import os
import warnings
from file_manager import FileSystemManager
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from io_utils import read_textfile

ALLOWED_EXTENSIONS = {'zip'}

config_path = os.environ.get("TEMPLATE_FILLER_CONFIG", "config.json")

app = Flask(__name__)
content = read_textfile(config_path)
cfg = json.loads(content)
app.config.update(cfg)

secret_key = cfg.get('SECRET_KEY', '')
if len(secret_key) < 24:
    secret_key = os.urandom(24)
    print(
        f"'secret_key' defined in config.json is too weak. "
        f"Randomly generating a new one: {secret_key}",
        file=sys.stderr
    )
app.secret_key = secret_key

manager = FileSystemManager(
    zip_dir=app.config['ZIP_DIR'],
    extracted_dir=app.config["EXTRACTED_DIR"],
    download_dir=app.config["DOWNLOAD_DIR"],
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return redirect(url_for('upload_file_and_check'))


@app.route('/uploads/check')
@app.route('/uploads/nocheck')
def legacy_upload():
    flash("Note: '/uploads/check' and '/uploads/nocheck' are permanently moved to '/uploads/new-letter'. "
          "Double check the address bar of your browser.", category="warning")
    return redirect(url_for("upload_file_and_check"), 301)


@app.route('/uploads/new-letter', methods=['GET', 'POST'])
def upload_file_and_check():
    if request.method == 'POST':
        print(request.form)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            check_error = (request.form.get("check_error", "off") == "on")
            pre_para_id = int(request.form.get("pre_para_id", 0))

            filename = secure_filename(file.filename)
            download_name = manager.handle(file=file, filename=filename, pre_para_id=pre_para_id, check=check_error)
            return redirect(url_for('download_file', filename=download_name))

    return render_template('upload.html')


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_DIR'], filename)


if __name__ == '__main__':
    app.run()
