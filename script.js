// Dark/Light Mode Toggle
const toggle = document.createElement("button");
toggle.innerText = "🌙 Dark Mode";
toggle.style.position = "fixed";
toggle.style.top = "1rem";
toggle.style.right = "1rem";
toggle.style.zIndex = "1000";
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
