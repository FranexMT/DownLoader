// main.js - Enhanced Frontend logic for Ethereal Downloader

// Sound System (Web Audio API)
const soundManager = {
    audioCtx: null,
    enabled: false,

    async init() {
        if (!this.audioCtx) {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        const config = await eel.get_config()();
        this.enabled = config.sound_enabled || false;
    },

    setEnable(val) { this.enabled = val; },

    async play(type) {
        if (!this.enabled || !this.audioCtx) return;
        if (this.audioCtx.state === 'suspended') {
            await this.audioCtx.resume();
        }

        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        const now = this.audioCtx.currentTime;

        switch (type) {
            case 'pop': // URL paste / button click
                osc.type = 'sine';
                osc.frequency.setValueAtTime(600, now);
                osc.frequency.exponentialRampToValueAtTime(100, now + 0.1);
                gain.gain.setValueAtTime(0.2, now);
                gain.gain.linearRampToValueAtTime(0, now + 0.1);
                osc.start(now);
                osc.stop(now + 0.1);
                break;
            case 'success': // Download complete
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, now); // A4
                osc.frequency.exponentialRampToValueAtTime(880, now + 0.1); // A5
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
                osc.start(now);
                osc.stop(now + 0.5);
                break;
            case 'error': // Something went wrong
                osc.type = 'square';
                osc.frequency.setValueAtTime(150, now);
                osc.frequency.linearRampToValueAtTime(50, now + 0.2);
                gain.gain.setValueAtTime(0.05, now);
                gain.gain.linearRampToValueAtTime(0, now + 0.2);
                osc.start(now);
                osc.stop(now + 0.2);
                break;
            case 'intro': // Welcome chime
                this.playSequence([523.25, 659.25, 783.99, 1046.50]); // C chord sweep
                break;
        }
    },

    playSequence(freqs) {
        const now = this.audioCtx.currentTime;
        freqs.forEach((f, i) => {
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);
            osc.frequency.setValueAtTime(f, now + i * 0.1);
            gain.gain.setValueAtTime(0, now + i * 0.1);
            gain.gain.linearRampToValueAtTime(0.1, now + i * 0.1 + 0.05);
            gain.gain.linearRampToValueAtTime(0, now + i * 0.1 + 0.2);
            osc.start(now + i * 0.1);
            osc.stop(now + i * 0.1 + 0.3);
        });
    }
};

// Helper to format bytes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function calculateETA(downloaded, total, speed) {
    if (speed <= 0 || downloaded >= total) return "Calculating...";
    const remaining = total - downloaded;
    const seconds = remaining / speed;

    if (seconds < 60) return `${Math.ceil(seconds)}s remains`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.ceil(seconds % 60)}s remains`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m remains`;
}

// Notifications System
function showNotification(message, type = 'info', duration = 4000) {
    const container = document.getElementById('notifications-container');
    const id = 'notif-' + Date.now();
    const colors = {
        success: 'bg-green-500/90 border-green-400',
        error: 'bg-red-500/90 border-red-400',
        warning: 'bg-yellow-500/90 border-yellow-400',
        info: 'bg-secondary/90 border-secondary'
    };
    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };

    const el = document.createElement('div');
    el.id = id;
    el.className = `${colors[type]} glass-panel backdrop-blur-2xl rounded-2xl p-4 shadow-2xl transform translate-x-full opacity-0 transition-all duration-500 flex items-center gap-4 border border-white/10`;
    el.innerHTML = `
        <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center border border-white/10">
            <span class="material-symbols-outlined text-white">${icons[type]}</span>
        </div>
        <div class="flex-grow">
            <p class="text-white text-sm font-bold">${message}</p>
        </div>
        <button onclick="dismissNotification('${id}')" class="p-2 glass-button rounded-lg text-white/50 hover:text-white">
            <span class="material-symbols-outlined text-sm">close</span>
        </button>
    `;
    container.appendChild(el);

    requestAnimationFrame(() => {
        el.classList.remove('translate-x-full', 'opacity-0');
    });

    if (duration > 0) {
        setTimeout(() => dismissNotification(id), duration);
    }
    return id;
}

function dismissNotification(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => el.remove(), 300);
    }
}

// Global state
let currentView = 'dashboard';
let tasks = {};
let historyData = [];
let speedHistory = new Array(20).fill(0);
let historyFilter = 'all';
let historySearch = '';

// DOM Elements
const sections = {
    dashboard: document.getElementById('main-dashboard'),
    tasks: document.getElementById('main-tasks'),
    history: document.getElementById('main-history'),
    settings: document.getElementById('main-settings')
};

const navButtons = {
    dashboard: document.getElementById('nav-dashboard'),
    tasks: document.getElementById('nav-downloads'),
    history: document.getElementById('nav-history'),
    settings: document.getElementById('nav-settings')
};

const tasksContainer = document.getElementById('tasks-container');
const historyContainer = document.getElementById('history-container');
const downloadBtn = document.getElementById('download-btn');
const urlInput = document.getElementById('url-input');
const urlInputBatch = document.getElementById('url-input-batch');
const batchToggle = document.getElementById('batch-toggle');

// Fetch local IP for mobile sync
async function initNetworking() {
    try {
        const ip = await eel.get_local_ip()();
        const ipDisplay = document.getElementById('ip-display');
        if (ipDisplay) ipDisplay.textContent = `IP: ${ip}`;
    } catch (e) {
        console.error('Failed to get local IP:', e);
    }
}
initNetworking();

// Legal Modal Logic
const legalModal = document.getElementById('legal-modal');
const showLegalBtn = document.getElementById('show-legal');
const closeLegalBtn = document.getElementById('close-legal');
const acceptLegalBtn = document.getElementById('accept-legal');
const legalContent = document.getElementById('legal-content');

