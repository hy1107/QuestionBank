import pytest
import sqlite3
import tempfile
import os
from db import init_db, insert_question, get_all_questions, get_question_by_id, update_question, update_question_tags, delete_question, save_quiz_result, get_quiz_result

@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / 'test.db')
    init_db(path)
    return path

def test_init_creates_tables(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [t[0] for t in tables]
    assert 'questions' in names
    assert 'tags' in names
    conn.close()

def test_insert_and_retrieve_question(db_path):
    q = {
        'original_no': '1',
        'question': '測試題目',
        'option_a': '選A',
        'option_b': '選B',
        'option_c': '選C',
        'option_d': '選D',
        'answer': 'A',
        'subject': '數學',
        'chapter': '第一章',
        'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    assert qid is not None
    questions = get_all_questions(db_path)
    assert len(questions) == 1
    assert questions[0]['question'] == '測試題目'

def test_get_question_by_id(db_path):
    q = {
        'original_no': '2', 'question': '第二題', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'B', 'subject': '', 'chapter': '', 'difficulty': 'medium',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    result = get_question_by_id(db_path, qid)
    assert result['original_no'] == '2'

def test_update_question_tags(db_path):
    q = {
        'original_no': '3', 'question': '第三題', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'C', 'subject': '', 'chapter': '', 'difficulty': 'hard',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    update_question_tags(db_path, qid, ['重要', '常考'])
    result = get_question_by_id(db_path, qid)
    assert set(result['tags']) == {'重要', '常考'}

def test_delete_question(db_path):
    q = {
        'original_no': '4', 'question': '刪除題', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'D', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    delete_question(db_path, qid)
    assert get_question_by_id(db_path, qid) is None

def test_delete_question_removes_tags(db_path):
    q = {
        'original_no': '5', 'question': '刪除含標籤題', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'A', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    update_question_tags(db_path, qid, ['重要'])
    delete_question(db_path, qid)
    # Verify orphaned tags are gone
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    orphans = conn.execute('SELECT * FROM tags WHERE question_id=?', (qid,)).fetchall()
    conn.close()
    assert len(orphans) == 0

def test_update_question(db_path):
    q = {
        'original_no': '6', 'question': '更新測試', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'A', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    update_question(db_path, qid, {'subject': '科學', 'chapter': '第二章', 'difficulty': 'hard'})
    result = get_question_by_id(db_path, qid)
    assert result['subject'] == '科學'
    assert result['chapter'] == '第二章'
    assert result['difficulty'] == 'hard'

def test_init_creates_quiz_result_table(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [t[0] for t in tables]
    assert 'quiz_result' in names
    conn.close()

def test_save_quiz_result_stores_records(db_path):
    q = {
        'original_no': '1', 'question': '題目', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'A', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    results = [{'question_id': qid, 'user_answer': 'A', 'is_correct': 1}]
    save_quiz_result(db_path, results)
    rows = get_quiz_result(db_path)
    assert len(rows) == 1
    assert rows[0]['user_answer'] == 'A'
    assert rows[0]['is_correct'] == 1
    assert rows[0]['question'] == '題目'
    assert rows[0]['answer'] == 'A'

def test_save_quiz_result_overwrites_previous(db_path):
    q = {
        'original_no': '1', 'question': '題目', 'option_a': 'A',
        'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'B', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': 'test.xlsx',
    }
    qid = insert_question(db_path, q)
    save_quiz_result(db_path, [{'question_id': qid, 'user_answer': 'A', 'is_correct': 0}])
    save_quiz_result(db_path, [{'question_id': qid, 'user_answer': 'B', 'is_correct': 1}])
    rows = get_quiz_result(db_path)
    assert len(rows) == 1
    assert rows[0]['user_answer'] == 'B'

def test_get_quiz_result_empty(db_path):
    rows = get_quiz_result(db_path)
    assert rows == []
