// ============================================
// Smooth Scroll
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const targetId = this.getAttribute('href');
    if (targetId === '#') return;

    const target = document.querySelector(targetId);
    if (target) {
      const navHeight = document.querySelector('.navbar').offsetHeight;
      const targetPosition = target.offsetTop - navHeight;

      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  });
});

// ============================================
// Scroll Animations (fade-in only)
// ============================================

const observerOptions = {
  threshold: 0.15,
  rootMargin: '0px 0px -60px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.project-item').forEach(el => {
  observer.observe(el);
});

// ============================================
// Navbar Background on Scroll
// ============================================

const navbar = document.querySelector('.navbar');

function updateNavbar() {
  if (window.scrollY > 10) {
    navbar.style.boxShadow = '0 1px 6px rgba(0, 0, 0, 0.06)';
  } else {
    navbar.style.boxShadow = 'none';
  }
}

window.addEventListener('scroll', updateNavbar);
updateNavbar();

// ============================================
// Active Navigation Link
// ============================================

const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

function highlightActiveSection() {
  const scrollY = window.scrollY;
  const navHeight = navbar.offsetHeight;

  sections.forEach(section => {
    const sectionTop = section.offsetTop - navHeight - 100;
    const sectionHeight = section.offsetHeight;
    const sectionId = section.getAttribute('id');

    if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
          link.classList.add('active');
        }
      });
    }
  });
}

window.addEventListener('scroll', highlightActiveSection);

// ============================================
// Smooth Page Load
// ============================================

window.addEventListener('load', () => {
  document.body.style.opacity = '0';
  setTimeout(() => {
    document.body.style.transition = 'opacity 0.4s ease';
    document.body.style.opacity = '1';
  }, 50);
});

// ============================================
// Project Number Counter Animation
// ============================================

function animateNumbers() {
  const statNumbers = document.querySelectorAll('.stat-number');

  statNumbers.forEach(stat => {
    const target = parseInt(stat.textContent);
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        stat.textContent = target + '+';
        clearInterval(timer);
      } else {
        stat.textContent = Math.floor(current) + '+';
      }
    }, 16);
  });
}

const aboutObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateNumbers();
      aboutObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const aboutSection = document.querySelector('.about-section');
if (aboutSection) {
  aboutObserver.observe(aboutSection);
}

// ============================================
// Project Details Toggle
// ============================================

function initializeProjectToggles() {
  const toggleButtons = document.querySelectorAll('.project-toggle');

  toggleButtons.forEach((button) => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      const wrapper = this.closest('.project-details-wrapper');
      const details = wrapper.querySelector('.project-details');
      const toggleText = this.querySelector('.toggle-text');

      if (details.classList.contains('collapsed')) {
        details.classList.remove('collapsed');
        void details.offsetHeight;
        details.classList.add('expanded');
        this.classList.add('active');
        toggleText.textContent = 'Read Less';
      } else {
        details.classList.remove('expanded');
        setTimeout(() => {
          if (!details.classList.contains('expanded')) {
            details.classList.add('collapsed');
          }
        }, 400);
        this.classList.remove('active');
        toggleText.textContent = 'Read More';
      }
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeProjectToggles);
} else {
  initializeProjectToggles();
}

// ============================================
// AI Career Agents (LangChain + Claude backend)
// ============================================

const AI_BACKEND_URL = '/api/agent';

const aiSection = document.querySelector('.ai-section');