if (showLegalBtn) {
    showLegalBtn.onclick = async () => {
        legalModal.classList.remove('hidden');
        const notice = await eel.get_legal_notice()();
        legalContent.innerHTML = notice.replace(/\n/g, '<br>');
    };
}

if (closeLegalBtn) closeLegalBtn.onclick = () => legalModal.classList.add('hidden');
if (acceptLegalBtn) acceptLegalBtn.onclick = () => legalModal.classList.add('hidden');

// Close modal on outside click
window.onclick = (event) => {
    if (event.target == legalModal) legalModal.classList.add('hidden');
};
const pendingCount = document.getElementById('pending-count');
const totalSpeed = document.getElementById('total-speed');
const breadcrumb = document.getElementById('breadcrumb');

// Navigation - Global function
window.switchView = function (view) {
    console.log('Switching to view:', view);
    
    // Hide all sections
    Object.keys(sections).forEach(k => {
        if (sections[k]) {
            sections[k].classList.add('hidden');
        }
    });
    
    // Show selected section
    if (sections[view]) {
        sections[view].classList.remove('hidden');
    }
    
    // Update nav buttons
    Object.keys(navButtons).forEach(k => {
        if (navButtons[k]) {
            const isSelected = k === view;
            navButtons[k].classList.toggle('text-secondary', isSelected);
            navButtons[k].classList.toggle('bg-secondary/10', isSelected);
            navButtons[k].classList.toggle('scale-105', isSelected);
            navButtons[k].classList.toggle('border-r-2', isSelected);
            navButtons[k].classList.toggle('border-secondary', isSelected);
            navButtons[k].classList.toggle('text-zinc-500', !isSelected);
            navButtons[k].classList.toggle('hover:text-zinc-300', !isSelected);
            navButtons[k].classList.toggle('hover:bg-white/5', !isSelected);
        }
    });

    currentView = view;
    if (breadcrumb) breadcrumb.textContent = `System / ${view.charAt(0).toUpperCase() + view.slice(1)}`;

    if (view === 'history') refreshHistory();
    if (view === 'settings') loadSettings();
    if (view === 'dashboard') refreshDashboard();
};

// Event Listeners - Initialize sections and set default view
function initNavigation() {
    console.log('Initializing navigation');

    // Make sure all sections are hidden initially
    Object.values(sections).forEach(section => {
        if (section) section.classList.add('hidden');
    });

    // Show dashboard by default
    window.switchView('dashboard');

    // Batch toggle
    const urlInputSingle = document.getElementById('url-input');
    const detectBtn = document.getElementById('detect-btn');

    if (batchToggle) {
        batchToggle.onchange = () => {
            const isBatch = batchToggle.checked;
            urlInputSingle.classList.toggle('hidden', isBatch);
            urlInputBatch.classList.toggle('hidden', !isBatch);
            if (detectBtn) detectBtn.classList.toggle('hidden', isBatch);
        };
    }

    // Engine status check
    checkEngine();
}

async function checkEngine() {
    try {
        const status = await eel.check_engine_status()();
        const ffmpegEl = document.getElementById('ffmpeg-status');
        if (ffmpegEl) {
            if (status.ffmpeg) {
                ffmpegEl.className = "flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20";
                ffmpegEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-green-500"></span><span class="text-[10px] font-black uppercase text-green-500">Instalado</span>`;
            } else {
                ffmpegEl.className = "flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20";
                ffmpegEl.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-red-500"></span><span class="text-[10px] font-black uppercase text-red-500">No detectado</span>`;
            }
        }
    } catch (e) { console.error("Engine check failed", e); }
}

downloadBtn.onclick = async () => {
    try {
        const isBatch = batchToggle && batchToggle.checked;
        const urlInputCurrent = isBatch ? urlInputBatch : urlInput;
        const urlStr = urlInputCurrent.value.trim();
        if (!urlStr) {
            showNotification('Por favor, ingresa un enlace.', 'warning');
            return;
        }

        console.log('Initiating download for:', urlStr, 'Batch mode:', !!isBatch);

        const qualitySelect = document.getElementById('quality-select');
        const formatSelect = document.getElementById('format-select');
        const customPathInput = document.getElementById('custom-path');
        const customSpeedInput = document.getElementById('custom-speed');
        const quality = qualitySelect ? qualitySelect.value : 'best';
        const fileFormat = formatSelect && formatSelect.value ? formatSelect.value : null;
        const customPath = customPathInput && customPathInput.value.trim() ? customPathInput.value.trim() : null;
        const customSpeed = customSpeedInput && customSpeedInput.value ? parseInt(customSpeedInput.value) : 0;

        downloadBtn.disabled = true;
        downloadBtn.textContent = 'PROCESANDO...';
        soundManager.play('pop');

        const videoTitle = document.getElementById('video-title')?.textContent || null;
        const videoThumb = document.getElementById('video-thumb')?.src || null;

        const success = await eel.add_download_with_options(urlStr, quality, fileFormat, customPath, customSpeed, videoTitle, videoThumb)();

        if (success) {
            showNotification('Descarga añadida a la cola.', 'success');
            urlInput.value = '';
            urlInputBatch.value = '';
            if (customPathInput) customPathInput.value = '';
            if (customSpeedInput) customSpeedInput.value = '0';
            if (qualitySelect) qualitySelect.value = 'best';
            if (formatSelect) formatSelect.value = '';
            document.getElementById('quality-options').classList.add('hidden');
            window.switchView('downloads');
            refreshHistory();
        } else {
            showNotification('Error al añadir descarga. Verifica el enlace.', 'error');
        }

    } catch (e) {
        console.error('Download click handler error:', e);
        showNotification('Error crítico en el sistema de descarga.', 'error');
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = `<span class="material-symbols-outlined" data-icon="download">download</span> Execute Task`;
    }
};

