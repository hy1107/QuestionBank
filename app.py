import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from db import init_db, insert_question, get_all_questions, get_question_by_id, update_question, update_question_tags, delete_question
from parser.pdf_parser import parse_pdf
from parser.excel_handler import questions_to_excel, excel_to_questions
from exporter.paper_exporter import export_to_word

def create_app(testing=False):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    if testing:
        app.config['TESTING'] = True

    if not testing:
        init_db()

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/parse')
    def parse_page():
        return render_template('parse.html')

    @app.route('/parse/upload', methods=['POST'])
    def parse_upload():
        if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
            return ('No file', 400)
        f = request.files['pdf_file']
        filename = f'{uuid.uuid4()}.pdf'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        questions = parse_pdf(filepath)
        out_name = f'{uuid.uuid4()}.xlsx'
        out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_name)
        questions_to_excel(questions, out_path)
        return render_template('parse.html', questions=questions, failed=0, download_url=url_for('download_file', filename=out_name))

    @app.route('/download/<filename>')
    def download_file(filename):
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(path, as_attachment=True)

    @app.route('/import')
    def import_page():
        return render_template('import.html')

    @app.route('/import/upload', methods=['POST'])
    def import_upload():
        if 'excel_file' not in request.files or request.files['excel_file'].filename == '':
            return ('No file', 400)
        f = request.files['excel_file']
        filename = f'{uuid.uuid4()}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        try:
            questions = excel_to_questions(filepath)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('import_page'))
        for q in questions:
            q['source_file'] = f.filename
            insert_question(None, q)
        flash(f'成功匯入 {len(questions)} 題', 'success')
        return redirect(url_for('questions_page'))

    @app.route('/questions')
    def questions_page():
        return render_template('questions.html')

    @app.route('/export')
    def export_page():
        return render_template('export.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
