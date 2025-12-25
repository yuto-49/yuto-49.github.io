// ============================================
// Bruno Simon Folio 2019 Inspired JavaScript
// ============================================

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