// Browse destination
const browseDestBtn = document.getElementById('browse-dest-btn');
if (browseDestBtn) {
    browseDestBtn.onclick = async () => {
        const path = await eel.browse_folder()();
        if (path) {
            document.getElementById('custom-path').value = path;
        }
    };
}

// Clear history
const clearHistoryBtn = document.getElementById('clear-history-btn');
if (clearHistoryBtn) {
    clearHistoryBtn.onclick = async () => {
        if (confirm('Are you sure you want to clear all history?')) {
            await eel.clear_history()();
            refreshDashboard();
        }
    };
}

// URL Detection
const detectBtn = document.getElementById('detect-btn');

async function detectUrl() {
    const url = urlInput.value.trim();
    const qualityOptions = document.getElementById('quality-options');
    const urlTypeBadge = document.getElementById('url-type-badge');
    const videoInfo = document.getElementById('video-info');

    if (!url) {
        qualityOptions.classList.add('hidden');
        urlTypeBadge.textContent = 'Enter a URL';
        urlTypeBadge.className = 'px-2 py-0.5 rounded bg-zinc-700 text-zinc-400';
        videoInfo.classList.add('hidden');
        return;
    }

    try {
        const isSocial = await eel.check_url_type(url)();

        if (isSocial) {
            qualityOptions.classList.remove('hidden');
            urlTypeBadge.textContent = 'Social Media';
            urlTypeBadge.className = 'px-2 py-0.5 rounded bg-tertiary/20 text-tertiary';

            // Get video info
            const info = await eel.get_available_formats(url)();
            if (info && !info.error) {
                document.getElementById('video-title').textContent = info.info.title || 'Unknown';
                document.getElementById('video-uploader').textContent = info.info.uploader || '';
                const duration = info.info.duration;
                if (duration) {
                    const mins = Math.floor(duration / 60);
                    const secs = duration % 60;
                    document.getElementById('video-duration').textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
                }
                const thumb = document.getElementById('video-thumb');
                if (info.info.thumbnail) {
                    thumb.src = info.info.thumbnail;
                }
                videoInfo.classList.remove('hidden');
            }
        } else {
            qualityOptions.classList.add('hidden');
            urlTypeBadge.textContent = 'Direct Download';
            urlTypeBadge.className = 'px-2 py-0.5 rounded bg-secondary/20 text-secondary';
            videoInfo.classList.add('hidden');
        }
    } catch (e) {
        console.error('URL detection error:', e);
    }
}

urlInput.addEventListener('input', () => {
    clearTimeout(urlInput.detectTimeout);
    urlInput.detectTimeout = setTimeout(detectUrl, 500);
});

detectBtn.addEventListener('click', detectUrl);

// Expose functions to Python
eel.expose(update_tasks);
function update_tasks(newTasks, stats) {
    // Check for status changes to notify user
    Object.keys(newTasks).forEach(id => {
        const newTask = newTasks[id];
        const oldTask = tasks[id];

        if (newTask.status === 'COMPLETED' && (!oldTask || oldTask.status !== 'COMPLETED')) {
            soundManager.play('success');
            const name = newTask.title || newTask.filename || 'Descarga finalizada';
            showNotification(`Descarga terminada: ${name}`, 'success');
        } else if (newTask.status === 'FAILED' && (!oldTask || oldTask.status !== 'FAILED')) {
            soundManager.play('error');
            const name = newTask.title || newTask.filename || 'Archivo desconocido';
            showNotification(`Error en descarga: ${name}`, 'error');
        }
    });
    tasks = newTasks;
    renderTasks();
    updateStats(stats);

    // Global Badge logic
    const badge = document.getElementById('global-status-badge');
    const hasActive = Object.values(newTasks).some(t => t.status === 'DOWNLOADING');
    if (hasActive) {
        badge.classList.remove('opacity-0', 'scale-90');
        badge.classList.add('opacity-100', 'scale-100');
    } else {
        badge.classList.remove('opacity-100', 'scale-100');
        badge.classList.add('opacity-0', 'scale-90');
    }
}

eel.expose(update_history);
function update_history(newHistory) {
    historyData = newHistory;
    if (currentView === 'history') renderHistory();
}

// Rendering
function renderTasks() {
    const taskIds = Object.keys(tasks);
    pendingCount.textContent = taskIds.length.toString().padStart(2, '0');

    // Calculate total speed
    let speedSum = 0;
    let activeCount = 0;
    taskIds.forEach(id => {
        if (tasks[id].status === 'DOWNLOADING') {
            speedSum += tasks[id].speed;
            activeCount++;
        }
    });

    totalSpeed.textContent = `${formatBytes(speedSum)}/s`;
    document.getElementById('active-tasks-label').textContent = `${activeCount} Active Tasks`;

    // Speed Chart Update
    speedHistory.push(speedSum);
    speedHistory.shift();
    updateSpeedChart();

    // Only render if we are in downloads view
    if (currentView !== 'downloads') return;

    // Use a temporary fragment for performance if there are many tasks
    tasksContainer.innerHTML = '';
    taskIds.forEach(id => {
        const task = tasks[id];
        const taskEl = createTaskElement(task);
        tasksContainer.appendChild(taskEl);
    });
}

