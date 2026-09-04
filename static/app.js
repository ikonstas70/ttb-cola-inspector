// TTB COLA Label Compliance Inspector State & Controller
let currentSamples = [];
let selectedSample = null;
let currentReport = null;
let currentImageFile = null;
let batchData = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
    setupNavigation();
    setupDropzone();
    setupKeyboardShortcuts();
    await loadSamples();
});

// Setup Navigation Tabs
function setupNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            
            tab.classList.add('active');
            const target = tab.dataset.tab;
            document.getElementById(target).classList.add('active');
        });
    });
}

// Load Preloaded Samples
async function loadSamples() {
    try {
        const res = await fetch('/api/samples');
        const data = await res.json();
        currentSamples = data.samples || [];
        
        const select = document.getElementById('sampleSelect');
        select.innerHTML = '<option value="">-- Choose a Preloaded Compliance Test Case --</option>';
        
        currentSamples.forEach((sample, idx) => {
            const opt = document.createElement('option');
            opt.value = idx;
            opt.textContent = `${sample.name} [${sample.expected_result}]`;
            select.appendChild(opt);
        });

        // Select first compliant sample by default
        if (currentSamples.length > 0) {
            select.value = "0";
            onSampleSelected(0);
        }
    } catch (err) {
        console.error("Failed to load samples:", err);
    }
}

// Handle Sample Selection
function onSampleSelected(index) {
    if (index === "" || index === null) return;
    const sample = currentSamples[parseInt(index)];
    if (!sample) return;
    
    selectedSample = sample;
    const app = sample.application;
    
    // Fill Application Form
    document.getElementById('appId').value = app.application_id || '';
    document.getElementById('brandName').value = app.brand_name || '';
    document.getElementById('beverageType').value = app.beverage_type || 'Distilled Spirits';
    document.getElementById('classType').value = app.class_type || '';
    document.getElementById('alcoholContent').value = app.alcohol_content || '';
    document.getElementById('netContents').value = app.net_contents || '';
    document.getElementById('bottlerAddress').value = app.bottler_name_address || '';
    document.getElementById('countryOrigin').value = app.country_of_origin || 'United States';
    
    // Display Label Image
    const imgUrl = `/api/samples/image/${sample.file}`;
    displayImageOnCanvas(imgUrl);
    
    // Auto-run verification
    runVerification();
}

// Display Image on Canvas & Prepare Overlay
function displayImageOnCanvas(srcUrl) {
    const canvasWrapper = document.getElementById('canvasWrapper');
    canvasWrapper.innerHTML = `
        <img id="labelImg" src="${srcUrl}" alt="Label Artwork" onload="onImageLoaded()" />
        <div id="boundingOverlay" class="bounding-overlay"></div>
    `;
}

function onImageLoaded() {
    if (currentReport && currentReport.all_bounding_boxes) {
        renderBoundingBoxes(currentReport.all_bounding_boxes);
    }
}

// Setup Custom Image Upload Dropzone
function setupDropzone() {
    const dropzone = document.getElementById('customUploadDropzone');
    const fileInput = document.getElementById('customFileInput');
    
    dropzone.addEventListener('click', () => fileInput.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleCustomFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleCustomFile(e.target.files[0]);
        }
    });
}

function handleCustomFile(file) {
    currentImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        displayImageOnCanvas(e.target.result);
        runVerification();
    };
    reader.readAsDataURL(file);
}

// Execute Label Verification
async function runVerification() {
    const verifyBtn = document.getElementById('verifyBtn');
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '⚡ Verifying Label (27 CFR Compliance)...';
    
    const appData = {
        application_id: document.getElementById('appId').value,
        brand_name: document.getElementById('brandName').value,
        beverage_type: document.getElementById('beverageType').value,
        class_type: document.getElementById('classType').value,
        alcohol_content: document.getElementById('alcoholContent').value,
        net_contents: document.getElementById('netContents').value,
        bottler_name_address: document.getElementById('bottlerAddress').value,
        country_of_origin: document.getElementById('countryOrigin').value
    };
    
    try {
        let res;
        if (currentImageFile) {
            const formData = new FormData();
            formData.append('label_image', currentImageFile);
            formData.append('application_data', JSON.stringify(appData));
            res = await fetch('/api/verify', { method: 'POST', body: formData });
        } else if (selectedSample) {
            // Load sample image bytes via fetch and send to /api/verify
            const imgRes = await fetch(`/api/samples/image/${selectedSample.file}`);
            const imgBlob = await imgRes.blob();
            const formData = new FormData();
            formData.append('label_image', imgBlob, selectedSample.file);
            formData.append('application_data', JSON.stringify(appData));
            res = await fetch('/api/verify', { method: 'POST', body: formData });
        } else {
            alert('Please select a sample or upload a label artwork image.');
            verifyBtn.disabled = false;
            verifyBtn.innerHTML = '🔍 Run 27 CFR Label Compliance Verification';
            return;
        }
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Verification request failed');
        }
        
        currentReport = await res.json();
        renderVerificationReport(currentReport);
    } catch (err) {
        alert(`Verification Error: ${err.message}`);
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '🔍 Run 27 CFR Label Compliance Verification';
    }
}

