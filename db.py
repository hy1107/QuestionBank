import sqlite3

DB_PATH = 'questions.db'

def get_conn(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db(db_path=None):
    conn = get_conn(db_path)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_no TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL,
            subject TEXT DEFAULT '',
            chapter TEXT DEFAULT '',
            difficulty TEXT DEFAULT 'medium',
            source_file TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS quiz_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            taken_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def insert_question(db_path, q):
    conn = get_conn(db_path)
    cur = conn.execute(
        '''INSERT INTO questions
           (original_no, question, option_a, option_b, option_c, option_d,
            answer, subject, chapter, difficulty, source_file)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (q['original_no'], q['question'], q['option_a'], q['option_b'],
         q['option_c'], q['option_d'], q['answer'],
         q.get('subject',''), q.get('chapter',''),
         q.get('difficulty','medium'), q.get('source_file',''))
    )
    qid = cur.lastrowid
    conn.commit()
    conn.close()
    return qid

def get_all_questions(db_path=None, filters=None):
    conn = get_conn(db_path)
    query = 'SELECT * FROM questions'
    params = []
    if filters:
        clauses = []
        if filters.get('subject'):
            clauses.append('subject = ?')
            params.append(filters['subject'])
        if filters.get('chapter'):
            clauses.append('chapter = ?')
            params.append(filters['chapter'])
        if filters.get('difficulty'):
            clauses.append('difficulty = ?')
            params.append(filters['difficulty'])
        if filters.get('keyword'):
            clauses.append('question LIKE ?')
            params.append(f"%{filters['keyword']}%")
        if filters.get('no_from') and filters.get('no_to'):
            clauses.append('CAST(original_no AS INTEGER) BETWEEN ? AND ?')
            params.extend([int(filters['no_from']), int(filters['no_to'])])
        if clauses:
            query += ' WHERE ' + ' AND '.join(clauses)
    rows = conn.execute(query, params).fetchall()
    questions = []
    for row in rows:
        q = dict(row)
        q['tags'] = [t['tag'] for t in
                     conn.execute('SELECT tag FROM tags WHERE question_id=?', (q['id'],)).fetchall()]
        questions.append(q)
    conn.close()
    return questions

def get_question_by_id(db_path=None, qid=None):
    if qid is None:
        db_path, qid = DB_PATH, db_path
    conn = get_conn(db_path)
    row = conn.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
    if row is None:
        conn.close()
        return None
    q = dict(row)
    q['tags'] = [t['tag'] for t in
                 conn.execute('SELECT tag FROM tags WHERE question_id=?', (qid,)).fetchall()]
    conn.close()
    return q

def update_question(db_path=None, qid=None, data=None):
    if data is None:
        db_path, qid, data = DB_PATH, db_path, qid
    conn = get_conn(db_path)
    conn.execute(
        '''UPDATE questions SET subject=?, chapter=?, difficulty=?
           WHERE id=?''',
        (data.get('subject',''), data.get('chapter',''),
         data.get('difficulty','medium'), qid)
    )
    conn.commit()
    conn.close()

def update_question_tags(db_path=None, qid=None, tags=None):
    if tags is None:
        db_path, qid, tags = DB_PATH, db_path, qid
    conn = get_conn(db_path)
    conn.execute('DELETE FROM tags WHERE question_id=?', (qid,))
    for tag in tags:
        if tag.strip():
            conn.execute('INSERT INTO tags (question_id, tag) VALUES (?,?)', (qid, tag.strip()))
    conn.commit()
    conn.close()

def delete_question(db_path=None, qid=None):
    if qid is None:
        db_path, qid = DB_PATH, db_path
    conn = get_conn(db_path)
    conn.execute('DELETE FROM questions WHERE id=?', (qid,))
    conn.commit()
    conn.close()

def save_quiz_result(db_path=None, results=None):
    if results is None:
        db_path, results = DB_PATH, db_path
    conn = get_conn(db_path)
    conn.execute('DELETE FROM quiz_result')
    for r in results:
        conn.execute(
            'INSERT INTO quiz_result (question_id, user_answer, is_correct) VALUES (?,?,?)',
            (r['question_id'], r['user_answer'], r['is_correct'])
        )
    conn.commit()
    conn.close()

def get_quiz_result(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = get_conn(db_path)
    rows = conn.execute('''
        SELECT qr.question_id, qr.user_answer, qr.is_correct, qr.taken_at,
               q.question, q.answer, q.option_a, q.option_b, q.option_c, q.option_d
        FROM quiz_result qr
        JOIN questions q ON qr.question_id = q.id
        ORDER BY qr.id
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]
