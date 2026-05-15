import os
from flask import Flask, render_template

def create_app(testing=False):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    if testing:
        app.config['TESTING'] = True

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
