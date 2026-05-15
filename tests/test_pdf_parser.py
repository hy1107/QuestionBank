import pytest
from parser.pdf_parser import parse_text_to_questions

SAMPLE_TEXT = """
(B) 1. 商管人最需要培養的資料探勘技能是
    (A) 了解演算法
    (B) 理解商業上的管理意涵
    (C) 懂得程式設計
    (D) 學會系統分析。
(D) 2. 商管人應該要至少能以下列角度去看資料探勘，那就是從資料輸入、資料分析
    與資訊輸出等三個單純的動作去展開，資料輸入不包含哪個程序
    (A) 資料欄位選擇
    (B) 前置作業
    (C) 轉換資料格式
    (D) 操作軟體工具。
(A) 3. 單行題目
    (A) 正確答案
    (B) 選項B
    (C) 選項C
    (D) 選項D。
"""

def test_parse_returns_list_of_dicts():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert isinstance(questions, list)
    assert len(questions) == 3

def test_parse_extracts_answer():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert questions[0]['answer'] == 'B'
    assert questions[1]['answer'] == 'D'
    assert questions[2]['answer'] == 'A'

def test_parse_extracts_question_number():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert questions[0]['original_no'] == '1'
    assert questions[1]['original_no'] == '2'

def test_parse_extracts_question_text():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert '商管人最需要培養的資料探勘技能是' in questions[0]['question']

def test_parse_extracts_multiline_question():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert '資料輸入不包含哪個程序' in questions[1]['question']

def test_parse_extracts_options():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert questions[0]['option_a'] == '了解演算法'
    assert questions[0]['option_b'] == '理解商業上的管理意涵'
    assert questions[0]['option_c'] == '懂得程式設計'
    assert questions[0]['option_d'] == '學會系統分析'

def test_parse_strips_trailing_period_from_option_d():
    questions = parse_text_to_questions(SAMPLE_TEXT)
    assert not questions[0]['option_d'].endswith('。')

def test_parse_empty_text():
    questions = parse_text_to_questions('')
    assert questions == []
