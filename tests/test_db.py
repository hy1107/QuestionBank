import pytest
import sqlite3
import tempfile
import os
from db import init_db, insert_question, get_all_questions, get_question_by_id, update_question_tags, delete_question

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