function updateSpeedChart() {
    const chart = document.getElementById('speed-chart');
    if (!chart) return;
    const path = chart.querySelector('path');
    const maxSpeed = Math.max(...speedHistory, 1024 * 1024); // at least 1MB for scale

    let d = "M0 100 ";
    speedHistory.forEach((speed, i) => {
        const x = (i / (speedHistory.length - 1)) * 100;
        const y = 100 - (speed / maxSpeed) * 80; // keep it in top 80%
        d += `L${x} ${y} `;
    });
    d += "L100 100 Z";
    path.setAttribute('d', d);
}

function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = "group relative glass-panel rounded-3xl p-6 transition-all duration-500 transform hover:scale-[1.02] border border-white/5 overflow-hidden";

    // Background highlight for cards
    const highlight = document.createElement('div');
    highlight.className = "absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none";
    div.appendChild(highlight);

    const sheen = document.createElement('div');
    sheen.className = "glass-sheen";
    div.appendChild(sheen);

    const innerContent = document.createElement('div');
    innerContent.className = "relative z-10";
    div.appendChild(innerContent);

    const isDownloading = task.status === 'DOWNLOADING';
    const isPaused = task.status === 'PAUSED';
    const progressColor = isPaused ? 'outline' : (task.status === 'COMPLETED' ? 'tertiary' : 'secondary');

    innerContent.innerHTML = `
        <div class="flex items-start justify-between mb-6">
            <div class="flex gap-5">
                <div class="relative w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-${progressColor}/30 transition-all duration-500 shadow-inner overflow-hidden">
                    ${task.thumbnail ? `<img src="${task.thumbnail}" class="w-full h-full object-cover">` :
            `<span class="material-symbols-outlined text-4xl group-hover:text-${progressColor} transition-colors">${getIcon(task.filename)}</span>`}
                </div>
                <div>
                    <h3 class="font-headline text-white text-xl font-bold leading-tight truncate max-w-md">${task.title || task.filename || 'Acquiring metadata...'}</h3>
                    <div class="flex items-center gap-3 mt-2">
                        <span class="text-[11px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded border border-white/5">${formatBytes(task.downloaded_size)} / ${formatBytes(task.total_size)}</span>
                        <div class="h-3 w-px bg-white/10"></div>
                        <span class="text-[11px] font-mono font-bold text-${progressColor} uppercase tracking-wider">${eta}</span>
                    </div>
                </div>
            </div>
            <div class="flex gap-2">
                ${isDownloading ?
            `<button onclick="eel.pause_task(${task.id})" class="w-12 h-12 glass-button rounded-xl flex items-center justify-center bg-white/5 text-zinc-400">
                        <span class="material-symbols-outlined">pause</span>
                    </button>` :
            (isPaused ?
                `<button onclick="eel.resume_task(${task.id})" class="w-12 h-12 glass-button rounded-xl flex items-center justify-center bg-secondary/20 text-secondary">
                            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">play_arrow</span>
                        </button>` : '')
        }
                <button onclick="eel.cancel_task(${task.id})" class="w-12 h-12 glass-button rounded-xl flex items-center justify-center bg-white/5 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-all">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        </div>
        <div class="relative pt-2">
            <div class="flex justify-between items-center mb-3">
                <div class="flex items-center gap-2">
                    <div class="px-3 py-1 rounded-full bg-${progressColor}/10 border border-${progressColor}/20 shadow-sm">
                        <span class="text-[10px] font-black uppercase tracking-widest text-${progressColor}">${task.progress.toFixed(1)}%</span>
                    </div>
                </div>
                <span class="text-[11px] font-mono text-zinc-500 bg-black/20 px-2 py-0.5 rounded">${formatBytes(task.speed)}/s</span>
            </div>
            <div class="h-2.5 w-full bg-black/40 rounded-full overflow-hidden border border-white/5">
                <div class="h-full bg-gradient-to-r from-${progressColor} to-${progressColor}/40 rounded-full relative transition-all duration-700 ease-out shadow-[0_0_15px_${progressColor}44]" style="width: ${task.progress}%">
                    ${isDownloading ? `<div class="absolute right-0 top-1/2 -translate-y-1/2 w-6 h-6 bg-${progressColor} blur-lg rounded-full animate-pulse"></div>` : ''}
                </div>
            </div>
        </div>
    `;
    return div;
}

function getIcon(filename) {
    if (!filename) return 'cloud_download';
    const ext = filename.split('.').pop().toLowerCase();
    const map = {
        'mp4': 'movie', 'mkv': 'movie', 'avi': 'movie', 'mov': 'movie',
        'mp3': 'music_note', 'wav': 'music_note', 'flac': 'music_note',
        'jpg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image',
        'zip': 'inventory_2', 'rar': 'inventory_2', '7z': 'inventory_2',
        'pdf': 'picture_as_pdf', 'doc': 'description', 'docx': 'description',
        'exe': 'terminal', 'msi': 'terminal'
    };
    return map[ext] || 'description';
}

