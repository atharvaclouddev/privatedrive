let state = {
    local_base: '',
    local_drive: '',
    public_base: null,
    public_drive: null,
    active_drive: '',
    username: 'admin',
    password: '',
    storage_dir: ''
};

document.addEventListener('DOMContentLoaded', () => {
    init();
    setupDropZone();
});

async function init() {
    await fetchStatus();
    fetchFiles();
    fetchNotes();

    // Poll status periodically until tunnel is ready
    setInterval(async () => {
        if (!state.public_drive) {
            await fetchStatus();
        }
    }, 3000);
}

// ----------------- Status & Credentials -----------------

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        state.local_base = data.local_base;
        state.local_drive = data.local_drive;
        state.public_base = data.public_base;
        state.public_drive = data.public_drive;
        state.username = data.username;
        state.password = data.password;
        state.storage_dir = data.storage_dir;

        // Choose best drive URL (public if available, else local)
        state.active_drive = data.public_drive ? data.public_drive : data.local_drive;

        document.getElementById('activeDriveUrl').innerText = state.active_drive;
        document.getElementById('credUsername').innerText = state.username;
        document.getElementById('credPassword').innerText = state.password;
        document.getElementById('storagePathLabel').innerText = state.storage_dir;

        // Update Windows & Mac Command Box
        const winCmd = `net use Z: "${state.active_drive}" /user:${state.username} ${state.password} /persistent:yes`;
        document.getElementById('winCliCommand').innerText = winCmd;
        document.getElementById('guideWinUrl').innerText = state.active_drive;
        document.getElementById('guideWinUser').innerText = state.username;
        const macEl = document.getElementById('guideMacUrl');
        if (macEl) macEl.innerText = state.active_drive;

    } catch (e) {
        console.error('Error fetching status', e);
    }
}

// ----------------- Guide Tab Switching -----------------

function switchGuide(type, btn) {
    document.querySelectorAll('.guide-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.guide-tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`guide-${type}`).classList.add('active');
    btn.classList.add('active');
}

// ----------------- File Manager -----------------

async function fetchFiles() {
    try {
        const res = await fetch('/api/files');
        const data = await res.json();
        renderFiles(data.files || []);
    } catch (e) {
        console.error('Error loading files', e);
    }
}

function renderFiles(files) {
    const list = document.getElementById('fileList');
    if (files.length === 0) {
        list.innerHTML = `<div class="empty-state">No files in shared storage. Drag & drop files above or copy into Drive Z:</div>`;
        return;
    }

    list.innerHTML = files.map(f => `
        <div class="file-row">
            <div class="file-info">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#60a5fa" stroke-width="2">
                    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                    <polyline points="13 2 13 9 20 9"></polyline>
                </svg>
                <div>
                    <div class="file-name">${escapeHtml(f.name)}</div>
                    <div class="subtle-text">${f.size_formatted} • ${f.modified}</div>
                </div>
            </div>
            <div class="file-actions">
                <a href="/api/download/${encodeURIComponent(f.name)}" class="btn-secondary btn-sm">Download</a>
                <button class="btn-danger btn-sm" onclick="deleteFile('${escapeHtml(f.name)}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function setupDropZone() {
    const zone = document.getElementById('dropZone');
    ['dragenter', 'dragover'].forEach(n => zone.addEventListener(n, (e) => { e.preventDefault(); zone.style.borderColor = 'var(--primary)'; }));
    ['dragleave', 'drop'].forEach(n => zone.addEventListener(n, (e) => { e.preventDefault(); zone.style.borderColor = 'var(--border)'; }));
    zone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
    });
}

async function handleUpload(files) {
    const fd = new FormData();
    for (let f of files) fd.append('files', f);

    showToast(`Uploading ${files.length} file(s)...`);
    try {
        const res = await fetch('/api/upload', { method: 'POST', body: fd });
        if (res.ok) {
            showToast('Files uploaded successfully! Visible in Drive Z: immediately.');
            fetchFiles();
        } else {
            showToast('Upload failed');
        }
    } catch (e) {
        showToast('Upload connection error');
    }
}

async function deleteFile(name) {
    if (!confirm(`Delete ${name}?`)) return;
    try {
        const res = await fetch(`/api/files/${encodeURIComponent(name)}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('File deleted');
            fetchFiles();
        }
    } catch (e) {
        showToast('Failed to delete');
    }
}

