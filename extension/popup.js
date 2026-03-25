
// Example: const API_BASE_URL = "https://youtube-intel-backend.onrender.com";
const API_BASE_URL = "http://127.0.0.1:8000";

let sentimentChartInstance = null;
let emotionRadarInstance = null;
let intentChartInstance = null;

document.addEventListener("DOMContentLoaded", async () => {
    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const titleEl = document.getElementById("ytTitle");
        const thumbEl = document.getElementById("ytThumb");
        const btn = document.getElementById("analyzeBtn");

        const isYT = tab && tab.url && (tab.url.includes("youtube.com/watch") || tab.url.includes("youtube.com/shorts/") || tab.url.includes("youtube.com/live/"));

        if (isYT) {
            let vidId = "";
            if (tab.url.includes("v=")) vidId = tab.url.split('v=')[1].split('&')[0];
            else if (tab.url.includes("/shorts/")) vidId = tab.url.split('/shorts/')[1].split('?')[0];
            else if (tab.url.includes("/live/")) vidId = tab.url.split('/live/')[1].split('?')[0];
            
            thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
            thumbEl.style.display = "block";
            
            let cleanTitle = tab.title.replace(/^\(\d+\)\s*/, "").replace(" - YouTube", "");
            titleEl.innerText = cleanTitle;
            btn.disabled = false;
        } else {
            if(titleEl) {
                titleEl.innerText = "Please open a YouTube Video or Short to begin.";
                titleEl.style.color = "#FF2E63";
            }
            if(btn) btn.disabled = true;
        }
    } catch(e) { }
});

document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
    });
});