function updateStats(stats) {
    if (!stats) return;
    document.getElementById('total-transferred-text').innerHTML = `${formatBytes(stats.total_bytes)}`;

    // License Badge Update
    const proBadge = document.getElementById('license-badge');
    const liteBadge = document.getElementById('lite-badge');
    if (stats.is_pro) {
        if (proBadge) proBadge.classList.remove('hidden');
        if (liteBadge) liteBadge.classList.add('hidden');
    } else {
        if (proBadge) proBadge.classList.add('hidden');
        if (liteBadge) liteBadge.classList.remove('hidden');
    }

    // Storage stats
    const usedPercent = (stats.total_bytes / (1024 * 1024 * 1024 * 500)) * 100; // Mock 500GB capacity
    const storageText = document.getElementById('storage-text');
    if (storageText) storageText.innerHTML = `${formatBytes(stats.total_bytes)} <span class="text-sm font-normal text-zinc-500">of 500GB</span>`;

    const storageBar = document.getElementById('storage-bar');
    if (storageBar) storageBar.style.width = `${Math.min(usedPercent, 100)}%`;

    // Sidebar update
    const sidebarPct = document.getElementById('sidebar-storage-pct');
    const sidebarBar = document.getElementById('sidebar-storage-bar');
    const sidebarText = document.getElementById('sidebar-storage-text');

    if (sidebarPct) sidebarPct.textContent = `${usedPercent.toFixed(1)}%`;
    if (sidebarBar) sidebarBar.style.width = `${Math.min(usedPercent, 100)}%`;
    if (sidebarText) sidebarText.textContent = `${formatBytes(stats.total_bytes)} sincronizado`;
}

// Settings
async function loadSettings() {
    try {
        const config = await eel.get_config()();
        document.getElementById('threads-slider').value = config.default_threads || 8;
        document.getElementById('threads-val').textContent = config.default_threads || 8;
        document.getElementById('path-input').value = config.default_download_path || '';
        document.getElementById('timeout-input').value = config.timeout || 60;
        
        // Load new settings
        if (document.getElementById('speed-input')) {
            document.getElementById('speed-input').value = config.max_speed_kbps || 0;
        }
        if (document.getElementById('checksum-select')) {
            document.getElementById('checksum-select').value = config.checksum_type || '';
        }
        
        document.getElementById('cookies-browser').value = config.cookies_browser || 'firefox';

        if (document.getElementById('max-concurrent')) {
            document.getElementById('max-concurrent').value = config.max_concurrent || 3;
        }
        
        if (document.getElementById('naming-template')) {
            document.getElementById('naming-template').value = config.naming_template || '%(title)s.%(ext)s';
        }
        if (document.getElementById('auto-subs-toggle')) {
            document.getElementById('auto-subs-toggle').checked = config.auto_subtitles || false;
        }
        if (document.getElementById('scheduler-toggle')) {
            document.getElementById('scheduler-toggle').checked = config.scheduler_enabled || false;
        }
        if (document.getElementById('scheduler-time')) {
            document.getElementById('scheduler-time').value = config.scheduler_time || '02:00';
        }
        
        // Just update the label to show saved color, don't change current theme
        const savedColor = config.accent_color || 'cyan';
        const label = document.getElementById('current-color-label');
        if (label) {
            label.textContent = `Saved: ${COLOR_NAMES[savedColor] || savedColor}`;
        }
    } catch (e) {
        console.error('Error loading settings:', e);
    }
}

const COLOR_NAMES = {
    'red': 'Red',
    'orange': 'Orange',
    'yellow': 'Yellow',
    'green': 'Green',
    'cyan': 'Cyan',
    'blue': 'Blue',
    'violet': 'Violet',
    'purple': 'Purple',
    'pink': 'Pink',
    'white': 'White'
};

const COLOR_RGB = {
    'red': { primary: '239, 68, 68', secondary: '185, 28, 28' },
    'orange': { primary: '249, 115, 22', secondary: '194, 65, 12' },
    'yellow': { primary: '234, 179, 8', secondary: '161, 98, 7' },
    'green': { primary: '34, 197, 94', secondary: '22, 101, 52' },
    'cyan': { primary: '0, 227, 253', secondary: '8, 145, 178' },
    'blue': { primary: '59, 130, 246', secondary: '30, 64, 175' },
    'violet': { primary: '139, 92, 246', secondary: '109, 40, 217' },
    'purple': { primary: '168, 85, 247', secondary: '126, 34, 206' },
    'pink': { primary: '236, 72, 153', secondary: '157, 11, 74' },
    'white': { primary: '255, 255, 255', secondary: '156, 163, 175' }
};

function applyColorTheme(color) {
    const html = document.documentElement;
    
    // Remove old color
    Object.keys(COLOR_NAMES).forEach(c => {
        html.removeAttribute('data-color');
    });
    
    // Apply new color
    html.setAttribute('data-color', color);
    
    // Update CSS variables
    const rgb = COLOR_RGB[color] || COLOR_RGB['cyan'];
    document.documentElement.style.setProperty('--primary-rgb', rgb.primary);
    document.documentElement.style.setProperty('--secondary-rgb', rgb.secondary);
    
    // Update color buttons
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.color === color) {
            btn.classList.add('active');
        }
    });
    
    // Update label
    const label = document.getElementById('current-color-label');
    if (label) {
        label.textContent = `Current: ${COLOR_NAMES[color] || color}`;
    }
    
    // Update gradient orbs with new colors
    updateOrbsColor(color);
}

function updateOrbsColor(color) {
    const colorMap = {
        'red': { primary: '#ef4444', secondary: '#dc2626' },
        'orange': { primary: '#f97316', secondary: '#ea580c' },
        'yellow': { primary: '#eab308', secondary: '#ca8a04' },
        'green': { primary: '#22c55e', secondary: '#16a34a' },
        'cyan': { primary: '#00e3fd', secondary: '#0891b2' },
        'blue': { primary: '#3b82f6', secondary: '#1d4ed8' },
        'violet': { primary: '#8b5cf6', secondary: '#6d28d9' },
        'purple': { primary: '#a855f7', secondary: '#7e22ce' },
        'pink': { primary: '#ec4899', secondary: '#db2777' },
        'white': { primary: '#ffffff', secondary: '#9ca3af' }
    };
    
    const orbs = document.querySelectorAll('.bg-orb');
    const colors = colorMap[color] || colorMap['cyan'];
    
    if (orbs[0]) orbs[0].style.backgroundColor = colors.primary + '25';
    if (orbs[1]) orbs[1].style.backgroundColor = colors.secondary + '15';
    if (orbs[2]) orbs[2].style.backgroundColor = colors.primary + '20';
}

