import json
import os
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

manager = FileSystemManager(
    zip_dir=app.config['ZIP_DIR'],
    extracted_dir=app.config["EXTRACTED_DIR"],
    download_dir=app.config["DOWNLOAD_DIR"],
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<check>', methods=['GET', 'POST'])
def upload_file_and_check(check):
    if check == "check" or check == "":
        check = True
    elif check == "nocheck":
        check = False
    else:
        return "Page not found", 404

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file.filename == 'test.zip':
            flash('testing flash')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            download_name = manager.handle(file=file, filename=filename, check=check)
            return redirect(url_for('download_file', filename=download_name))

    return render_template('upload.html')


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_DIR'], filename)


if __name__ == '__main__':
    app.run(debug=True)
