const API = {
    create: '/api/create',
    status: (id) => `/api/status/${id}`,
    videos: '/api/videos',
    delete: (id) => `/api/delete/${id}`,
    download: (id) => `/api/download/${id}`
};

document.getElementById('generateBtn').addEventListener('click', async () => {
    const prompt = document.getElementById('prompt').value.trim();
    const duration = document.getElementById('duration').value;
    const video_type = document.getElementById('videoType').value;
    
    if (!prompt) return alert('Please enter a prompt');
    
    const res = await fetch(API.create, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt, duration: parseInt(duration), video_type})
    });
    
    const data = await res.json();
    if (data.job_id) {
        document.getElementById('progressBox').style.display = 'block';
        pollJob(data.job_id);
    }
});

async function pollJob(jobId) {
    const interval = setInterval(async () => {
        const res = await fetch(API.status(jobId));
        const job = await res.json();
        
        document.getElementById('progressFill').style.width = job.progress + '%';
        document.getElementById('progressText').textContent = `${job.status} (${job.progress}%)`;
        
        if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval);
            loadVideos();
            document.getElementById('prompt').value = '';
            setTimeout(() => {
                document.getElementById('progressBox').style.display = 'none';
            }, 3000);
        }
    }, 1500);
}

async function loadVideos() {
    const res = await fetch(API.videos);
    const videos = await res.json();
    const tbody = document.getElementById('videoRows');
    tbody.innerHTML = '';
    
    videos.forEach(v => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${esc(v.prompt?.substring(0, 50) || '')}</td>
            <td>${v.video_type}</td>
            <td>${v.duration}s</td>
            <td><span class="status-${v.status}">${v.status}</span></td>
            <td>
                ${v.status === 'completed' ? `<a href="${API.download(v.id)}" class="btn-sm btn-download">⬇️</a>` : ''}
                <button class="btn-sm btn-delete" onclick="deleteVideo('${v.id}')">🗑️</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

async function deleteVideo(id) {
    if (!confirm('Delete this video?')) return;
    await fetch(API.delete(id), {method: 'DELETE'});
    loadVideos();
}

function esc(s) {
    return s?.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') || '';
}

loadVideos();