// Initialize color picker buttons
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.color-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const color = btn.dataset.color;
            applyColorTheme(color);
            saveColorPreference(color);
        });
    });
});

function saveColorPreference(color) {
    const config = load_config_from_ui();
    config.accent_color = color;
    // Will be saved when user clicks save settings
}

function load_config_from_ui() {
    return {
        accent_color: document.documentElement.getAttribute('data-color') || 'cyan'
    };
}

// Removed activation logic as the app is now free.

document.getElementById('threads-slider').oninput = (e) => {
    document.getElementById('threads-val').textContent = e.target.value;
};

document.getElementById('save-settings').onclick = async () => {
    const threads = parseInt(document.getElementById('threads-slider').value);
    const path = document.getElementById('path-input').value;
    const timeout = parseInt(document.getElementById('timeout-input').value);
    const speed = parseInt(document.getElementById('speed-input')?.value || 0);
    const checksum = document.getElementById('checksum-select')?.value || null;
    const cookiesBrowser = document.getElementById('cookies-browser').value;
    const accentColor = document.documentElement.getAttribute('data-color') || 'cyan';
    const maxConcurrent = parseInt(document.getElementById('max-concurrent')?.value || 3);
    const notifications = document.getElementById('notifications-toggle')?.checked ?? true;
    const autoQuality = document.getElementById('auto-quality-toggle')?.checked ?? true;
    const sound = document.getElementById('sound-toggle')?.checked ?? false;
    const autoRetry = document.getElementById('auto-retry-toggle')?.checked ?? true;

    soundManager.setEnable(sound);

    const success = await eel.save_settings({
        default_threads: threads,
        default_download_path: path,
        timeout: timeout,
        max_speed_kbps: speed,
        checksum_type: checksum || null,
        cookies_browser: cookiesBrowser,
        accent_color: accentColor,
        max_concurrent: maxConcurrent,
        notifications_enabled: notifications,
        auto_quality: autoQuality,
        sound_enabled: sound,
        auto_retry: autoRetry,
        naming_template: document.getElementById('naming-template')?.value || '%(title)s.%(ext)s',
        auto_subtitles: document.getElementById('auto-subs-toggle')?.checked || false,
        scheduler_enabled: document.getElementById('scheduler-toggle')?.checked || false,
        scheduler_time: document.getElementById('scheduler-time')?.value || '02:00'
    })();

    if (success) {
        showNotification('Settings saved successfully!', 'success');
    } else {
        showNotification('Failed to save settings', 'error');
    }
};

document.getElementById('browse-btn').onclick = async () => {
    const path = await eel.browse_folder()();
    if (path) document.getElementById('path-input').value = path;
};

document.getElementById('reset-settings')?.addEventListener('click', async () => {
    if (confirm('Reset all settings to defaults?')) {
        const success = await eel.save_settings({
            default_threads: 8,
            default_download_path: '/home/' + (await eel.get_config()().then(c => c.default_download_path?.split('/')[2] || 'Downloads')) + '/Downloads',
            timeout: 60,
            cookies_browser: 'firefox',
            theme: 'dark',
            max_concurrent: 3,
            notifications_enabled: true,
            auto_quality: true,
            sound_enabled: false,
            auto_retry: true
        })();
        if (success) {
            loadSettings();
            showNotification('Settings reset to defaults', 'success');
        }
    }
});

// History functions
async function refreshHistory() {
    try {
        console.log('Refreshing history list');
        const response = await eel.get_history()();
        historyData = response.history || [];
        renderHistory();
    } catch (e) {
        console.error('History refresh error:', e);
    }
}

