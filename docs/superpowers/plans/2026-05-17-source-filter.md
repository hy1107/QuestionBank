# Source File Filter & Batch Delete Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-file dropdown filter to the questions page and a batch-delete button that removes all questions from the selected source.

**Architecture:** Extend the existing AJAX pattern — new DB functions feed two new REST endpoints; `main.js` populates the dropdown on load, wires `loadQuestions()` to the new filter, and triggers batch delete with confirmation.

**Tech Stack:** Python Flask, SQLite, vanilla JS (no new dependencies)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `db.py` | Add `get_source_files()`, `delete_questions_by_source()`, add `source_file` filter to `get_all_questions()` |
| Modify | `app.py` | Add `GET /api/source-files`, `DELETE /api/questions/by-source`, add `source_file` param to `GET /api/questions` |
| Modify | `templates/questions.html` | Add `#filter-source` dropdown and `#delete-source` button to toolbar |
| Modify | `static/main.js` | Add `loadSourceFiles()`, update `loadQuestions()`, add change/click handlers |
| Modify | `tests/test_db.py` | Tests for `get_source_files` and `delete_questions_by_source` |
| Modify | `tests/test_routes.py` | Tests for new API routes |

---

### Task 1: DB Layer — get_source_files, delete_questions_by_source, source_file filter

**Files:**
- Modify: `db.py`
- Modify: `tests/test_db.py`

**Context:** `db.py` is at `/Users/yanghaoyu/Desktop/new_idea/題庫密室/db.py`. All functions follow a dual-signature pattern: `func(db_path=None, arg=None)` — when `arg is None`, treat `db_path` as the arg and use `DB_PATH`. The existing `get_all_questions(db_path=None, filters=None)` already handles `subject`, `chapter`, `difficulty`, `keyword`, `no_from`, `no_to` in a `clauses`/`params` list pattern.

Existing test fixture in `tests/test_db.py`:
```python
@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / 'test.db')
    init_db(path)
    return path
```

- [ ] **Step 1: Write failing tests**

Add to `tests/test_db.py`. First, extend the import line (currently ends with `delete_question`):

```python
from db import (init_db, insert_question, get_all_questions, get_question_by_id,
                update_question, update_question_tags, delete_question,
                save_quiz_result, get_quiz_result,
                get_source_files, delete_questions_by_source)
```

Then add these tests after the existing ones:

```python
def _make_question(original_no, source_file='test.xlsx'):
    return {
        'original_no': original_no, 'question': f'題目{original_no}',
        'option_a': 'A', 'option_b': 'B', 'option_c': 'C', 'option_d': 'D',
        'answer': 'A', 'subject': '', 'chapter': '', 'difficulty': 'easy',
        'source_file': source_file,
    }

def test_get_source_files_returns_distinct_sorted(db_path):
    insert_question(db_path, _make_question('1', 'beta.xlsx'))
    insert_question(db_path, _make_question('2', 'alpha.xlsx'))
    insert_question(db_path, _make_question('3', 'beta.xlsx'))
    sources = get_source_files(db_path)
    assert sources == ['alpha.xlsx', 'beta.xlsx']

def test_get_source_files_excludes_empty(db_path):
    insert_question(db_path, _make_question('1', ''))
    insert_question(db_path, _make_question('2', 'file.xlsx'))
    sources = get_source_files(db_path)
    assert sources == ['file.xlsx']

def test_get_source_files_empty_db(db_path):
    assert get_source_files(db_path) == []

def test_delete_questions_by_source_removes_correct_rows(db_path):
    insert_question(db_path, _make_question('1', 'a.xlsx'))
    insert_question(db_path, _make_question('2', 'a.xlsx'))
    insert_question(db_path, _make_question('3', 'b.xlsx'))
    deleted = delete_questions_by_source(db_path, 'a.xlsx')
    assert deleted == 2
    remaining = get_all_questions(db_path)
    assert len(remaining) == 1
    assert remaining[0]['source_file'] == 'b.xlsx'

def test_delete_questions_by_source_returns_zero_for_unknown(db_path):
    deleted = delete_questions_by_source(db_path, 'nonexistent.xlsx')
    assert deleted == 0

def test_get_all_questions_filters_by_source_file(db_path):
    insert_question(db_path, _make_question('1', 'a.xlsx'))
    insert_question(db_path, _make_question('2', 'b.xlsx'))
    result = get_all_questions(db_path, {'source_file': 'a.xlsx'})
    assert len(result) == 1
    assert result[0]['source_file'] == 'a.xlsx'
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/yanghaoyu/Desktop/new_idea/題庫密室
pytest tests/test_db.py::test_get_source_files_returns_distinct_sorted -v
```