// Render Report to UI
function renderVerificationReport(report) {
    const resultsContainer = document.getElementById('verificationResults');
    resultsContainer.style.display = 'block';
    
    // 1. Overall Status Banner
    const banner = document.getElementById('complianceBanner');
    banner.className = `compliance-banner ${report.overall_status}`;
    
    let statusIcon = '✅';
    let statusHeading = 'COMPLIANT — APPROVED FOR COLA CERTIFICATE';
    let statusClass = 'text-green';
    
    if (report.overall_status === 'REJECTED_MISMATCH') {
        statusIcon = '❌';
        statusHeading = 'REJECTED — MANDATORY 27 CFR DISCREPANCIES DETECTED';
    } else if (report.overall_status === 'WARNING_REVIEW') {
        statusIcon = '⚠️';
        statusHeading = 'FLAGGED FOR AGENT MANUAL REVIEW';
    }
    
    banner.innerHTML = `
        <div class="status-left">
            <div class="status-icon">${statusIcon}</div>
            <div class="status-text">
                <h2>${statusHeading}</h2>
                <p>Application ID: <strong>${report.application_id}</strong> &middot; ${report.suggested_action}</p>
            </div>
        </div>
        <div class="metrics-pill-group">
            <div class="metric-pill">
                <span style="font-size:0.7rem;color:#9ca3af;">SPEED</span>
                <span class="metric-val" style="color:#38bdf8;">${report.processing_time_ms} ms</span>
            </div>
            <div class="metric-pill">
                <span style="font-size:0.7rem;color:#9ca3af;">CONFIDENCE</span>
                <span class="metric-val" style="color:#34d399;">${(report.overall_confidence * 100).toFixed(1)}%</span>
            </div>
        </div>
    `;

    // 2. Government Warning Inspector (Jenny Park's focus)
    const gw = report.government_warning;
    const gwCard = document.getElementById('gwCard');
    
    const headerBadge = gw.header_valid 
        ? '<span class="badge badge-pass">✓ ALL CAPS "GOVERNMENT WARNING:"</span>'
        : '<span class="badge badge-fail">✗ CASE / PUNCTUATION VIOLATION</span>';
        
    const pClauseBadge = gw.pregnancy_clause_valid
        ? '<span class="badge badge-pass">✓ (1) Surgeon General / Pregnancy</span>'
        : '<span class="badge badge-fail">✗ (1) Pregnancy Warning Missing/Altered</span>';
        
    const mClauseBadge = gw.machinery_clause_valid
        ? '<span class="badge badge-pass">✓ (2) Machinery / Health Problems</span>'
        : '<span class="badge badge-fail">✗ (2) Impairment Warning Missing/Altered</span>';

    let issuesHtml = '';
    if (gw.issues && gw.issues.length > 0) {
        issuesHtml = `<div style="margin-top:10px;color:#f87171;font-size:0.85rem;">
            <strong>Violations Detected:</strong>
            <ul style="margin-left:20px;margin-top:4px;">
                ${gw.issues.map(i => `<li>${i}</li>`).join('')}
            </ul>
        </div>`;
    }

    gwCard.innerHTML = `
        <div class="card-header">
            <h3>⚖️ 27 CFR Part 16 Government Health Warning Statement Check</h3>
            <span class="badge ${gw.status === 'COMPLIANT' ? 'badge-pass' : 'badge-fail'}">${gw.status}</span>
        </div>
        <div class="card-body">
            <p style="font-size:0.85rem;color:#9ca3af;">Verifies exact uppercase bold header, Surgeon General pregnancy clause, and motor vehicle/machinery warning.</p>
            <div class="warning-badges-row">
                ${headerBadge}
                ${pClauseBadge}
                ${mClauseBadge}
            </div>
            ${issuesHtml}
            <div style="margin-top:12px;">
                <span style="font-size:0.78rem;font-weight:700;color:#9ca3af;">EXTRACTED WARNING TEXT FROM LABEL:</span>
                <div class="extracted-quote-box">${gw.raw_extracted_warning || 'NO WARNING STATEMENT DETECTED ON ARTWORK'}</div>
            </div>
        </div>
    `;

    // 3. Field-by-Field Breakdown Table
    const tableBody = document.getElementById('fieldTableBody');
    tableBody.innerHTML = '';
    
    report.field_results.forEach((f, idx) => {
        const row = document.createElement('tr');
        
        let statusBadge = '<span class="badge badge-pass">✓ MATCH</span>';
        if (f.status === 'REJECTED_MISMATCH') {
            statusBadge = '<span class="badge badge-fail">✗ MISMATCH</span>';
        } else if (f.status === 'WARNING_REVIEW') {
            statusBadge = '<span class="badge badge-warn">⚠️ REVIEW</span>';
        }
        
        row.innerHTML = `
            <td><strong>${f.display_name}</strong></td>
            <td><code>${f.application_value || '&mdash;'}</code></td>
            <td><code>${f.extracted_value || '<span style="color:#ef4444;">Not Detected</span>'}</code></td>
            <td><strong style="color:${f.confidence >= 0.85 ? '#34d399' : '#f87171'};">${(f.confidence * 100).toFixed(0)}%</strong></td>
            <td>${statusBadge}</td>
            <td style="font-size:0.82rem;color:#d1d5db;">${f.explanation}</td>
        `;
        
        // Highlight corresponding bounding box on hover
        row.addEventListener('mouseenter', () => highlightBox(idx));
        row.addEventListener('mouseleave', () => resetHighlights());
        
        tableBody.appendChild(row);
    });

    // 4. Render Bounding Boxes on Artwork Canvas
    renderBoundingBoxes(report.all_bounding_boxes);
}