// ----------------- Shared Clipboard / Notes -----------------

async function fetchNotes() {
    try {
        const res = await fetch('/api/notes');
        const data = await res.json();
        renderNotes(data.notes || []);
    } catch (e) {
        console.error(e);
    }
}

function renderNotes(notes) {
    const cont = document.getElementById('notesContainer');
    if (notes.length === 0) {
        cont.innerHTML = `<div class="subtle-text" style="padding: 10px 0;">No clipboard notes shared yet.</div>`;
        return;
    }
    cont.innerHTML = notes.map(n => `
        <div class="note-row">
            <div>
                <div style="font-weight: 500;">${escapeHtml(n.content)}</div>
                <div class="subtle-text">${n.created_at}</div>
            </div>
            <div style="display: flex; gap: 6px;">
                <button class="btn-secondary btn-sm" onclick="copyText('${escapeHtmlForJs(n.content)}', 'Copied!')">Copy</button>
                <button class="btn-danger btn-sm" onclick="deleteNote('${n.id}')">&times;</button>
            </div>
        </div>
    `).join('');
}

async function submitNote() {
    const input = document.getElementById('noteInput');
    const val = input.value.trim();
    if (!val) return;

    try {
        const res = await fetch('/api/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: val })
        });
        if (res.ok) {
            input.value = '';
            showToast('Note synced!');
            fetchNotes();
        }
    } catch (e) {
        showToast('Failed to sync note');
    }
}

async function deleteNote(id) {
    try {
        await fetch(`/api/notes?id=${id}`, { method: 'DELETE' });
        fetchNotes();
    } catch (e) {}
}

// ----------------- QR Code Modal -----------------

function openQrModal() {
    const modal = document.getElementById('qrModal');
    const qrBox = document.getElementById('qrContainer');
    const label = document.getElementById('qrUrlLabel');

    const targetUrl = state.public_base || state.local_base;
    label.innerText = targetUrl;
    qrBox.innerHTML = '';

    new QRCode(qrBox, {
        text: targetUrl,
        width: 200,
        height: 200,
        colorDark: "#000",
        colorLight: "#fff",
        correctLevel: QRCode.CorrectLevel.M
    });

    modal.classList.remove('hidden');
}

function closeQrModal(e) {
    if (!e || e.target.id === 'qrModal' || e.target.classList.contains('btn-close')) {
        document.getElementById('qrModal').classList.add('hidden');
    }
}

// ----------------- Helpers -----------------

function copyText(text, msg, btnElement) {
    if (!text) return;
    const onSuccess = () => {
        showToast(msg || 'Copied to clipboard!');
        if (btnElement) {
            const originalHTML = btnElement.innerHTML;
            btnElement.innerHTML = `✓ Copied!`;
            btnElement.style.color = 'var(--accent)';
            setTimeout(() => {
                btnElement.innerHTML = originalHTML;
                btnElement.style.color = '';
            }, 1800);
        }
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onSuccess).catch(() => fallbackCopy(text, onSuccess));
    } else {
        fallbackCopy(text, onSuccess);
    }
}

function fallbackCopy(text, cb) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    if (cb) cb();
}

function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.remove('hidden');
    setTimeout(() => t.classList.add('hidden'), 3000);
}

async function handleLogout() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
}

function escapeHtml(t) {
    const d = document.createElement('div');
    d.innerText = t || '';
    return d.innerHTML;
}

function escapeHtmlForJs(t) {
    return (t || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}