Expected: FAIL with `ImportError: cannot import name 'get_source_files'`

- [ ] **Step 3: Add get_source_files to db.py**

Append at the end of `db.py`:

```python
def get_source_files(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = get_conn(db_path)
    rows = conn.execute(
        "SELECT DISTINCT source_file FROM questions WHERE source_file != '' ORDER BY source_file"
    ).fetchall()
    conn.close()
    return [r['source_file'] for r in rows]
```

- [ ] **Step 4: Add delete_questions_by_source to db.py**

Append after `get_source_files`:

```python
def delete_questions_by_source(db_path=None, source_file=None):
    if source_file is None:
        db_path, source_file = DB_PATH, db_path
    conn = get_conn(db_path)
    result = conn.execute('DELETE FROM questions WHERE source_file = ?', (source_file,))
    deleted = result.rowcount
    conn.commit()
    conn.close()
    return deleted
```

- [ ] **Step 5: Add source_file filter to get_all_questions**

In `db.py`, inside `get_all_questions`, find the block that checks `filters.get('keyword')` and add one more clause after it (before `if clauses:`):

```python
        if filters.get('source_file'):
            clauses.append('source_file = ?')
            params.append(filters['source_file'])
```

The full filters block should look like:

```python
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
        if filters.get('source_file'):
            clauses.append('source_file = ?')
            params.append(filters['source_file'])
        if clauses:
            query += ' WHERE ' + ' AND '.join(clauses)
```

- [ ] **Step 6: Run all DB tests**

```bash
pytest tests/test_db.py -v
```

Expected: All 17 tests PASS (11 existing + 6 new)

- [ ] **Step 7: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: add get_source_files, delete_questions_by_source, source_file filter"
```

---

### Task 2: API Routes

**Files:**
- Modify: `app.py`
- Modify: `tests/test_routes.py`

**Context:** `app.py` is at `/Users/yanghaoyu/Desktop/new_idea/題庫密室/app.py`. All routes are inside `create_app()`. Current import from db:
```python
from db import (init_db, insert_question, get_all_questions, get_question_by_id,
                update_question, update_question_tags, delete_question,
                save_quiz_result, get_quiz_result)
```
The existing `api_questions` route reads filters from `request.args` and passes them to `get_all_questions`.

- [ ] **Step 1: Write failing route tests**

Add to `tests/test_routes.py`:

```python
def test_api_source_files_returns_json_list(client):
    response = client.get('/api/source-files')
    assert response.status_code == 200
    assert response.is_json
    assert isinstance(response.get_json(), list)

def test_api_delete_by_source_missing_param_returns_400(client):
    response = client.delete('/api/questions/by-source')
    assert response.status_code == 400

def test_api_delete_by_source_unknown_source_returns_zero(client):
    response = client.delete('/api/questions/by-source?source_file=nonexistent.xlsx')
    assert response.status_code == 200
    assert response.get_json()['deleted'] == 0

def test_api_questions_accepts_source_file_filter(client):
    response = client.get('/api/questions?source_file=test.xlsx')
    assert response.status_code == 200
    assert response.is_json
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_routes.py::test_api_source_files_returns_json_list -v
```

Expected: FAIL with 404

- [ ] **Step 3: Update db import in app.py**

Replace the `from db import ...` line:

```python
from db import (init_db, insert_question, get_all_questions, get_question_by_id,
                update_question, update_question_tags, delete_question,
                save_quiz_result, get_quiz_result,
                get_source_files, delete_questions_by_source)
```

- [ ] **Step 4: Add source_file to /api/questions filter**

In `app.py`, find `api_questions` and update the `filters` dict to include `source_file`:

```python
    @app.route('/api/questions')
    def api_questions():
        filters = {
            'keyword': request.args.get('keyword', ''),
            'subject': request.args.get('subject', ''),
            'difficulty': request.args.get('difficulty', ''),
            'no_from': request.args.get('no_from', ''),
            'no_to': request.args.get('no_to', ''),
            'source_file': request.args.get('source_file', ''),
        }
        filters = {k: v for k, v in filters.items() if v}
        questions = get_all_questions(None, filters)
        return jsonify(questions)