if (aiSection) {
  const agentButtons = document.querySelectorAll('.ai-agent-btn');
  const summaryEl = document.getElementById('ai-summary');
  const messagesEl = document.getElementById('ai-messages');
  const formEl = document.getElementById('ai-form');
  const questionInput = document.getElementById('ai-question');
  const statusEl = document.getElementById('ai-status');

  // Resume upload elements
  const resumeForm = document.getElementById('ai-resume-form');
  const resumeFileInput = document.getElementById('ai-resume-file');
  const resumeDropzone = document.getElementById('ai-file-dropzone');
  const resumeFileName = document.getElementById('ai-file-name');
  const resumeUploadBtn = document.getElementById('ai-upload-btn');
  const resumeStatusEl = document.getElementById('ai-resume-status');

  let currentAgent = null;
  let isRequestInFlight = false;
  let uploadedResumeText = null;

  function setStatus(message, isError = false) {
    if (!statusEl) return;
    statusEl.textContent = message || '';
    statusEl.classList.toggle('error', Boolean(isError));
  }

  function setResumeStatus(message, type = '') {
    if (!resumeStatusEl) return;
    resumeStatusEl.textContent = message || '';
    resumeStatusEl.className = 'ai-resume-status';
    if (type) resumeStatusEl.classList.add(type);
  }

  // Handle file selection
  if (resumeFileInput) {
    resumeFileInput.addEventListener('change', () => {
      const file = resumeFileInput.files[0];
      if (file) {
        resumeFileName.textContent = file.name;
        if (resumeDropzone) resumeDropzone.classList.add('has-file');
        resumeUploadBtn.disabled = false;
      } else {
        resumeFileName.textContent = 'Drag & drop your PDF here, or click to browse';
        if (resumeDropzone) resumeDropzone.classList.remove('has-file');
        resumeUploadBtn.disabled = true;
      }
    });
  }

  // Drag-and-drop support
  if (resumeDropzone) {
    resumeDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      resumeDropzone.classList.add('dragover');
    });
    resumeDropzone.addEventListener('dragleave', () => {
      resumeDropzone.classList.remove('dragover');
    });
    resumeDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      resumeDropzone.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && file.name.toLowerCase().endsWith('.pdf')) {
        resumeFileInput.files = e.dataTransfer.files;
        resumeFileInput.dispatchEvent(new Event('change'));
      }
    });
  }

  // Handle resume upload
  if (resumeForm) {
    resumeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const file = resumeFileInput.files[0];
      if (!file) return;

      resumeUploadBtn.disabled = true;
      setResumeStatus('Uploading and processing resume...', 'loading');

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/api/agent/upload-resume', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Upload failed');
        }

        const data = await response.json();
        uploadedResumeText = data.resumeText;
        setResumeStatus(`Resume "${data.filename}" uploaded successfully!`, 'success');

        // Re-generate summary if an agent is already selected
        if (currentAgent) {
          generateCareerSummary(currentAgent);
        }
      } catch (err) {
        console.error('Resume upload error:', err);
        setResumeStatus(`Upload failed: ${err.message}`, 'error');
      } finally {
        resumeUploadBtn.disabled = false;
      }
    });
  }

  function buildUserProfile() {
    if (!uploadedResumeText) {
      return null;
    }
    return `Candidate Resume:\n${uploadedResumeText}`;
  }

  function appendMessage(role, text) {
    if (!messagesEl) return;
    const div = document.createElement('div');
    div.classList.add('ai-message');
    if (role === 'user') div.classList.add('ai-message-user');
    if (role === 'agent') div.classList.add('ai-message-agent');
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function generateCareerSummary(agent) {
    if (!summaryEl) return;

    currentAgent = agent;

    if (!uploadedResumeText) {
      summaryEl.textContent = 'Please upload your resume first, then select an agent.';
      return;
    }

    const profile = buildUserProfile();

    summaryEl.textContent = 'Thinking about your future career in this field...';
    setStatus('Generating career vision with your AI backend...', false);

    try {
      const response = await fetch(AI_BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mode: 'summary',
          agentType: agent,
          profile
        })
      });

      if (!response.ok) {
        throw new Error(`Backend responded with status ${response.status}`);
      }

      const data = await response.json();
      const summary = data.summary || data.text || 'Your backend did not return a summary field.';
      summaryEl.textContent = summary;
      setStatus('', false);
    } catch (err) {
      console.error('AI summary error:', err);
      summaryEl.textContent =
        'Could not reach your AI backend. Once you connect a LangChain + Claude endpoint, this will generate a tailored career story.';
      setStatus('Unable to reach AI backend. Check AI_BACKEND_URL and your server.', true);
    }
  }

  async function askAgent(question) {
    if (!currentAgent || !messagesEl || !formEl || !questionInput) return;
    if (isRequestInFlight) return;

    const profile = buildUserProfile();
    if (!profile) {
      setStatus('Please upload your resume first.', true);
      return;
    }

    appendMessage('user', question);
    setStatus('Asking your agent...', false);
    isRequestInFlight = true;
    formEl.querySelector('button').disabled = true;

    try {
      const response = await fetch(AI_BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mode: 'chat',
          agentType: currentAgent,
          profile,
          question
        })
      });

      if (!response.ok) {
        throw new Error(`Backend responded with status ${response.status}`);
      }

      const data = await response.json();
      const answer = data.answer || data.text || 'Your backend did not return an answer field.';
      appendMessage('agent', answer);
      setStatus('', false);
    } catch (err) {
      console.error('AI chat error:', err);
      appendMessage(
        'agent',
        'I could not contact the AI backend. Once you deploy your LangChain + Claude server, I can answer your questions here.'
      );
      setStatus('Unable to reach AI backend. Check AI_BACKEND_URL and your server.', true);
    } finally {
      isRequestInFlight = false;
      formEl.querySelector('button').disabled = false;
    }
  }

  agentButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      agentButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const agent = btn.getAttribute('data-agent');
      if (agent) {
        generateCareerSummary(agent);
      }
    });
  });

  if (formEl && questionInput) {
    formEl.addEventListener('submit', e => {
      e.preventDefault();
      const value = questionInput.value.trim();
      if (!value) return;
      if (!currentAgent) {
        setStatus('Select Finance, Healthcare, or Consultant agent first.', true);
        return;
      }
      if (!uploadedResumeText) {
        setStatus('Please upload your resume first for personalized results.', true);
        return;
      }
      questionInput.value = '';
      askAgent(value);
    });
  }
}