function renderHistory() {
    const container = document.getElementById('history-container');
    if (!container) return;

    let filtered = [...historyData];

    // Apply filter
    if (historyFilter === 'completed') {
        filtered = filtered.filter(h => h.status === 'COMPLETED');
    } else if (historyFilter === 'failed') {
        filtered = filtered.filter(h => h.status === 'FAILED');
    }

    // Apply search
    if (historySearch) {
        const search = historySearch.toLowerCase();
        filtered = filtered.filter(h =>
            (h.title && h.title.toLowerCase().includes(search)) ||
            (h.filename && h.filename.toLowerCase().includes(search)) ||
            (h.url && h.url.toLowerCase().includes(search))
        );
    }

    // Update stats
    const totalSize = historyData.reduce((sum, h) => sum + (h.total_size || 0), 0);
    const completedCount = historyData.filter(h => h.status === 'COMPLETED').length;
    const rate = historyData.length > 0 ? Math.round((completedCount / historyData.length) * 100) : 0;

    document.getElementById('hist-total').textContent = historyData.length;
    document.getElementById('hist-size').textContent = formatBytes(totalSize);
    document.getElementById('hist-rate').textContent = rate + '%';

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="glass-panel bg-surface-container/20 rounded-2xl p-12 border border-white/5 text-center">
                <span class="material-symbols-outlined text-6xl text-zinc-600">folder_open</span>
                <p class="text-zinc-500 mt-4">No downloads found</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    filtered.forEach(item => {
        const statusColor = item.status === 'COMPLETED' ? 'green' : (item.status === 'FAILED' ? 'red' : 'yellow');
        const statusIcon = item.status === 'COMPLETED' ? 'check_circle' : (item.status === 'FAILED' ? 'error' : 'pending');
        const fileType = item.filename ? item.filename.split('.').pop().toLowerCase() : 'file';

        const el = document.createElement('div');
        el.className = 'glass-panel rounded-2xl p-5 hover:bg-white/5 transition-all group overflow-hidden';
        el.innerHTML = `
            <div class="glass-sheen"></div>
            <div class="flex items-center justify-between relative z-10">
                <div class="flex items-center gap-5 flex-grow">
                    <div class="relative w-16 h-16 rounded-2xl bg-${statusColor}-500/10 flex items-center justify-center border border-${statusColor}-500/20 group-hover:border-${statusColor}-500/40 transition-colors overflow-hidden">
                        ${item.thumbnail ? `<img src="${item.thumbnail}" class="w-full h-full object-cover">` :
                `<span class="material-symbols-outlined text-2xl text-${statusColor}-400">${getFileIcon(fileType)}</span>`}
                    </div>
                    <div class="flex-grow min-w-0">
                        <h4 class="text-white font-bold text-sm truncate">${item.title || item.filename || 'Unknown'}</h4>
                        <div class="flex items-center gap-3 mt-1">
                            <span class="text-[11px] font-mono text-zinc-500">${formatBytes(item.total_size)}</span>
                            <div class="w-1 h-1 rounded-full bg-zinc-800"></div>
                            <span class="text-[10px] font-mono text-zinc-500">${new Date(item.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                    <div class="hidden md:flex items-center gap-8 mr-6">
                        <div class="text-center">
                            <span class="text-[10px] text-zinc-500 uppercase tracking-widest font-black">Size</span>
                            <p class="text-white font-mono text-sm mt-1">${formatBytes(item.total_size || 0)}</p>
                        </div>
                        <div class="text-center">
                            <span class="text-[10px] text-zinc-500 uppercase tracking-widest font-black">Status</span>
                            <div class="flex items-center gap-2 mt-1">
                                <span class="w-1.5 h-1.5 rounded-full bg-${statusColor}-400"></span>
                                <p class="text-${statusColor}-400 font-bold text-xs uppercase tracking-tighter">${item.status}</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-3 ml-4">
                    ${item.status === 'COMPLETED' ? `
                    <button onclick="openFile(${item.id})" class="w-10 h-10 glass-button rounded-xl flex items-center justify-center bg-white/5 text-zinc-400" title="Open file">
                        <span class="material-symbols-outlined">open_in_new</span>
                    </button>
                    ` : ''}
                    <button onclick="retryDownload(${item.id}, '${item.url}')" class="w-10 h-10 glass-button rounded-xl flex items-center justify-center bg-secondary/10 text-secondary" title="Retry download">
                        <span class="material-symbols-outlined">refresh</span>
                    </button>
                    <button onclick="deleteHistoryItem(${item.id})" class="w-10 h-10 glass-button rounded-xl flex items-center justify-center bg-white/5 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-all" title="Delete">
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                </div>
            </div>
        `;
        container.appendChild(el);
    });
}

function getFileIcon(ext) {
    const icons = {
        'mp4': 'movie', 'mkv': 'movie', 'avi': 'movie', 'mov': 'movie', 'webm': 'movie',
        'mp3': 'music_note', 'wav': 'music_note', 'flac': 'music_note', 'm4a': 'music_note',
        'jpg': 'image', 'png': 'image', 'gif': 'image', 'webp': 'image',
        'zip': 'folder_zip', 'rar': 'folder_zip', '7z': 'folder_zip',
        'pdf': 'picture_as_pdf', 'doc': 'description', 'docx': 'description',
    };
    return icons[ext] || 'description';
}

// History filter buttons
document.getElementById('filter-all')?.addEventListener('click', () => {
    historyFilter = 'all';
    updateFilterButtons();
    renderHistory();
});

document.getElementById('filter-completed')?.addEventListener('click', () => {
    historyFilter = 'completed';
    updateFilterButtons();
    renderHistory();
});

document.getElementById('filter-failed')?.addEventListener('click', () => {
    historyFilter = 'failed';
    updateFilterButtons();
    renderHistory();
});

function updateFilterButtons() {
    ['filter-all', 'filter-completed', 'filter-failed'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            if (btn.id === `filter-${historyFilter}`) {
                btn.className = 'px-4 py-2 bg-secondary/20 text-secondary rounded-xl text-sm font-bold transition-all';
            } else {
                btn.className = 'px-4 py-2 bg-white/5 text-zinc-400 hover:bg-white/10 rounded-xl text-sm font-bold transition-all';
            }
        }
    });
}

// History search
document.getElementById('history-search')?.addEventListener('input', (e) => {
    historySearch = e.target.value;
    renderHistory();
});

// Clear history button
document.getElementById('history-clear-btn')?.addEventListener('click', async () => {
    if (confirm('Clear all history? This cannot be undone.')) {
        await eel.clear_history()();
        showNotification('History cleared', 'success');
        refreshHistory();
        refreshDashboard();
    }
});

// Window functions
window.openFile = async function (id) {
    await eel.open_download(id)();
};

window.deleteDownload = async function (id) {
    await eel.delete_download(id)();
    showNotification('Download removed from history', 'success');
    refreshDashboard();
};

window.deleteHistoryItem = async function (id) {
    if (confirm('Delete this item from history?')) {
        await eel.delete_download(id)();
        showNotification('Item deleted', 'success');
        refreshHistory();
        refreshDashboard();
    }
};

window.retryDownload = async function (id, url) {
    if (url) {
        const task = await eel.add_download(url)();
        if (task) {
            showNotification('Download restarted', 'info');
            switchView('downloads');
        }
    }
};

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM ready');
    initNavigation();
    soundManager.init().then(() => {
        soundManager.play('intro');
    });
});

