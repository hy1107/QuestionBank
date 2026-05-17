function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Questions page
function loadQuestions() {
  const keyword = document.getElementById('search')?.value || '';
  const difficulty = document.getElementById('filter-difficulty')?.value || '';
  const source = document.getElementById('filter-source')?.value || '';
  fetch(`/api/questions?keyword=${encodeURIComponent(keyword)}&difficulty=${encodeURIComponent(difficulty)}&source_file=${encodeURIComponent(source)}`)
    .then(r => r.json())
    .then(renderQuestions);
}

function loadSourceFiles() {
  fetch('/api/source-files')
    .then(r => r.json())
    .then(sources => {
      const sel = document.getElementById('filter-source');
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = '<option value="">所有來源</option>' +
        sources.map(s => `<option value="${escapeHtml(s)}"${s === current ? ' selected' : ''}>${escapeHtml(s)}</option>`).join('');
      if (current && !sources.includes(current)) {
        sel.value = '';
        document.getElementById('delete-source').style.display = 'none';
      }
    });
}

function renderQuestions(questions) {
  const tbody = document.getElementById('questions-body');
  if (!tbody) return;
  tbody.innerHTML = questions.map(q => `
    <tr>
      <td><input type="checkbox" class="q-check" value="${q.id}"></td>
      <td>${escapeHtml(q.original_no)}</td>
      <td title="${escapeHtml(q.question)}">${escapeHtml(q.question.substring(0, 50))}${q.question.length > 50 ? '...' : ''}</td>
      <td>${escapeHtml(q.answer)}</td>
      <td>
        <select onchange="updateField(${q.id}, 'difficulty', this.value)">
          ${['easy','medium','hard'].map(d => `<option value="${d}" ${q.difficulty===d?'selected':''}>${{easy:'簡單',medium:'中等',hard:'困難'}[d]}</option>`).join('')}
        </select>
      </td>
      <td><input type="text" value="${escapeHtml(q.subject||'')}" data-original="${escapeHtml(q.subject||'')}" placeholder="科目" onblur="if(this.value!==this.dataset.original){updateField(${q.id},'subject',this.value);this.dataset.original=this.value;}" style="width:80px"></td>
      <td><button onclick="deleteQuestion(${q.id})" class="btn" style="background:#e74c3c;padding:.25rem .6rem;font-size:.8rem">刪除</button></td>
    </tr>
  `).join('');
  updateSelectedCount();
}

function updateField(id, field, value) {
  fetch(`/api/questions/${id}`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({[field]: value})
  }).catch(() => alert('儲存失敗，請重試'));
}

function deleteQuestion(id) {
  if (!confirm('確定刪除這題？')) return;
  fetch(`/api/questions/${id}`, {method: 'DELETE'})
    .then(() => loadQuestions())
    .catch(() => alert('刪除失敗，請重試'));
}

function updateSelectedCount() {
  const count = document.querySelectorAll('.q-check:checked').length;
  const el = document.getElementById('selected-count');
  if (el) el.textContent = count;
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('questions-body')) {
    loadQuestions();
    document.getElementById('search')?.addEventListener('input', loadQuestions);
    document.getElementById('filter-difficulty')?.addEventListener('change', loadQuestions);
    document.getElementById('select-all')?.addEventListener('change', e => {
      document.querySelectorAll('.q-check').forEach(c => c.checked = e.target.checked);
      updateSelectedCount();
    });
    document.getElementById('questions-body')?.addEventListener('change', e => {
      if (e.target.classList.contains('q-check')) updateSelectedCount();
    });

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
  }

  // Export page
  const previewBtn = document.getElementById('preview-btn');
  const downloadBtn = document.getElementById('download-btn');
  if (previewBtn) {
    previewBtn.addEventListener('click', () => {
      const form = document.getElementById('export-form');
      const params = getExportParams(form);
      fetch('/api/questions?' + new URLSearchParams({
        subject: params.subject || '',
        difficulty: params.difficulty || '',
        no_from: params.no_from || '',
        no_to: params.no_to || '',
      }))
        .then(r => r.json())
        .then(questions => {
          let result = params.order === 'random'
            ? questions.sort(() => Math.random() - 0.5)
            : questions;
          if (params.count) result = result.slice(0, parseInt(params.count));
          document.getElementById('preview-count').textContent = result.length;
          document.getElementById('preview-list').innerHTML =
            result.map(q => `<li>${escapeHtml(q.original_no)}. ${escapeHtml(q.question.substring(0, 60))}</li>`).join('');
          document.getElementById('preview-section').style.display = 'block';
          downloadBtn._questions = result;
        });
    });

    downloadBtn?.addEventListener('click', () => {
      const form = document.getElementById('export-form');
      const params = getExportParams(form);
      const questions = downloadBtn._questions || [];
      fetch('/export/download', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          ids: questions.map(q => q.id),
          format: params.format,
          show_answers: params.show_answers,
        })
      })
        .then(r => r.json())
        .then(data => { window.location.href = data.download_url; });
    });
  }
});

function getExportParams(form) {
  const fd = new FormData(form);
  return {
    count: fd.get('count'),
    no_from: fd.get('no_from'),
    no_to: fd.get('no_to'),
    subject: fd.get('subject'),
    difficulty: fd.get('difficulty'),
    order: fd.get('order'),
    format: fd.get('format'),
    show_answers: fd.get('show_answers') === 'on',
  };
}