// ============================================
// PDF Career Path Functionality
// ============================================

const API_BASE = '/api';

function initializePDFFeatures() {
  const resumeForm = document.getElementById('upload-resume-form');
  const resumeStatus = document.getElementById('resume-status');

  if (resumeForm && resumeStatus) {
    resumeForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById('resume-file');

      if (!fileInput.files[0]) {
        setStatusMessage(resumeStatus, 'Please select a PDF file', 'error');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('source_type', 'resume');
      formData.append('company', '');

      setStatusMessage(resumeStatus, 'Uploading and indexing resume...', 'loading');

      try {
        const response = await fetch(`${API_BASE}/upload-pdf`, {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
          setStatusMessage(resumeStatus, `${result.message} (${result.chunks} chunks)`, 'success');
          resumeForm.reset();
          setTimeout(loadDocuments, 500);
        } else {
          setStatusMessage(resumeStatus, `Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(resumeStatus, `Error: ${error.message}`, 'error');
      }
    });
  }

  const uploadForm = document.getElementById('upload-company-form');
  const uploadStatus = document.getElementById('upload-status');

  if (uploadForm && uploadStatus) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById('company-file');
      const companyInput = document.getElementById('company-name');
      const sourceTypeSelect = document.getElementById('source-type');

      if (!fileInput.files[0]) {
        setStatusMessage(uploadStatus, 'Please select a PDF file', 'error');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('source_type', sourceTypeSelect.value);
      formData.append('company', companyInput.value);

      setStatusMessage(uploadStatus, 'Uploading and indexing PDF...', 'loading');

      try {
        const response = await fetch(`${API_BASE}/upload-pdf`, {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
          setStatusMessage(uploadStatus, `${result.message} (${result.chunks} chunks)`, 'success');
          uploadForm.reset();
          setTimeout(loadDocuments, 500);
        } else {
          setStatusMessage(uploadStatus, `Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(uploadStatus, `Error: ${error.message}`, 'error');
      }
    });
  }

  const refreshDocsBtn = document.getElementById('refresh-docs-btn');
  if (refreshDocsBtn) {
    refreshDocsBtn.addEventListener('click', loadDocuments);
  }

  const careerPathForm = document.getElementById('career-path-form');
  const careerPathStatus = document.getElementById('career-path-status');
  const careerPathOutput = document.getElementById('career-path-output');

  if (careerPathForm && careerPathStatus && careerPathOutput) {
    careerPathForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const targetRole = document.getElementById('target-role').value;
      const filterCompany = document.getElementById('filter-company').value;

      setStatusMessage(careerPathStatus, 'Generating personalized career path...', 'loading');
      careerPathOutput.classList.remove('visible');

      try {
        const response = await fetch(`${API_BASE}/career-path`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            target_role: targetRole,
            company: filterCompany || undefined
          })
        });

        const result = await response.json();

        if (response.ok) {
          setStatusMessage(careerPathStatus, 'Career path generated successfully!', 'success');
          careerPathOutput.textContent = result.career_path;
          careerPathOutput.classList.add('visible');
        } else {
          setStatusMessage(careerPathStatus, `Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(careerPathStatus, `Error: ${error.message}`, 'error');
      }
    });
  }

  loadDocuments();
}

async function loadDocuments() {
  const documentsList = document.getElementById('documents-list');
  if (!documentsList) return;

  try {
    const response = await fetch(`${API_BASE}/list-documents`);
    const text = await response.text();
    if (!text) {
      documentsList.innerHTML = '<p class="documents-empty">No documents uploaded yet</p>';
      return;
    }
    const result = JSON.parse(text);

    if (response.ok && result.success) {
      displayDocuments(result.documents);
    } else {
      documentsList.innerHTML = '<p class="documents-empty">Error loading documents</p>';
    }
  } catch (error) {
    documentsList.innerHTML = '<p class="documents-empty">No documents uploaded yet</p>';
  }
}

function displayDocuments(documents) {
  const documentsList = document.getElementById('documents-list');
  if (!documentsList) return;

  const totalDocs = documents.resume.length + documents.company_pdf.length + documents.project_pdf.length;

  if (totalDocs === 0) {
    documentsList.innerHTML = '<p class="documents-empty">No documents uploaded yet</p>';
    return;
  }

  let html = '';

  if (documents.resume.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">Resume</div>';
    documents.resume.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  if (documents.company_pdf.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">Company Documents</div>';
    documents.company_pdf.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  if (documents.project_pdf.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">Project Documents</div>';
    documents.project_pdf.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  documentsList.innerHTML = html;

  documentsList.querySelectorAll('.document-delete').forEach(btn => {
    btn.addEventListener('click', () => {
      const docId = btn.dataset.docId;
      deleteDocument(docId);
    });
  });
}

function createDocumentItem(doc) {
  const company = doc.company ? ` · ${doc.company}` : '';
  const date = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '';

  return `
    <div class="document-item">
      <div class="document-info">
        <div class="document-filename">${doc.filename}</div>
        <div class="document-meta">${date}${company} · ${doc.total_chunks} chunks</div>
      </div>
      <button class="document-delete" data-doc-id="${doc.doc_id}">Delete</button>
    </div>
  `;
}

async function deleteDocument(docId) {
  if (!confirm('Are you sure you want to delete this document?')) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/delete-document/${docId}`, {
      method: 'DELETE'
    });

    const result = await response.json();

    if (response.ok && result.success) {
      loadDocuments();
    } else {
      alert(`Error deleting document: ${result.detail || 'Unknown error'}`);
    }
  } catch (error) {
    alert(`Error deleting document: ${error.message}`);
  }
}

function setStatusMessage(element, message, type) {
  if (!element) return;

  element.textContent = message;
  element.className = 'pdf-status';

  if (type) {
    element.classList.add(type);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePDFFeatures);
} else {
  initializePDFFeatures();
}
