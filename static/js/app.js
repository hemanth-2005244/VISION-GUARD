document.addEventListener('DOMContentLoaded', () => {
    // --- Audio Alert Synthesizer ---
    let audioContext = null;
    let audioEnabled = true;

    function playAlarmSound() {
        if (!audioEnabled) return;
        try {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }

            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(880, audioContext.currentTime); // A5 note
            osc.frequency.exponentialRampToValueAtTime(440, audioContext.currentTime + 0.3);

            gain.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

            osc.connect(gain);
            gain.connect(audioContext.destination);

            osc.start();
            osc.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            console.log("Audio play error:", e);
        }
    }

    // --- Mode Titles ---
    const MODE_INFO = {
        intrusion: {
            title: "Perimeter Intrusion Guard",
            sub: "Real-time background subtraction & restricted ROI security monitoring"
        },
        face: {
            title: "Access Face Recognition Guard",
            sub: "Local LBPH AI Facial pattern matching & unknown intruder detection"
        },
        drowsiness: {
            title: "Health & Eye Fatigue Guard",
            sub: "Eye Aspect Ratio (EAR) computation & operator fatigue alert system"
        },
        tracking: {
            title: "Analytics Motion Tracker Guard",
            sub: "Centroid trajectory tracking, movement counts, and velocity paths"
        }
    };

    // --- Navigation & Mode Switching ---
    const navBtns = document.querySelectorAll('.nav-btn');
    let currentMode = 'intrusion';

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            currentMode = btn.getAttribute('data-mode');
            updateModeInfo(currentMode);
            updateBackendSettings({ active_mode: currentMode });
        });
    });

    function updateModeInfo(modeKey) {
        const info = MODE_INFO[modeKey] || MODE_INFO.intrusion;
        document.getElementById('active-mode-title').innerText = info.title;
        document.getElementById('active-mode-subtitle').innerText = info.sub;
    }

    // --- Audio & Snapshot Toggles ---
    const audioToggle = document.getElementById('btn-audio-toggle');
    audioToggle.addEventListener('click', () => {
        audioEnabled = !audioEnabled;
        audioToggle.classList.toggle('active', audioEnabled);
        updateBackendSettings({ alert_sound: audioEnabled });
    });

    const snapshotToggle = document.getElementById('btn-snapshot-toggle');
    let snapshotEnabled = true;
    snapshotToggle.addEventListener('click', () => {
        snapshotEnabled = !snapshotEnabled;
        snapshotToggle.classList.toggle('active', snapshotEnabled);
        updateBackendSettings({ save_snapshots: snapshotEnabled });
    });

    // --- Sliders Listener ---
    const sliders = [
        { id: 'slider-sensitivity', label: 'lbl-sensitivity', key: 'motion_sensitivity' },
        { id: 'slider-min-area', label: 'lbl-min-area', key: 'min_contour_area' },
        { id: 'slider-face-conf', label: 'lbl-face-conf', key: 'face_confidence_threshold' },
        { id: 'slider-ear', label: 'lbl-ear', key: 'ear_threshold' },
        { id: 'slider-cooldown', label: 'lbl-cooldown', key: 'cooldown_seconds' }
    ];

    sliders.forEach(s => {
        const input = document.getElementById(s.id);
        const label = document.getElementById(s.label);
        input.addEventListener('input', () => {
            label.innerText = input.value;
            const payload = {};
            payload[s.key] = parseFloat(input.value);
            updateBackendSettings(payload);
        });
    });

    function updateBackendSettings(payload) {
        fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).catch(err => console.error("Error saving settings:", err));
    }

    // --- Real-time Stats & Logs Polling ---
    let lastAlertCount = 0;

    function pollMetrics() {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                document.getElementById('val-fps').innerText = data.fps || '0.0';
                document.getElementById('val-total-alerts').innerText = data.total_alerts || 0;
                document.getElementById('val-intrusions').innerText = data.intrusions || 0;
                document.getElementById('val-persons').innerText = data.registered_persons || 0;

                if (data.total_alerts > lastAlertCount) {
                    if (lastAlertCount > 0) {
                        playAlarmSound();
                    }
                    lastAlertCount = data.total_alerts;
                }

                const camBadge = document.getElementById('cam-source-info');
                if (data.camera_fallback) {
                    camBadge.innerText = "Source: Sample Security Feed";
                } else {
                    camBadge.innerText = "Source: HD Hardware Camera";
                }
            })
            .catch(err => console.log("Stats error:", err));
    }

    function fetchAlertLogs() {
        fetch('/api/alerts')
            .then(res => res.json())
            .then(logs => {
                const tbody = document.getElementById('alert-logs-body');
                if (!logs || logs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="empty-msg">No security alerts logged yet. System clear.</td></tr>`;
                    return;
                }

                tbody.innerHTML = logs.map(a => {
                    let badgeClass = 'intrusion';
                    if (a.alert_type === 'Unknown Face') badgeClass = 'unknown';
                    if (a.alert_type === 'Drowsiness') badgeClass = 'drowsiness';

                    const snapHtml = a.snapshot_path 
                        ? `<button class="thumbnail-btn" onclick="openLightbox('${a.snapshot_path}', '${a.alert_type}: ${a.message}')"><i class="fa-solid fa-image"></i> View</button>`
                        : `<span style="color:var(--text-muted); font-size:11px;">None</span>`;

                    return `
                        <tr>
                            <td style="font-family:'JetBrains Mono', monospace;">${a.timestamp}</td>
                            <td><span class="alert-badge ${badgeClass}">${a.alert_type}</span></td>
                            <td style="color:var(--accent-red); font-weight:700;">${a.severity}</td>
                            <td>${a.message}</td>
                            <td>${snapHtml}</td>
                        </tr>
                    `;
                }).join('');
            })
            .catch(err => console.log("Alert logs error:", err));
    }

    // Clear Logs Button
    document.getElementById('btn-clear-alerts').addEventListener('click', () => {
        if (confirm("Are you sure you want to clear all alert logs?")) {
            fetch('/api/alerts', { method: 'DELETE' })
                .then(() => {
                    lastAlertCount = 0;
                    fetchAlertLogs();
                    pollMetrics();
                });
        }
    });

    // Export CSV Report
    document.getElementById('btn-export-csv').addEventListener('click', () => {
        window.location.href = '/api/export_logs';
    });

    // --- Face Registration Modal Handling ---
    const regModal = document.getElementById('modal-register');
    const openRegBtn = document.getElementById('btn-open-register');
    const closeRegBtn = document.getElementById('close-register-modal');
    const cancelRegBtn = document.getElementById('btn-cancel-register');
    const submitRegBtn = document.getElementById('btn-submit-register');
    const regMsg = document.getElementById('modal-register-msg');

    openRegBtn.addEventListener('click', () => {
        regModal.classList.add('active');
        regMsg.innerText = '';
    });

    [closeRegBtn, cancelRegBtn].forEach(b => {
        b.addEventListener('click', () => regModal.classList.remove('active'));
    });

    submitRegBtn.addEventListener('click', () => {
        const name = document.getElementById('reg-person-name').value.trim();
        const role = document.getElementById('reg-person-role').value;

        if (!name) {
            regMsg.style.color = '#ef4444';
            regMsg.innerText = 'Please enter person full name!';
            return;
        }

        regMsg.style.color = '#00f0ff';
        regMsg.innerText = 'Capturing face samples from camera stream...';

        fetch('/api/register_face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, role })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                regMsg.style.color = '#10b981';
                regMsg.innerText = data.message;
                setTimeout(() => {
                    regModal.classList.remove('active');
                    pollMetrics();
                }, 1500);
            } else {
                regMsg.style.color = '#ef4444';
                regMsg.innerText = data.message;
            }
        })
        .catch(err => {
            regMsg.style.color = '#ef4444';
            regMsg.innerText = 'Error capturing face profile.';
        });
    });

    // --- Lightbox Function ---
    window.openLightbox = function(url, caption) {
        const modal = document.getElementById('modal-snapshot');
        document.getElementById('lightbox-img').src = url;
        document.getElementById('lightbox-caption').innerText = caption;
        modal.classList.add('active');
    };

    document.getElementById('close-snapshot-modal').addEventListener('click', () => {
        document.getElementById('modal-snapshot').classList.remove('active');
    });

    // Start Polling Loops
    setInterval(pollMetrics, 1000);
    setInterval(fetchAlertLogs, 2000);
    pollMetrics();
    fetchAlertLogs();
});
