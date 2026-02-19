// Dark/Light Mode Toggle
const toggle = document.createElement("button");
toggle.innerText = "🌙 Dark Mode";
toggle.className = "theme-toggle";
document.body.appendChild(toggle);

toggle.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
  toggle.innerText = document.body.classList.contains("dark-mode") ? "☀️ Light Mode" : "🌙 Dark Mode";
});

// Smooth Scroll for internal links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth"
      });
    }
  });
});

document.querySelectorAll(".accordion-toggle").forEach(toggle => {
    toggle.addEventListener("click", () => {
      const content = toggle.nextElementSibling;
      const arrow = toggle.querySelector(".arrow");
      content.classList.toggle("open");
  
      // Change arrow direction
      if (arrow) {
        arrow.textContent = content.classList.contains("open") ? "⬆" : "⬇";
      }
    });
  });

  const panels = document.querySelectorAll('.panel');

window.addEventListener('scroll', () => {
  const scrollY = window.scrollY;
  panels.forEach((panel, index) => {
    const offset = panel.offsetTop;
    const distance = scrollY - offset;
    const scale = Math.max(0.5, 1 - Math.abs(distance / 1000));
    panel.style.transform = `scale(${scale})`;
  });
});

