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
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB
    if testing:
        app.config['TESTING'] = True

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
        if not f.filename.lower().endswith('.pdf'):
            flash('請上傳 PDF 格式的檔案', 'error')
            return redirect(url_for('parse_page'))
        filename = f'{uuid.uuid4()}.pdf'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        try:
            questions = parse_pdf(filepath)
            out_name = f'{uuid.uuid4()}.xlsx'
            out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_name)
            questions_to_excel(questions, out_path)
        except Exception as e:
            flash(f'PDF 解析失敗：{e}', 'error')
            return redirect(url_for('parse_page'))
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
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
        if not f.filename.lower().endswith('.xlsx'):
            flash('請上傳 .xlsx 格式的 Excel 檔案', 'error')
            return redirect(url_for('import_page'))
        filename = f'{uuid.uuid4()}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        try:
            questions = excel_to_questions(filepath)
        except Exception as e:
            flash(f'匯入失敗：{e}', 'error')
            return redirect(url_for('import_page'))
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
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

    @app.route('/api/questions')
    def api_questions():
        filters = {
            'keyword': request.args.get('keyword', ''),
            'subject': request.args.get('subject', ''),
            'difficulty': request.args.get('difficulty', ''),
            'no_from': request.args.get('no_from', ''),
            'no_to': request.args.get('no_to', ''),
        }
        filters = {k: v for k, v in filters.items() if v}
        questions = get_all_questions(None, filters)
        return jsonify(questions)

    @app.route('/api/questions/<int:qid>', methods=['PATCH'])
    def api_update_question(qid):
        data = request.get_json()
        update_question(None, qid, data)
        if 'tags' in data:
            update_question_tags(None, qid, data['tags'])
        return jsonify({'ok': True})

    @app.route('/api/questions/<int:qid>', methods=['DELETE'])
    def api_delete_question(qid):
        delete_question(None, qid)
        return jsonify({'ok': True})

    @app.route('/export/download', methods=['POST'])
    def export_download():
        data = request.get_json()
        ids = data.get('ids', [])
        fmt = data.get('format', 'word')
        show_answers = data.get('show_answers', False)
        count = data.get('count')
        order = data.get('order', 'sequential')

        filters = {k: v for k, v in {
            'subject': data.get('subject', ''),
            'difficulty': data.get('difficulty', ''),
            'no_from': data.get('no_from', ''),
            'no_to': data.get('no_to', ''),
        }.items() if v}

        if ids:
            questions = [q for q in (get_question_by_id(None, i) for i in ids) if q]
        else:
            questions = get_all_questions(None, filters)

        if order == 'random':
            import random
            random.shuffle(questions)

        if count:
            questions = questions[:int(count)]

        if not questions:
            return ('No questions selected', 400)

        out_name = f'{uuid.uuid4()}.{"docx" if fmt == "word" else "xlsx"}'
        out_path = os.path.join(app.config['UPLOAD_FOLDER'], out_name)

        if fmt == 'word':
            export_to_word(questions, out_path, show_answers=show_answers)
        else:
            questions_to_excel(questions, out_path)

        return jsonify({'download_url': url_for('download_file', filename=out_name)})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
