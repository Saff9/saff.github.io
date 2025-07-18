document.addEventListener("DOMContentLoaded", () => {
  const loadingScreen = document.getElementById("loadingScreen");
  window.addEventListener("load", () => {
    loadingScreen.style.opacity = "0";
    setTimeout(() => loadingScreen.style.display = "none", 500);
  });

  const dateTime = document.getElementById("dateTime");
  const subjectModal = document.getElementById("subjectModal");
  const subjectsContainer = document.getElementById("subjectsContainer");
  const progressContainer = document.getElementById("progressContainer");

  setInterval(() => {
    const now = new Date();
    dateTime.textContent = now.toLocaleString();
  }, 1000);

  function loadSubjects() {
    subjectsContainer.innerHTML = "";
    const subjects = JSON.parse(localStorage.getItem("subjects") || "[]");
    subjects.forEach(sub => {
      const card = document.createElement("div");
      card.className = "subject-card";
      card.textContent = sub;
      subjectsContainer.appendChild(card);
    });
  }

  loadSubjects();

  document.getElementById("addSubjectBtn").onclick = () => {
    subjectModal.style.display = "flex";
  };

  document.getElementById("cancelBtn").onclick = () => {
    subjectModal.style.display = "none";
  };

  document.getElementById("saveBtn").onclick = () => {
    const name = document.getElementById("subjectName").value.trim();
    if (!name) return;
    const subjects = JSON.parse(localStorage.getItem("subjects") || "[]");
    subjects.push(name);
    localStorage.setItem("subjects", JSON.stringify(subjects));
    subjectModal.style.display = "none";
    document.getElementById("subjectName").value = "";
    loadSubjects();
  };

  const offlineBanner = document.getElementById("offlineBanner");
  function updateOnlineStatus() {
    offlineBanner.style.display = navigator.onLine ? "none" : "block";
  }
  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);
  updateOnlineStatus();

  document.querySelectorAll("nav button").forEach(btn => {
    btn.onclick = () => {
      const target = btn.getAttribute("data-screen");
      document.getElementById("subjectsSection").style.display = (target === "subjects") ? "block" : "none";
      document.getElementById("progressSection").style.display = (target === "progress") ? "block" : "none";
    };
  });

  let deferredPrompt;
  const installPrompt = document.getElementById("installPrompt");
  const installBtn = document.getElementById("installBtn");

  window.addEventListener("beforeinstallprompt", e => {
    e.preventDefault();
    deferredPrompt = e;
    installPrompt.style.display = "flex";
  });

  installBtn.addEventListener("click", () => {
    installPrompt.style.display = "none";
    deferredPrompt.prompt();
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js')
      .then(() => console.log('SW registered'))
      .catch(err => console.error('SW registration failed:', err));
  }
});