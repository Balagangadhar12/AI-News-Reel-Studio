// AI News Reel Studio - Frontend Script
document.addEventListener("DOMContentLoaded", () => {
    
    // --- PARTICLE BACKGROUND SYSTEM ---
    initParticles();
    
    // --- HERO TYPING ENGINE ---
    initTyping();
    
    // --- CORE GENERATION PIPELINE ---
    initLatestNews();
    initGenerator();
    
    // --- RESULT PAGE UTILITIES ---
    initResultActions();
});

let selectedArticle = null;

// Particle Background Animation
function initParticles() {
    const canvas = document.getElementById("particles-canvas");
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    let particles = [];
    const particleCount = 45;
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 4 + 1;
            this.speedX = Math.random() * 0.4 - 0.2;
            this.speedY = Math.random() * 0.4 - 0.2;
            // Alternate colors between primary (purple) and secondary (cyan)
            this.color = Math.random() > 0.5 ? "rgba(168, 85, 247, 0.25)" : "rgba(6, 182, 212, 0.25)";
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 8;
            ctx.shadowColor = this.color;
            ctx.fill();
            ctx.shadowBlur = 0; // Reset shadow for next draw
        }
    }
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// Typing Effect for Landing Page
function initTyping() {
    const el = document.getElementById("hero-typing");
    if (!el) return;
    
    const phrases = ["Professional Shorts", "Instagram Reels", "YouTube Shorts", "TikTok Videos"];
    let phraseIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    let typeSpeed = 100;
    
    function type() {
        const currentPhrase = phrases[phraseIdx];
        
        if (isDeleting) {
            el.textContent = currentPhrase.substring(0, charIdx - 1);
            charIdx--;
            typeSpeed = 40;
        } else {
            el.textContent = currentPhrase.substring(0, charIdx + 1);
            charIdx++;
            typeSpeed = 120;
        }
        
        if (!isDeleting && charIdx === currentPhrase.length) {
            isDeleting = true;
            typeSpeed = 1800; // Pause at end of phrase
        } else if (isDeleting && charIdx === 0) {
            isDeleting = false;
            phraseIdx = (phraseIdx + 1) % phrases.length;
            typeSpeed = 400; // Pause before typing next phrase
        }
        
        setTimeout(type, typeSpeed);
    }
    setTimeout(type, 500);
}

// Video Generation Handlers
function initGenerator() {
    const btnGenerate = document.getElementById("btn-generate");
    if (!btnGenerate) return;
    
    let activeInputTab = "latest"; // Default tab
    
    // Track active tab clicks
    document.getElementById("latest-tab")?.addEventListener("click", () => {
        activeInputTab = "latest";
        updateGenerateButtonState(activeInputTab);
    });
    document.getElementById("search-tab")?.addEventListener("click", () => {
        activeInputTab = "search";
        updateGenerateButtonState(activeInputTab);
    });
    document.getElementById("url-tab")?.addEventListener("click", () => {
        activeInputTab = "url";
        updateGenerateButtonState(activeInputTab);
    });
    
    btnGenerate.addEventListener("click", async () => {
        const voice = document.getElementById("select-voice").value;
        const fastMode = document.getElementById("toggle-fast-mode")?.checked ?? true;
        let payload = { voice: voice, fast_mode: fastMode };
        
        if (activeInputTab === "latest") {
            if (!selectedArticle) {
                showToast("Pick a Headline", "Please select one of the latest news headlines first.", "warning");
                return;
            }
            payload.selected_article = selectedArticle;
        } else if (activeInputTab === "search") {
            const query = document.getElementById("input-query").value.trim();
            if (!query) {
                showToast("Input Required", "Please enter a search topic/keyword.", "warning");
                return;
            }
            payload.search_query = query;
        } else {
            const url = document.getElementById("input-url").value.trim();
            if (!url) {
                showToast("Input Required", "Please paste a news article URL.", "warning");
                return;
            }
            payload.source_url = url;
        }
        
        // Start Request
        btnGenerate.disabled = true;
        btnGenerate.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin me-2"></i>Starting...`;
        
        try {
            const response = await fetch("/api/reel/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                const taskId = data.task_id;
                // Reveal Progress timeline
                document.getElementById("progress-container").style.display = "block";
                document.getElementById("generate-section").scrollIntoView({ behavior: "smooth" });
                
                showToast("Studio Started", "Your video is enqueued. Rendering starting shortly...", "info");
                
                // Poll progress
                pollProgress(taskId);
            } else {
                throw new Error(data.error || "Failed to trigger generation.");
            }
            
        } catch (err) {
            showToast("Server Error", err.message, "danger");
            btnGenerate.disabled = false;
            btnGenerate.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-2"></i>Generate Reel`;
        }
    });

    document.getElementById("input-query")?.addEventListener("input", () => updateGenerateButtonState(activeInputTab));
    document.getElementById("input-url")?.addEventListener("input", () => updateGenerateButtonState(activeInputTab));
    updateGenerateButtonState(activeInputTab);
}

