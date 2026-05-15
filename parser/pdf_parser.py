import re
import pdfplumber

def parse_text_to_questions(text):
    question_pattern = re.compile(r'^\(([ABCD])\)\s*(\d+)[.、．]\s*(.+)')
    option_pattern = re.compile(r'^\s+\(([ABCD])\)\s+(.+)')

    questions = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        m = question_pattern.match(lines[i].strip())
        if not m:
            i += 1
            continue

        answer = m.group(1)
        original_no = m.group(2)
        question_text = m.group(3).strip()
        i += 1

        # Collect continuation lines and options
        options = {}
        while i < len(lines):
            line = lines[i]
            opt_m = option_pattern.match(line)
            if opt_m:
                opt_letter = opt_m.group(1)
                opt_text = opt_m.group(2).strip()
                if opt_letter == 'D':
                    opt_text = opt_text.rstrip('。.')
                options[opt_letter] = opt_text
                i += 1
                if opt_letter == 'D':
                    break
            elif re.match(r'^\(([ABCD])\)\s*\d+[.、．]', line.strip()):
                break
            elif line.strip():
                question_text += ' ' + line.strip()
                i += 1
            else:
                i += 1

        if len(options) == 4:
            questions.append({
                'original_no': original_no,
                'question': question_text,
                'option_a': options.get('A', ''),
                'option_b': options.get('B', ''),
                'option_c': options.get('C', ''),
                'option_d': options.get('D', ''),
                'answer': answer,
                'subject': '',
                'chapter': '',
                'difficulty': 'medium',
                'source_file': '',
            })

    return questions

def parse_pdf(filepath):
    text = ''
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    questions = parse_text_to_questions(text)
    return questions