// Render Bounding Boxes on Canvas Overlay
function renderBoundingBoxes(boxes) {
    const overlay = document.getElementById('boundingOverlay');
    if (!overlay) return;
    overlay.innerHTML = '';
    
    if (!boxes || boxes.length === 0) return;
    
    boxes.forEach((box, i) => {
        const rect = document.createElement('div');
        rect.className = 'bbox-rect';
        rect.id = `bbox-${i}`;
        rect.style.left = `${box.x * 100}%`;
        rect.style.top = `${box.y * 100}%`;
        rect.style.width = `${box.w * 100}%`;
        rect.style.height = `${box.h * 100}%`;
        rect.title = box.text || `Field Box #${i+1}`;
        overlay.appendChild(rect);
    });
}

function highlightBox(index) {
    const rect = document.getElementById(`bbox-${index}`);
    if (rect) rect.classList.add('highlighted');
}

function resetHighlights() {
    document.querySelectorAll('.bbox-rect').forEach(r => r.classList.remove('highlighted'));
}

// Batch Processing
async function runBatchBuiltinTest() {
    const btn = document.getElementById('runBatchBtn');
    btn.disabled = true;
    btn.innerHTML = '⚡ Processing Batch (Multi-Label)...';
    
    try {
        const res = await fetch('/api/batch/run-manifest-test', { method: 'POST' });
        if (!res.ok) throw new Error('Batch processing failed');
        
        batchData = await res.json();
        renderBatchResults(batchData);
    } catch (err) {
        alert(`Batch Error: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '⚡ Run Built-In Importer Batch (6 Multi-Category Labels)';
    }
}

function renderBatchResults(data) {
    document.getElementById('batchKpis').style.display = 'grid';
    document.getElementById('batchResultsTableContainer').style.display = 'block';
    
    document.getElementById('kpiTotal').textContent = data.total_processed;
    document.getElementById('kpiCompliant').textContent = data.compliant_count;
    document.getElementById('kpiWarning').textContent = data.warning_count;
    document.getElementById('kpiRejected').textContent = data.rejected_count;
    document.getElementById('kpiAvgTime').textContent = `${data.avg_time_per_label_ms} ms`;
    
    const tbody = document.getElementById('batchTableBody');
    tbody.innerHTML = '';
    
    data.reports.forEach(r => {
        const tr = document.createElement('tr');
        
        let statusBadge = '<span class="badge badge-pass">COMPLIANT</span>';
        if (r.overall_status === 'REJECTED_MISMATCH') {
            statusBadge = '<span class="badge badge-fail">REJECTED</span>';
        } else if (r.overall_status === 'WARNING_REVIEW') {
            statusBadge = '<span class="badge badge-warn">REVIEW</span>';
        }
        
        tr.innerHTML = `
            <td><strong>${r.application_id}</strong></td>
            <td>${r.brand_name}</td>
            <td>${r.beverage_type || 'Spirits'}</td>
            <td>${statusBadge}</td>
            <td><strong>${(r.overall_confidence * 100).toFixed(1)}%</strong></td>
            <td><code>${r.processing_time_ms} ms</code></td>
            <td style="font-size:0.8rem;color:#d1d5db;">${r.summary_notes.join('; ')}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Export Batch to CSV
async function exportBatchCSV() {
    if (!batchData || !batchData.reports) {
        alert('Please run a batch first before exporting.');
        return;
    }
    
    try {
        const res = await fetch('/api/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(batchData)
        });
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ttb_compliance_audit_report.csv';
        document.body.appendChild(a);
        a.click();
        document.body.appendChild(a);
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert(`Export Error: ${err.message}`);
    }
}

// Setup Keyboard Shortcuts (for senior agents Dave & Jenny)
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runVerification();
        }
    });
}