document.getElementById("analyzeBtn").addEventListener("click", async () => {
    const btn = document.getElementById("analyzeBtn");
    const loader = document.getElementById("loader");
    const main = document.getElementById("mainContent");
    const error = document.getElementById("error");
    const landing = document.getElementById("landingPage");

    btn.disabled = true;
    if(landing) landing.classList.add("hidden");
    loader.classList.remove("hidden");
    main.classList.add("hidden");
    error.classList.add("hidden");

    if (sentimentChartInstance) sentimentChartInstance.destroy();
    if (emotionRadarInstance) emotionRadarInstance.destroy();
    if (intentChartInstance) intentChartInstance.destroy();

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        const isYT = tab && tab.url && (tab.url.includes("youtube.com/watch") || tab.url.includes("youtube.com/shorts/") || tab.url.includes("youtube.com/live/"));
        if (!isYT) throw new Error("Open a YouTube Video or Short First!");

        const res = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: tab.url })
        });

        const data = await res.json();
        if (data.error) throw new Error(data.error);

        const { stats, meta, comments, keywords, deep_data } = data;

        const displayTotal = meta.total || meta.analyzed_total || 0;
        document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
        document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
        const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
        const toxEl = document.getElementById("toxicScore");
        if(toxEl) {
            toxEl.innerText = toxicPct + "%";
            toxEl.className = "stat-label"; 
            if(toxicPct < 5) toxEl.classList.add("safe");
            else if(toxicPct < 20) toxEl.classList.add("warning");
            else toxEl.classList.add("danger");
        }

        const emos = stats.emotion_counts;
        const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
        document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

        const total = stats.positive + stats.neutral + stats.negative || 1;
        const p = Math.round((stats.positive / total) * 100);
        const n = Math.round((stats.negative / total) * 100);
        const neu = 100 - (p + n);

        document.getElementById("bar-pos").style.width = p + "%";
        document.getElementById("bar-neu").style.width = neu + "%";
        document.getElementById("bar-neg").style.width = n + "%";
        
        const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
        setTxt("lbl-pos", p + "%");
        setTxt("lbl-neu", neu + "%");
        setTxt("lbl-neg", n + "%");

        let verdict = "Mixed Reactions";
        let vColor = "#FFD700";
        if (toxicPct > 15) { verdict = "Controversial"; vColor = "#FF2E63"; }
        else if (p >= 60) { verdict = "Highly Loved"; vColor = "#00FF9D"; }
        else if (n >= 40) { verdict = "🛑 Poorly Received"; vColor = "#FF2E63"; }
        else if (neu >= 60) { verdict = "Informative"; vColor = "#00E5FF"; }
        else if (p > n) { verdict = "👍 Mostly Positive"; vColor = "#00FF9D"; }

        const vEl = document.getElementById("aiVerdict");
        if (vEl) { vEl.innerText = verdict; vEl.style.color = vColor; }

        let chatQ = "Quick Reactions ⚡";
        let cColor = "#00E5FF";
        if (meta.avg_len >= 25) { chatQ = "Deep Discussions "; cColor = "#8A2BE2"; }
        else if (meta.avg_len >= 12) { chatQ = "Good Engagement 💬"; cColor = "#00FF9D"; }
        else if (meta.avg_len < 5) { chatQ = "Spam / Short "; cColor = "#FF2E63"; }

        const cEl = document.getElementById("chatQuality");
        if (cEl) { cEl.innerText = chatQ; cEl.style.color = cColor; }

        const list = document.getElementById("commentsList");
        list.innerHTML = "";
        comments.forEach(c => {
            let sClass = "NEU";
            if(c.sentiment === "POSITIVE") sClass = "POS";
            if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
            list.innerHTML += `
                <div class="comment-card">
                    <div class="comment-header">
                        <div class="badge-group">
                            <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
                            <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="comment-body">"${c.text}"</div>
                </div>`;
        });

        const kwBox = document.getElementById("keywordCloud");
        if (kwBox && keywords && keywords.length > 0) {
            const maxCount = Math.max(...keywords.map(k => k[1]));
            const minCount = Math.min(...keywords.map(k => k[1]));
            const cloudColors = ['#00E5FF', '#00FF9D', '#FFD700', '#8A2BE2', '#FFFFFF', '#FF2E63'];
            const shuffledKeywords = [...keywords].sort(() => Math.random() - 0.5);

            kwBox.innerHTML = shuffledKeywords.map(([word, count], index) => {
                let fontSize = 12; 
                if (maxCount > minCount) {
                    fontSize = 12 + ((count - minCount) / (maxCount - minCount)) * 28; 
                } else { fontSize = 20; }
                let color = cloudColors[index % cloudColors.length];
                return `<span class="cloud-word" style="font-size: ${Math.round(fontSize)}px; color: ${color};" title="Used ${count} times">${word}</span>`;
            }).join(" ");
        }

        if (deep_data) {
            const phraseBox = document.getElementById("phraseCloud");
            if(phraseBox && deep_data.bigrams) {
                phraseBox.innerHTML = deep_data.bigrams.map(([k,v]) => `<span class="phrase-tag">"${k}"</span>`).join("");
            }

            const emojiBox = document.getElementById("emojiCloud");
            if(emojiBox && deep_data.emojis) {
                emojiBox.innerHTML = deep_data.emojis.map(([k,v]) => `<span>${k}</span>`).join("");
            }
        }

        renderCharts(stats, deep_data);

        const sumEl = document.getElementById("summaryText");
        if(sumEl) {
            sumEl.innerHTML = `<div style="padding: 10px; text-align: center;"><b style="color:#00E5FF;">⏳ AI is analyzing audience discussions and demands...</b></div>`;
        }
        
        fetch(`${API_BASE_URL}/summarize`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: tab.url })
        }).then(r=>r.json()).then(d => {
            if(sumEl) {
                let demandsHTML = "";
                
                if (d.demands && d.demands.length > 0) {
                    demandsHTML = d.demands.map(dem => 
                        `<div style="background: rgba(255, 46, 99, 0.1); border-left: 3px solid #FF2E63; padding: 8px; margin-top: 8px; font-size: 12px; color: #fff; border-radius: 0 4px 4px 0; font-style: italic;">
                            💬 "${dem}"
                        </div>`
                    ).join("");
                } else {
                    demandsHTML = `<div style="color: #888; font-size: 12px; margin-top: 8px;">ℹ️ No specific demands or requests found in this discussion.</div>`;
                }

                sumEl.innerHTML = `
                    <div style="text-align: left;">
                        <h4 style="color: #00E5FF; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🧠 Audience Discussion</h4>
                        <p style="color: #ddd; font-size: 13px; line-height: 1.5; margin-bottom: 15px;">${d.summary}</p>
                        
                        <h4 style="color: #FFD700; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🔥 Top Public Demands</h4>
                        ${demandsHTML}
                    </div>
                `;
            }
        }).catch(err => {
            if(sumEl) sumEl.innerHTML = "<b style='color:#FF2E63;'>Failed to analyze audience demands.</b>";
        });

        loader.classList.add("hidden");
        main.classList.remove("hidden");

    } catch (e) {
        loader.classList.add("hidden");
        error.innerText = e.message;
        error.classList.remove("hidden");
    } finally {
        btn.disabled = false;
    }
});

function renderCharts(stats, deep_data) {
    const radarEl = document.getElementById("emotionRadarChart");
    const sentEl = document.getElementById("sentimentChart");
    const intentEl = document.getElementById("intentChart");

    if (radarEl) {
        const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
        const data = labels.map(l => stats.emotion_counts[l]);
        
        emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
            type: 'radar',
            data: {
                labels: labels.map(l => l.toUpperCase()),
                datasets: [{
                    label: 'Intensity',
                    data: data,
                    backgroundColor: 'rgba(138, 43, 226, 0.2)',
                    borderColor: '#8A2BE2',
                    borderWidth: 2,
                    pointBackgroundColor: '#00E5FF'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#ccc', font: {size: 10} },
                        ticks: { display: false, callback: ()=>"" }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    if (sentEl) {
        sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
            type: 'doughnut',
            data: {
                labels: ['Pos', 'Neu', 'Neg'],
                datasets: [{
                    data: [stats.positive, stats.neutral, stats.negative],
                    backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
                    borderColor: '#050505',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '75%',
                plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
            }
        });
    }

    if (intentEl && deep_data && deep_data.intents) {
        intentChartInstance = new Chart(intentEl.getContext("2d"), {
            type: 'pie',
            data: {
                labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
                datasets: [{
                    data: [
                        deep_data.intents.question, 
                        deep_data.intents.appreciation, 
                        deep_data.intents.request, 
                        deep_data.intents.discussion
                    ],
                    backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
                    borderColor: '#050505',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10, font: {size: 9} } } }
            }
        });
    }
}