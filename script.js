

// Custom Cursor
const cursor = document.querySelector('.cursor');
const cursorFollower = document.querySelector('.cursor-follower');

let mouseX = 0;
let mouseY = 0;
let followerX = 0;
let followerY = 0;

// Update cursor position
function updateCursor(e) {
  mouseX = e.clientX;
  mouseY = e.clientY;
  
  cursor.style.left = mouseX + 'px';
  cursor.style.top = mouseY + 'px';
}

// Smooth follower animation
function animateFollower() {
  followerX += (mouseX - followerX) * 0.1;
  followerY += (mouseY - followerY) * 0.1;
  
  cursorFollower.style.left = followerX + 'px';
  cursorFollower.style.top = followerY + 'px';
  
  requestAnimationFrame(animateFollower);
}

// Initialize cursor
if (window.innerWidth > 480) {
  document.addEventListener('mousemove', updateCursor);
  animateFollower();
  
  // Cursor hover effects
  const hoverElements = document.querySelectorAll('a, button, .project-image-wrapper, .skill-tag, .tech, .contact-item');
  
  hoverElements.forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.classList.add('hover');
      cursorFollower.classList.add('hover');
    });
    
    el.addEventListener('mouseleave', () => {
      cursor.classList.remove('hover');
      cursorFollower.classList.remove('hover');
    });
  });
}

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
// Scroll Animations
// ============================================

const observerOptions = {
  threshold: 0.2,
  rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

// Observe project items
document.querySelectorAll('.project-item').forEach(el => {
  observer.observe(el);
});

// ============================================
// Parallax Effect for Hero
// ============================================

const heroSection = document.querySelector('.hero-section');
const heroImage = document.querySelector('.hero-image');

function handleParallax() {
  const scrollY = window.scrollY;
  const heroHeight = heroSection.offsetHeight;
  
  if (scrollY < heroHeight) {
    const parallaxValue = scrollY * 0.3;
    if (heroImage) {
      heroImage.style.transform = `translateY(${parallaxValue}px)`;
      heroImage.style.opacity = 1 - (scrollY / heroHeight) * 0.5;
    }
  }
}

// Throttle scroll events
let ticking = false;
window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      handleParallax();
      ticking = false;
    });
    ticking = true;
  }
});

// ============================================
// Navbar Background on Scroll
// ============================================

const navbar = document.querySelector('.navbar');