```

- [ ] **Step 5: Add two new routes inside create_app before return app**

```python
    @app.route('/api/source-files')
    def api_source_files():
        return jsonify(get_source_files())

    @app.route('/api/questions/by-source', methods=['DELETE'])
    def api_delete_by_source():
        source_file = request.args.get('source_file', '')
        if not source_file:
            return ('source_file parameter required', 400)
        deleted = delete_questions_by_source(None, source_file)
        return jsonify({'deleted': deleted})
```

- [ ] **Step 6: Run route tests**

```bash
pytest tests/test_routes.py -v
```

Expected: All 17 tests PASS (13 existing + 4 new)

- [ ] **Step 7: Commit**

```bash
git add app.py tests/test_routes.py
git commit -m "feat: add /api/source-files and /api/questions/by-source routes"
```

---

### Task 3: Frontend — toolbar + main.js

**Files:**
- Modify: `templates/questions.html`
- Modify: `static/main.js`

No automated tests for this task — verify manually.

- [ ] **Step 1: Update templates/questions.html toolbar**

Replace the existing `<div class="toolbar">` block with:

```html
<div class="toolbar">
  <input type="text" id="search" placeholder="搜尋題目..." class="mock-input">
  <select id="filter-difficulty">
    <option value="">所有難度</option>
    <option value="easy">簡單</option>
    <option value="medium">中等</option>
    <option value="hard">困難</option>
  </select>
  <select id="filter-source">
    <option value="">所有來源</option>
  </select>
  <button id="delete-source" class="btn" style="background:#e74c3c;display:none">刪除此來源所有題目</button>
  <button id="export-selected" class="btn">加入出題清單 (<span id="selected-count">0</span>)</button>
</div>
```

- [ ] **Step 2: Add loadSourceFiles() to main.js**

After the `loadQuestions` function definition, add:

```javascript
function loadSourceFiles() {
  fetch('/api/source-files')
    .then(r => r.json())
    .then(sources => {
      const sel = document.getElementById('filter-source');
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = '<option value="">所有來源</option>' +
        sources.map(s => `<option value="${escapeHtml(s)}"${s === current ? ' selected' : ''}>${escapeHtml(s)}</option>`).join('');
      // if previously selected source no longer exists, reset
      if (current && !sources.includes(current)) {
        sel.value = '';
        document.getElementById('delete-source').style.display = 'none';
      }
    });
}
```

- [ ] **Step 3: Update loadQuestions() to include source_file**

Replace the existing `loadQuestions` function:

```javascript
function loadQuestions() {
  const keyword = document.getElementById('search')?.value || '';
  const difficulty = document.getElementById('filter-difficulty')?.value || '';
  const source = document.getElementById('filter-source')?.value || '';
  fetch(`/api/questions?keyword=${encodeURIComponent(keyword)}&difficulty=${encodeURIComponent(difficulty)}&source_file=${encodeURIComponent(source)}`)
    .then(r => r.json())
    .then(renderQuestions);
}
```

- [ ] **Step 4: Add event handlers in DOMContentLoaded**

Inside the `if (document.getElementById('questions-body'))` block in `DOMContentLoaded`, add after the existing event listener registrations:

```javascript
    loadSourceFiles();

    document.getElementById('filter-source')?.addEventListener('change', function () {
      const val = this.value;
      const btn = document.getElementById('delete-source');
      if (btn) btn.style.display = val ? 'inline-block' : 'none';
      loadQuestions();
    });

    document.getElementById('delete-source')?.addEventListener('click', function () {
      const source = document.getElementById('filter-source')?.value;
      if (!source) return;
      const rows = document.querySelectorAll('#questions-body tr');
      const count = rows.length;
      if (!confirm(`確定刪除「${source}」的所有 ${count} 題？此操作無法復原。`)) return;
      fetch(`/api/questions/by-source?source_file=${encodeURIComponent(source)}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
          loadSourceFiles();
          loadQuestions();
        })
        .catch(() => alert('刪除失敗，請重試'));
    });
```

- [ ] **Step 5: Smoke test manually**

Start the server and open `http://127.0.0.1:5000/questions`:

```bash
python app.py
```

- Verify "所有來源" dropdown appears and is populated with source file names
- Select a source → table filters to only that source's questions; red delete button appears
- Click delete button → confirmation dialog shows source name and count → confirm → questions removed, dropdown updated, table refreshed
- Switch back to "所有來源" → delete button hides, all questions shown

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: 40 tests pass (1 pre-existing failure `test_export_word_no_questions_returns_400` unrelated to this feature)

- [ ] **Step 7: Commit**

```bash
git add templates/questions.html static/main.js
git commit -m "feat: add source file filter and batch delete to questions page"
```
