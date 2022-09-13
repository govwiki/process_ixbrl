from flask import Flask
from pathlib import Path
uploadDirectoryAbsolutePath = Path('upload').absolute()
UPLOAD_FOLDER = uploadDirectoryAbsolutePath

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024