function updateNavbar() {
  if (window.scrollY > 50) {
    navbar.style.background = 'rgba(10, 10, 10, 0.95)';
    navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.3)';
  } else {
    navbar.style.background = 'rgba(10, 10, 10, 0.8)';
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

// Add active state styling
const style = document.createElement('style');
style.textContent = `
  .nav-link.active {
    color: var(--text-primary);
  }
  .nav-link.active::after {
    width: 100%;
  }
`;
document.head.appendChild(style);

// ============================================
// Project Image Hover Effects
// ============================================

document.querySelectorAll('.project-image-wrapper').forEach(wrapper => {
  wrapper.addEventListener('mouseenter', function() {
    this.style.transform = 'scale(1.05)';
  });
  
  wrapper.addEventListener('mouseleave', function() {
    this.style.transform = 'scale(1)';
  });
});

// ============================================
// Smooth Page Load
// ============================================

window.addEventListener('load', () => {
  document.body.style.opacity = '0';
  setTimeout(() => {
    document.body.style.transition = 'opacity 0.5s ease';
    document.body.style.opacity = '1';
  }, 100);
});

// ============================================
// Text Reveal Animation
// ============================================

function revealText() {
  const textElements = document.querySelectorAll('.hero-title .line');
  
  textElements.forEach((el, index) => {
    setTimeout(() => {
      el.style.transform = 'translateY(0)';
    }, index * 200);
  });
}

// Initialize on load
window.addEventListener('load', () => {
  revealText();
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

// Trigger when about section is visible
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
// Smooth Scroll for Project Links
// ============================================

document.querySelectorAll('.project-link').forEach(link => {
  link.addEventListener('click', function(e) {
    e.preventDefault();
    // Add your project link logic here
    console.log('Project link clicked');
  });
});

// ============================================
// Project Details Toggle
// ============================================

function initializeProjectToggles() {
  const toggleButtons = document.querySelectorAll('.project-toggle');
  console.log('Found', toggleButtons.length, 'toggle buttons');

  toggleButtons.forEach((button, index) => {
    console.log('Attaching click handler to button', index + 1);
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();

      console.log('Button clicked!', index + 1);

      const wrapper = this.closest('.project-details-wrapper');
      const details = wrapper.querySelector('.project-details');
      const toggleText = this.querySelector('.toggle-text');

      // Toggle the expanded/collapsed state
      if (details.classList.contains('collapsed')) {
        console.log('Expanding details...');
        details.classList.remove('collapsed');
        // Force a reflow to enable transition
        void details.offsetHeight;
        details.classList.add('expanded');
        this.classList.add('active');
        toggleText.textContent = 'Read Less';
      } else {
        console.log('Collapsing details...');
        details.classList.remove('expanded');
        // Add collapsed after transition
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

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeProjectToggles);
} else {
  initializeProjectToggles();
}

console.log('Project toggle script loaded. DOM state:', document.readyState);

// ============================================
// AI Career Agents (Crew AI + Claude backend hook)
// ============================================

// IMPORTANT:
// - This front-end does NOT talk directly to Claude or Crew AI.
// - You should create a backend endpoint (Node/Express, Python/FastAPI, etc.)
//   that uses Crew AI + Claude, then set AI_BACKEND_URL to that endpoint.
// - Never expose your API keys in this file or in the browser.

const AI_BACKEND_URL = 'http://localhost:8000/api/agent'; // TODO: replace with your backend URL

const aiSection = document.querySelector('.ai-section');

if (aiSection) {
  const agentButtons = document.querySelectorAll('.ai-agent-btn');
  const summaryEl = document.getElementById('ai-summary');
  const messagesEl = document.getElementById('ai-messages');
  const formEl = document.getElementById('ai-form');
  const questionInput = document.getElementById('ai-question');
  const statusEl = document.getElementById('ai-status');

  let currentAgent = null;
  let isRequestInFlight = false;

  function setStatus(message, isError = false) {
    if (!statusEl) return;
    statusEl.textContent = message || '';
    statusEl.classList.toggle('error', Boolean(isError));
  }

  function buildUserProfile() {
    const aboutText = document.querySelector('.about-text')?.textContent?.trim() || '';
    const skills = Array.from(document.querySelectorAll('.skill-tag')).map(el => el.textContent.trim());
    const projects = Array.from(document.querySelectorAll('.project-title')).map(el => el.textContent.trim());

    return [
      'Candidate: Yuto Maruyama',
      `About: ${aboutText}`,
      skills.length ? `Skills: ${skills.join(', ')}` : '',
      projects.length ? `Projects: ${projects.join(' | ')}` : '',
      'Resume file: assets/YUTO_MARUYAMA_RESUME_031925.pdf'
    ].filter(Boolean).join('\n');
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
          agentType: agent, // "finance" | "healthcare" | "consultant"
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
        'Could not reach your AI backend. Once you connect a Crew AI + Claude endpoint, this will generate a tailored career story.';
      setStatus('Unable to reach AI backend. Check AI_BACKEND_URL and your server.', true);
    }
  }

  async function askAgent(question) {
    if (!currentAgent || !messagesEl || !formEl || !questionInput) return;
    if (isRequestInFlight) return;

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
          profile: buildUserProfile(),
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
        'I could not contact the AI backend. Once you deploy your Crew AI + Claude server, I can answer your questions here.'
      );
      setStatus('Unable to reach AI backend. Check AI_BACKEND_URL and your server.', true);
    } finally {
      isRequestInFlight = false;
      formEl.querySelector('button').disabled = false;
    }
  }

  // Agent selection
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

  // Chat form
  if (formEl && questionInput) {
    formEl.addEventListener('submit', e => {
      e.preventDefault();
      const value = questionInput.value.trim();
      if (!value) return;
      if (!currentAgent) {
        setStatus('Select Finance, Healthcare, or Consultant agent first.', true);
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

const API_BASE = 'http://localhost:8000/api';

function initializePDFFeatures() {
  // Resume PDF upload
  const resumeForm = document.getElementById('upload-resume-form');
  const resumeStatus = document.getElementById('resume-status');

  if (resumeForm && resumeStatus) {
    resumeForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById('resume-file');

      if (!fileInput.files[0]) {
        setStatusMessage(resumeStatus, '✗ Please select a PDF file', 'error');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('source_type', 'resume');
      formData.append('company', ''); // Not needed for resume

      setStatusMessage(resumeStatus, 'Uploading and indexing resume...', 'loading');

      try {
        const response = await fetch(`${API_BASE}/upload-pdf`, {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
          setStatusMessage(resumeStatus, `✓ ${result.message} (${result.chunks} chunks)`, 'success');
          resumeForm.reset();
          // Refresh documents list
          setTimeout(loadDocuments, 500);
        } else {
          setStatusMessage(resumeStatus, `✗ Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(resumeStatus, `✗ Error: ${error.message}`, 'error');
      }
    });
  }

  // Company PDF upload
  const uploadForm = document.getElementById('upload-company-form');
  const uploadStatus = document.getElementById('upload-status');

  if (uploadForm && uploadStatus) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById('company-file');
      const companyInput = document.getElementById('company-name');
      const sourceTypeSelect = document.getElementById('source-type');

      if (!fileInput.files[0]) {
        setStatusMessage(uploadStatus, '✗ Please select a PDF file', 'error');
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
          setStatusMessage(uploadStatus, `✓ ${result.message} (${result.chunks} chunks)`, 'success');
          uploadForm.reset();
          // Refresh documents list
          setTimeout(loadDocuments, 500);
        } else {
          setStatusMessage(uploadStatus, `✗ Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(uploadStatus, `✗ Error: ${error.message}`, 'error');
      }
    });
  }

  // Refresh documents button
  const refreshDocsBtn = document.getElementById('refresh-docs-btn');
  if (refreshDocsBtn) {
    refreshDocsBtn.addEventListener('click', loadDocuments);
  }

  // Career path generation
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
          setStatusMessage(careerPathStatus, '✓ Career path generated successfully!', 'success');
          careerPathOutput.textContent = result.career_path;
          careerPathOutput.classList.add('visible');
        } else {
          setStatusMessage(careerPathStatus, `✗ Error: ${result.detail || 'Unknown error'}`, 'error');
        }
      } catch (error) {
        setStatusMessage(careerPathStatus, `✗ Error: ${error.message}`, 'error');
      }
    });
  }

  // Load documents on page load
  loadDocuments();
}

async function loadDocuments() {
  const documentsList = document.getElementById('documents-list');
  if (!documentsList) return;

  try {
    const response = await fetch(`${API_BASE}/list-documents`);
    const result = await response.json();

    if (response.ok && result.success) {
      displayDocuments(result.documents);
    } else {
      documentsList.innerHTML = '<p class="documents-empty">Error loading documents</p>';
    }
  } catch (error) {
    documentsList.innerHTML = `<p class="documents-empty">Error: ${error.message}</p>`;
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

  // Resume documents
  if (documents.resume.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">📄 Resume</div>';
    documents.resume.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  // Company PDFs
  if (documents.company_pdf.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">🏢 Company Documents</div>';
    documents.company_pdf.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  // Project PDFs
  if (documents.project_pdf.length > 0) {
    html += '<div class="document-group">';
    html += '<div class="document-group-title">📚 Project Documents</div>';
    documents.project_pdf.forEach(doc => {
      html += createDocumentItem(doc);
    });
    html += '</div>';
  }

  documentsList.innerHTML = html;

  // Add delete button event listeners
  documentsList.querySelectorAll('.document-delete').forEach(btn => {
    btn.addEventListener('click', () => {
      const docId = btn.dataset.docId;
      deleteDocument(docId);
    });
  });
}

function createDocumentItem(doc) {
  const company = doc.company ? ` • ${doc.company}` : '';
  const date = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '';

  return `
    <div class="document-item">
      <div class="document-info">
        <div class="document-filename">${doc.filename}</div>
        <div class="document-meta">${date}${company} • ${doc.total_chunks} chunks</div>
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
      // Refresh the documents list
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

// Initialize PDF features when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePDFFeatures);
} else {
  initializePDFFeatures();
}
