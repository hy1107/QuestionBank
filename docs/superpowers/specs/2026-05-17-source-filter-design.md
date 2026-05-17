# 來源檔案篩選與批次刪除 — 系統設計文件

**日期：** 2026-05-17  
**版本：** v1.0  
**基於：** 題庫密室 v1.0（`docs/superpowers/specs/2026-05-15-question-bank-design.md`）

---

## 1. 功能概述

在題庫管理頁（`/questions`）新增「來源檔案」下拉篩選器，讓使用者可以按匯入的 Excel 檔名篩選題目，並在選定來源後一次刪除該來源的所有題目。

**功能範圍：**
- 來源檔案下拉篩選（動態從 DB 載入）
- 按來源篩選後顯示對應題目
- 選定來源時顯示「刪除此來源所有題目」按鈕，批次刪除後重整列表與下拉選單

---

## 2. 技術方案

沿用現有 AJAX 模式：前端呼叫 REST API，`main.js` 處理互動邏輯，不新增頁面。

---

## 3. 後端變更

### 3.1 `db.py` 新增函式

```python
def get_source_files(db_path=None)
    # SELECT DISTINCT source_file FROM questions WHERE source_file != '' ORDER BY source_file
    # Returns: ['file_a.xlsx', 'file_b.xlsx', ...]

def delete_questions_by_source(db_path=None, source_file=None)
    # DELETE FROM questions WHERE source_file = ?
    # Returns: number of deleted rows (conn.execute(...).rowcount)
```

### 3.2 `db.py` 修改 `get_all_questions()`

在現有篩選條件中新增 `source_file` 支援：

```python
if filters.get('source_file'):
    clauses.append('source_file = ?')
    params.append(filters['source_file'])
```

### 3.3 `app.py` 新增路由

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/source-files` | GET | 回傳所有不重複的來源檔名清單（JSON array） |
| `/api/questions/by-source` | DELETE | 刪除指定來源的所有題目，回傳 `{"deleted": N}` |

`/api/questions` GET 新增讀取 `source_file` query 參數並傳入 `get_all_questions()` 的 filters。

---

## 4. 前端變更

### 4.1 `templates/questions.html`

工具列新增來源檔案下拉選單與刪除按鈕：

```html
<select id="filter-source">
  <option value="">所有來源</option>
</select>
<button id="delete-source" class="btn" style="background:#e74c3c;display:none">
  刪除此來源所有題目
</button>
```

### 4.2 `static/main.js`

**初始化：** 頁面載入時呼叫 `loadSourceFiles()` 填充 `#filter-source`。

**`loadSourceFiles()`：**
- `GET /api/source-files`
- 清空並重建 `#filter-source` 選項（保留「所有來源」為第一項）
- 若目前選中的來源不在新清單中，重設為「所有來源」

**`#filter-source` change 事件：**
- 呼叫 `loadQuestions()`（`source_file` 篩選條件已包含在內）
- 若選值非空，顯示 `#delete-source`；否則隱藏

**`#delete-source` click 事件：**
- 取得目前來源名稱與題目數量（從已載入的題目列表計算）
- `confirm('確定刪除「{source}」的所有 {N} 題？此操作無法復原。')`
- 確認後：`DELETE /api/questions/by-source?source_file={source}`
- 成功後：呼叫 `loadSourceFiles()`（會觸發重設選單）、`loadQuestions()`

**`loadQuestions()` 修改：**
新增從 `#filter-source` 讀取 `source_file` 並加入 fetch URL。

---

## 5. 不在本版本範圍內

- 重新命名來源檔案
- 將某來源的題目移轉到另一來源
- 來源層級的統計資訊（題目數、難度分布等）