window.onload = () => {
    console.log('Window loaded');
    // Removed startup notification as requested by user
};

// Dashboard refresh
async function refreshDashboard() {
    try {
        const data = await eel.get_all_downloads()();
        const { stats, history: dashHistory, active } = data;

        // Update stats cards
        document.getElementById('dash-total').textContent = stats.total;
        document.getElementById('dash-completed').textContent = stats.completed;
        document.getElementById('dash-failed').textContent = stats.failed;
        document.getElementById('dash-bytes').textContent = formatBytes(stats.total_bytes);

        // Update active downloads
        const activeContainer = document.getElementById('dash-active-container');
        if (active && active.length > 0) {
            activeContainer.innerHTML = '';
            active.forEach(item => {
                const pct = item.total_size > 0 ? ((item.downloaded_size / item.total_size) * 100).toFixed(1) : 0;
                const el = document.createElement('div');
                el.className = 'glass-panel bg-surface-container/20 rounded-2xl p-4 border border-white/5';
                el.innerHTML = `
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-secondary animate-pulse">download</span>
                            <span class="text-white font-label font-bold">#${item.id}</span>
                            <span class="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 text-[10px] font-black uppercase animate-pulse">${item.status}</span>
                        </div>
                        <span class="text-primary font-mono text-sm">${formatBytes(item.speed)}/s</span>
                    </div>
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-zinc-400 text-xs truncate max-w-md">${item.filename || 'Acquiring...'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-zinc-500 font-mono mb-2">
                        <span>${formatBytes(item.downloaded_size)}</span>
                        <span>/</span>
                        <span>${formatBytes(item.total_size)}</span>
                        <span class="text-secondary ml-2">${pct}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
                        <div class="h-full bg-secondary rounded-full transition-all" style="width: ${pct}%"></div>
                    </div>
                `;
                activeContainer.appendChild(el);
            });
        } else {
            activeContainer.innerHTML = '<p class="text-zinc-500 font-label py-4 flex items-center gap-2"><span class="material-symbols-outlined">check_circle</span> No active downloads</p>';
        }

        // Update recent history
        const historyContainer = document.getElementById('dash-history-container');
        if (dashHistory && dashHistory.length > 0) {
            historyContainer.innerHTML = '';
            dashHistory.slice(0, 5).forEach(item => {
                const statusColor = item.status === 'COMPLETED' ? 'green' : (item.status === 'FAILED' ? 'red' : 'zinc');
                const statusIcon = item.status === 'COMPLETED' ? 'check_circle' : (item.status === 'FAILED' ? 'error' : 'pending');
                const el = document.createElement('div');
                el.className = 'glass-panel bg-surface-container/20 rounded-2xl p-4 border border-white/5 flex items-center justify-between';
                el.innerHTML = `
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg overflow-hidden bg-white/5 flex items-center justify-center border border-white/10">
                            ${item.thumbnail ? `<img src="${item.thumbnail}" class="w-full h-full object-cover">` :
                        `<span class="material-symbols-outlined text-zinc-400 text-sm">${statusIcon}</span>`}
                        </div>
                        <div class="flex flex-col">
                            <span class="text-white font-bold text-xs truncate max-w-[200px]">${item.title || item.filename || 'Unknown'}</span>
                            <div class="flex items-center gap-2">
                                <span class="text-[9px] font-black uppercase text-${statusColor}-400">${item.status}</span>
                                <span class="text-[9px] text-zinc-600 font-mono">${formatBytes(item.total_size)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="text-zinc-500 font-mono text-sm">${formatBytes(item.total_size)}</span>
                        ${item.status === 'COMPLETED' ? `
                        <button onclick="openFile(${item.id})" class="px-3 py-1 rounded bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 text-xs font-bold transition-all">
                            Open
                        </button>
                        ` : ''}
                    </div>
                `;
                historyContainer.appendChild(el);
            });
        } else {
            historyContainer.innerHTML = '<p class="text-zinc-500 font-label py-4">No downloads yet</p>';
        }
    } catch (e) {
        console.error('Dashboard refresh error:', e);
    }
}
// Mobile Menu
const sidebar = document.getElementById('sidebar');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');

if (mobileMenuBtn) {
    mobileMenuBtn.onclick = () => {
        sidebar.classList.toggle('-translate-x-full');
    };
}

// Close sidebar when clicking a link on mobile
const originalSwitchView = window.switchView;
window.switchView = (view) => {
    if (originalSwitchView) originalSwitchView(view);
    if (window.innerWidth < 768 && sidebar) {
        sidebar.classList.add('-translate-x-full');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Ready, initializing...');
    // Re-initialize sections after DOM is ready
    const newSections = {
        dashboard: document.getElementById('main-dashboard'),
        tasks: document.getElementById('main-tasks'),
        history: document.getElementById('main-history'),
        settings: document.getElementById('main-settings')
    };
    
    const newNavButtons = {
        dashboard: document.getElementById('nav-dashboard'),
        tasks: document.getElementById('nav-downloads'),
        history: document.getElementById('nav-history'),
        settings: document.getElementById('nav-settings')
    };
    
    // Update global references
    Object.assign(sections, newSections);
    Object.assign(navButtons, newNavButtons);
    
    // Add click listeners to nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.getAttribute('data-view');
            if (view && typeof window.switchView === 'function') {
                window.switchView(view);
            }
        });
    });
    
    // Initialize navigation
    initNavigation();
    initNetworking();
    
    console.log('Initialization complete');
});