// Latest headline picker
function initLatestNews() {
    const list = document.getElementById("latest-news-list");
    if (!list) return;

    const topicInput = document.getElementById("input-news-topic");
    const refreshBtn = document.getElementById("btn-refresh-news");
    const loadTopicBtn = document.getElementById("btn-load-topic");

    refreshBtn?.addEventListener("click", () => loadLatestNews(topicInput?.value.trim() || "top stories"));
    loadTopicBtn?.addEventListener("click", () => loadLatestNews(topicInput?.value.trim() || "top stories"));
    topicInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            loadLatestNews(topicInput.value.trim() || "top stories");
        }
    });

    loadLatestNews("top stories");
}

async function loadLatestNews(topic) {
    const list = document.getElementById("latest-news-list");
    if (!list) return;

    list.innerHTML = `<div class="news-loading">Loading latest headlines...</div>`;

    try {
        const response = await fetch(`/api/news/latest?topic=${encodeURIComponent(topic)}`);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || "Could not load latest news.");
        }

        renderLatestNews(data.articles || []);
    } catch (err) {
        list.innerHTML = `<div class="news-empty">Could not load news. Try a topic search.</div>`;
        showToast("News Error", err.message, "danger");
    }
}

function renderLatestNews(articles) {
    const list = document.getElementById("latest-news-list");
    if (!list) return;

    selectedArticle = null;
    updateSelectedHeadlineBox();
    updateGenerateButtonState("latest");

    if (!articles.length) {
        list.innerHTML = `<div class="news-empty">No headlines found. Try another topic.</div>`;
        return;
    }

    list.innerHTML = "";
    articles.slice(0, 10).forEach((article) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "news-headline-item";
        item.innerHTML = `
            <span class="news-select-pill">Select</span>
            <span class="news-headline-title">${escapeHtml(article.title || "Untitled headline")}</span>
            <span class="news-headline-meta">${escapeHtml(article.source || "News")} ${article.publishedAt ? `- ${escapeHtml(article.publishedAt)}` : ""}</span>
        `;

        item.addEventListener("click", () => {
            selectedArticle = article;
            document.querySelectorAll(".news-headline-item").forEach(el => {
                el.classList.remove("active");
                const pill = el.querySelector(".news-select-pill");
                if (pill) pill.textContent = "Select";
            });
            item.classList.add("active");
            const pill = item.querySelector(".news-select-pill");
            if (pill) pill.textContent = "Selected";
            updateSelectedHeadlineBox();
            document.getElementById("latest-tab")?.click();
            updateGenerateButtonState("latest");
        });

        list.appendChild(item);
    });
}

function updateSelectedHeadlineBox() {
    const box = document.getElementById("selected-headline-box");
    if (!box) return;

    if (!selectedArticle) {
        box.innerHTML = `<span class="text-muted">No headline selected yet. Click a headline in Step 1.</span>`;
        return;
    }

    box.innerHTML = `
        <div class="selected-headline-title">${escapeHtml(selectedArticle.title || "Selected headline")}</div>
        <div class="selected-headline-desc">${escapeHtml(selectedArticle.description || selectedArticle.source || "Ready to generate a short reel from this headline.")}</div>
    `;
}

function updateGenerateButtonState(activeInputTab = "latest") {
    const btnGenerate = document.getElementById("btn-generate");
    if (!btnGenerate) return;

    let ready = false;
    if (activeInputTab === "latest") {
        ready = Boolean(selectedArticle);
    } else if (activeInputTab === "search") {
        ready = Boolean(document.getElementById("input-query")?.value.trim());
    } else if (activeInputTab === "url") {
        ready = Boolean(document.getElementById("input-url")?.value.trim());
    }

    btnGenerate.disabled = !ready;
    let waitingText = "Select a Headline First";
    if (activeInputTab === "search") {
        waitingText = "Enter a Search Topic";
    } else if (activeInputTab === "url") {
        waitingText = "Paste an Article URL";
    }

    btnGenerate.innerHTML = ready
        ? `<i class="fa-solid fa-wand-magic-sparkles me-2"></i> Generate Reel`
        : `<i class="fa-solid fa-arrow-pointer me-2"></i> ${waitingText}`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// Progress Polling loop
function pollProgress(taskId) {
    const btnGenerate = document.getElementById("btn-generate");
    const progressBar = document.getElementById("progress-bar");
    const progressPerc = document.getElementById("progress-percentage");
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/reel/status/${taskId}`);
            const data = await response.json();
            
            if (!data.success) {
                clearInterval(interval);
                throw new Error(data.error || "Failed polling task.");
            }
            
            const task = data;
            const progress = task.progress;
            
            // Update Progress Bar
            progressBar.style.width = `${progress}%`;
            progressPerc.textContent = `${progress}%`;
            
            // Update active timeline step details
            updateTimeline(progress, task.stage);
            
            if (task.status === "completed") {
                clearInterval(interval);
                showToast("Render Finished", "Redirecting to your completed reel...", "success");
                setTimeout(() => {
                    window.location.href = `/result/${taskId}`;
                }, 1000);
            } else if (task.status === "failed") {
                clearInterval(interval);
                showToast("Generation Failed", task.error || "An error occurred during rendering.", "danger");
                btnGenerate.disabled = false;
                btnGenerate.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-2"></i>Generate Reel`;
            }
            
        } catch (err) {
            clearInterval(interval);
            showToast("Polling Error", err.message, "danger");
            btnGenerate.disabled = false;
            btnGenerate.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-2"></i>Generate Reel`;
        }
    }, 1500);
}

// Timeline State Manager
function updateTimeline(progress, currentStage) {
    const steps = [
        { id: "step-1", threshold: 10, title: "Initializing Workspace" },
        { id: "step-2", threshold: 25, title: "Fetching & Scraping Article" },
        { id: "step-3", threshold: 45, title: "AI Script Writing" },
        { id: "step-4", threshold: 60, title: "Voiceover Synthesis" },
        { id: "step-5", threshold: 80, title: "Imagery Generation" },
        { id: "step-6", threshold: 100, title: "Rendering Reel" }
    ];
    
    steps.forEach((step, idx) => {
        const el = document.getElementById(step.id);
        if (!el) return;
        
        const marker = el.querySelector(".step-marker");
        const desc = el.querySelector(".step-desc");
        
        if (progress >= step.threshold) {
            // Completed
            el.classList.remove("active");
            el.classList.add("completed");
            if (marker) marker.innerHTML = `<i class="fa-solid fa-check"></i>`;
        } else if (progress > (idx > 0 ? steps[idx-1].threshold : 0)) {
            // Currently active
            el.classList.remove("completed");
            el.classList.add("active");
            if (marker) marker.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
            if (desc && currentStage) desc.textContent = currentStage;
        } else {
            // Pending
            el.classList.remove("active", "completed");
            if (marker) marker.textContent = idx + 1;
        }
    });
}

// Actions inside the completed results page
function initResultActions() {
    const btnCopy = document.getElementById("btn-copy-script");
    const btnShare = document.getElementById("btn-share");
    
    if (btnCopy) {
        btnCopy.addEventListener("click", () => {
            const scriptText = btnCopy.getAttribute("data-script");
            navigator.clipboard.writeText(scriptText).then(() => {
                showToast("Copied!", "Narration script copied to clipboard.", "success");
            }).catch(err => {
                showToast("Copy Failed", "Failed to write to clipboard.", "danger");
            });
        });
    }
    
    if (btnShare) {
        btnShare.addEventListener("click", () => {
            const shareUrl = btnShare.getAttribute("data-url");
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast("Link Copied!", "Shareable result link copied to clipboard.", "success");
            }).catch(err => {
                showToast("Copy Failed", "Failed to write to clipboard.", "danger");
            });
        });
    }
}

// Toast Display Engine
function showToast(title, body, type = "info") {
    const toastEl = document.getElementById("status-toast");
    if (!toastEl) return;
    
    const titleEl = document.getElementById("toast-title");
    const bodyEl = document.getElementById("toast-body");
    
    // Choose color icon
    let icon = `<i class="fa-solid fa-circle-info text-secondary me-2"></i>`;
    if (type === "success") {
        icon = `<i class="fa-solid fa-circle-check text-success me-2"></i>`;
    } else if (type === "warning") {
        icon = `<i class="fa-solid fa-triangle-exclamation text-warning me-2"></i>`;
    } else if (type === "danger") {
        icon = `<i class="fa-solid fa-circle-xmark text-danger me-2"></i>`;
    }
    
    titleEl.innerHTML = `${icon} ${title}`;
    bodyEl.textContent = body;
    
    // Trigger Bootstrap Toast
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}
