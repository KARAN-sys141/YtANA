// let sentimentChartInstance = null;
// let emotionRadarInstance = null;

// // TABS
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");

//     btn.disabled = true;
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open a YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords } = data;

//         // --- 1. SAFE METRICS UPDATE ---
//         // Checks both keys to prevent "undefined"
//         const totalCount = meta.total || meta.total_scanned || 0;
//         const avgLen = meta.avg_len || 0;

//         document.getElementById("totalComments").innerText = totalCount;
//         document.getElementById("avgLength").innerText = avgLen + " words";
        
//         // Toxicity
//         const toxicPct = Math.round((stats.toxic_count / (totalCount || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = ""; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         // Top Emotion
//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // --- 2. SENTIMENT BAR ---
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         document.getElementById("lbl-pos").innerText = p + "%";
//         document.getElementById("lbl-neu").innerText = neu + "%";
//         document.getElementById("lbl-neg").innerText = n + "%";

//         // --- 3. COMMENTS LIST ---
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // --- 4. KEYWORDS ---
//         const kwBox = document.getElementById("keywordCloud");
//         if(kwBox) {
//             kwBox.innerHTML = keywords.map(([k,v]) => `<span class="keyword-tag">#${k} <small>${v}</small></span>`).join("");
//         }

//         // --- 5. CHARTS ---
//         renderCharts(stats);

//         // --- 6. SUMMARY ---
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats) {
//     const ctxRadar = document.getElementById('emotionRadarChart').getContext('2d');
//     const ctxSent = document.getElementById('sentimentChart').getContext('2d');

//     const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//     const data = labels.map(l => stats.emotion_counts[l]);

//     emotionRadarInstance = new Chart(ctxRadar, {
//         type: 'radar',
//         data: {
//             labels: labels.map(l => l.toUpperCase()),
//             datasets: [{
//                 label: 'Intensity',
//                 data: data,
//                 backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                 borderColor: '#8A2BE2',
//                 borderWidth: 2,
//                 pointBackgroundColor: '#00E5FF'
//             }]
//         },
//         options: {
//             responsive: true,
//             maintainAspectRatio: false,
//             scales: {
//                 r: {
//                     angleLines: { color: 'rgba(255,255,255,0.1)' },
//                     grid: { color: 'rgba(255,255,255,0.1)' },
//                     pointLabels: { color: '#ccc', font: {size: 10} },
//                     ticks: { display: false, callback: ()=>"" }
//                 }
//             },
//             plugins: { legend: { display: false } }
//         }
//     });

//     sentimentChartInstance = new Chart(ctxSent, {
//         type: 'doughnut',
//         data: {
//             labels: ['Pos', 'Neu', 'Neg'],
//             datasets: [{
//                 data: [stats.positive, stats.neutral, stats.negative],
//                 backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                 borderColor: '#050505',
//                 borderWidth: 2
//             }]
//         },
//         options: {
//             responsive: true,
//             maintainAspectRatio: false,
//             cutout: '75%',
//             plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//         }
//     });
// }





// let sentimentChartInstance = null;
// let emotionRadarInstance = null;

// // TABS
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");

//     btn.disabled = true;
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords } = data;

//         // --- 1. DISPLAY TRUE NUMBERS ---
//         // Use true_total if available, else analyzed count
//         const displayTotal = meta.total || meta.analyzed_total || 0;        
//         // Formatter for numbers (e.g. 28,400)
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         // Toxicity (Based on analyzed sample)
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = ""; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         // Top Emotion
//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // 2. SENTIMENT BAR
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         // Safe setters
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // 3. COMMENTS
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // 4. KEYWORDS
//         const kwBox = document.getElementById("keywordCloud");
//         if(kwBox) {
//             kwBox.innerHTML = keywords.map(([k,v]) => `<span class="keyword-tag">#${k} <small>${v}</small></span>`).join("");
//         }

//         // 5. CHARTS
//         renderCharts(stats);

//         // 6. SUMMARY
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }
// }





// let sentimentChartInstance = null;
// let emotionRadarInstance = null;

// // TABS
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");

//     btn.disabled = true;
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords } = data;

//         // --- 1. DISPLAY TRUE NUMBERS ---
//         // Use true_total if available, else analyzed count
//         const displayTotal = meta.total || meta.analyzed_total || 0;
        
//         // Formatter for numbers (e.g. 28,400)
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         // Toxicity (Based on analyzed sample)
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = ""; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         // Top Emotion
//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // 2. SENTIMENT BAR
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         // Safe setters
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // 3. COMMENTS
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // 4. KEYWORDS
//         const kwBox = document.getElementById("keywordCloud");
//         if(kwBox) {
//             kwBox.innerHTML = keywords.map(([k,v]) => `<span class="keyword-tag">#${k} <small>${v}</small></span>`).join("");
//         }

//         // 5. CHARTS
//         renderCharts(stats);

//         // 6. SUMMARY
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }
// }




// let sentimentChartInstance = null;
// let emotionRadarInstance = null;
// let intentChartInstance = null;

// // --- 🚀 NEW: INITIALIZE LANDING PAGE ---
// document.addEventListener("DOMContentLoaded", async () => {
//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         const titleEl = document.getElementById("ytTitle");
//         const thumbEl = document.getElementById("ytThumb");
//         const btn = document.getElementById("analyzeBtn");

//         if (tab && tab.url && tab.url.includes("youtube.com/watch")) {
//             // Extract Video ID directly from URL
//             const urlParams = new URLSearchParams(new URL(tab.url).search);
//             const vidId = urlParams.get("v") || tab.url.split('v=')[1].split('&')[0];
            
//             // Build High-Quality Thumbnail URL (YouTube default structure)
//             thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
//             thumbEl.style.display = "block";
            
//             // Clean and set Title
//             let cleanTitle = tab.title.replace(" - YouTube", "");
//             titleEl.innerText = cleanTitle;
            
//             // Enable Button
//             btn.disabled = false;
//         } else {
//             titleEl.innerText = "⚠️ Please open a YouTube Video to begin.";
//             titleEl.style.color = "#FF2E63";
//             btn.disabled = true;
//         }
//     } catch(e) {
//         console.log("Not on a valid tab.");
//     }
// });

// // --- TABS LOGIC ---
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// // --- MAIN ANALYZE LOGIC ---
// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");
//     const landing = document.getElementById("landingPage"); // Target new landing page

//     btn.disabled = true;
//     landing.classList.add("hidden"); // Hide Landing Page
//     loader.classList.remove("hidden"); // Show Loader
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();
//     if (intentChartInstance) intentChartInstance.destroy(); // Add this line

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords } = data;

//         // 1. DISPLAY TRUE NUMBERS
//         const displayTotal = meta.total || meta.analyzed_total || 0;
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         // Toxicity
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = ""; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         // Top Emotion
//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // 2. SENTIMENT BAR
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // --- 🚀 NEW: STEP 2 (AI VERDICT & CHAT QUALITY) ---
        
//         // 1. Calculate AI Verdict
//         let verdict = "📊 Mixed Reactions";
//         let verdictColor = "#FFD700"; // Yellow
        
//         if (toxicPct > 15) {
//             verdict = "⚠️ Controversial";
//             verdictColor = "#FF2E63"; // Red
//         } else if (p >= 60) {
//             verdict = "💎 Highly Loved";
//             verdictColor = "#00FF9D"; // Green
//         } else if (n >= 40) {
//             verdict = "🛑 Poorly Received";
//             verdictColor = "#FF2E63"; // Red
//         } else if (neu >= 60) {
//             verdict = "📚 Informative";
//             verdictColor = "#00E5FF"; // Cyan
//         } else if (p > n) {
//             verdict = "👍 Mostly Positive";
//             verdictColor = "#00FF9D"; // Green
//         }

//         const verdictEl = document.getElementById("aiVerdict");
//         if (verdictEl) {
//             verdictEl.innerText = verdict;
//             verdictEl.style.color = verdictColor;
//         }

//         // 2. Calculate Chat Quality (Based on Avg Length)
//         let chatQuality = "Quick Reactions ⚡";
//         let chatColor = "#00E5FF";
        
//         const avgL = meta.avg_len || 0;
//         if (avgL >= 25) {
//             chatQuality = "Deep Discussions 🧠";
//             chatColor = "#8A2BE2"; // Purple
//         } else if (avgL >= 12) {
//             chatQuality = "Good Engagement 💬";
//             chatColor = "#00FF9D"; // Green
//         } else if (avgL < 5) {
//             chatQuality = "Spam / One-liners 🤖";
//             chatColor = "#FF2E63"; // Red
//         }

//         const chatQualEl = document.getElementById("chatQuality");
//         if (chatQualEl) {
//             chatQualEl.innerText = chatQuality;
//             chatQualEl.style.color = chatColor;
//         }
//         // --- END STEP 2 ---

//         // 3. COMMENTS
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // 4. KEYWORDS
//         const kwBox = document.getElementById("keywordCloud");
//         if(kwBox) {
//             kwBox.innerHTML = keywords.map(([k,v]) => `<span class="keyword-tag">#${k} <small>${v}</small></span>`).join("");
//         }

//         // 🚀 NEW: POPULATE DEEP DATA UI
//         window.deep_data_global = data.deep_data; // Store globally for chart

//         const phraseBox = document.getElementById("phraseCloud");
//         if(phraseBox && data.deep_data.bigrams) {
//             phraseBox.innerHTML = data.deep_data.bigrams.map(([k,v]) => `<span class="phrase-tag">"${k}"</span>`).join("");
//         }

//         const emojiBox = document.getElementById("emojiCloud");
//         if(emojiBox && data.deep_data.emojis) {
//             emojiBox.innerHTML = data.deep_data.emojis.map(([k,v]) => `<span>${k}</span>`).join("");
//         }

//         // 5. CHARTS
//         renderCharts(stats);

//         // 6. SUMMARY
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden"); // Show main dashboard

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }

//     // --- 🚀 NEW: INTENT PIE CHART ---
//     const ctxIntent = document.getElementById('intentChart');
//     if (ctxIntent && window.deep_data_global) { // Using a global or direct reference
//         intentChartInstance = new Chart(ctxIntent.getContext("2d"), {
//             type: 'pie',
//             data: {
//                 labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
//                 datasets: [{
//                     data: [
//                         window.deep_data_global.intents.question, 
//                         window.deep_data_global.intents.appreciation, 
//                         window.deep_data_global.intents.request, 
//                         window.deep_data_global.intents.discussion
//                     ],
//                     backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
//                     borderWidth: 0
//                 }]  
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }
// }



// let sentimentChartInstance = null;
// let emotionRadarInstance = null;
// let intentChartInstance = null;

// // --- 🚀 STEP 1: LANDING PAGE LOGIC ---
// document.addEventListener("DOMContentLoaded", async () => {
//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         const titleEl = document.getElementById("ytTitle");
//         const thumbEl = document.getElementById("ytThumb");
//         const btn = document.getElementById("analyzeBtn");

//         if (tab && tab.url && tab.url.includes("youtube.com/watch")) {
//             const urlParams = new URLSearchParams(new URL(tab.url).search);
//             const vidId = urlParams.get("v") || tab.url.split('v=')[1].split('&')[0];
            
//             thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
//             thumbEl.style.display = "block";
            
//             let cleanTitle = tab.title.replace(" - YouTube", "");
//             titleEl.innerText = cleanTitle;
//             btn.disabled = false;
//         } else {
//             titleEl.innerText = "⚠️ Please open a YouTube Video to begin.";
//             titleEl.style.color = "#FF2E63";
//             btn.disabled = true;
//         }
//     } catch(e) { }
// });

// // TABS
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");
//     const landing = document.getElementById("landingPage");

//     btn.disabled = true;
//     landing.classList.add("hidden");
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();
//     if (intentChartInstance) intentChartInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords, deep_data } = data;

//         // --- 1. DISPLAY TRUE NUMBERS ---
//         const displayTotal = meta.total || meta.analyzed_total || 0;
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         // Toxicity 
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = "stat-label"; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         // Top Emotion
//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // 2. SENTIMENT BAR
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // --- 🚀 STEP 2: AI VERDICT & CHAT QUALITY ---
//         let verdict = "📊 Mixed Reactions";
//         let vColor = "#FFD700";
//         if (toxicPct > 15) { verdict = "⚠️ Controversial"; vColor = "#FF2E63"; }
//         else if (p >= 60) { verdict = "💎 Highly Loved"; vColor = "#00FF9D"; }
//         else if (n >= 40) { verdict = "🛑 Poorly Received"; vColor = "#FF2E63"; }
//         else if (neu >= 60) { verdict = "📚 Informative"; vColor = "#00E5FF"; }
//         else if (p > n) { verdict = "👍 Mostly Positive"; vColor = "#00FF9D"; }

//         const vEl = document.getElementById("aiVerdict");
//         if (vEl) { vEl.innerText = verdict; vEl.style.color = vColor; }

//         let chatQ = "Quick Reactions ⚡";
//         let cColor = "#00E5FF";
//         if (meta.avg_len >= 25) { chatQ = "Deep Discussions 🧠"; cColor = "#8A2BE2"; }
//         else if (meta.avg_len >= 12) { chatQ = "Good Engagement 💬"; cColor = "#00FF9D"; }
//         else if (meta.avg_len < 5) { chatQ = "Spam / Short 🤖"; cColor = "#FF2E63"; }

//         const cEl = document.getElementById("chatQuality");
//         if (cEl) { cEl.innerText = chatQ; cEl.style.color = cColor; }

//         // 3. COMMENTS
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // 4. ☁️ TRUE WORD CLOUD (Dynamic Size & Colors)
//         const kwBox = document.getElementById("keywordCloud");
//         if (kwBox && keywords && keywords.length > 0) {
//             // Sabse bada aur sabse chhota count nikalo font scaling ke liye
//             const maxCount = Math.max(...keywords.map(k => k[1]));
//             const minCount = Math.min(...keywords.map(k => k[1]));
            
//             // Apne extension ke theme colors
//             const cloudColors = ['#00E5FF', '#00FF9D', '#FFD700', '#8A2BE2', '#FFFFFF', '#FF2E63'];
            
//             // Words ko thoda mix (shuffle) kar dete hain taaki original "cloud" wali feel aaye
//             const shuffledKeywords = [...keywords].sort(() => Math.random() - 0.5);

//             kwBox.innerHTML = shuffledKeywords.map(([word, count], index) => {
//                 // Font Size Math: Min 12px, Max 40px
//                 let fontSize = 12; 
//                 if (maxCount > minCount) {
//                     fontSize = 12 + ((count - minCount) / (maxCount - minCount)) * 28; 
//                 } else {
//                     fontSize = 20; // Agar sabka count barabar ho
//                 }
                
//                 // Har word ko ek theme color do
//                 let color = cloudColors[index % cloudColors.length];
                
//                 return `<span class="cloud-word" style="font-size: ${Math.round(fontSize)}px; color: ${color};" title="Used ${count} times">${word}</span>`;
//             }).join(" ");
//         } else if (kwBox) {
//             kwBox.innerHTML = "<span style='color: #888; font-size: 12px;'>Not enough words.</span>";
//         }

//         // 5. CHARTS
//         renderCharts(stats);

//         // 6. SUMMARY
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");
//     const intentEl = document.getElementById("intentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }

//     // --- 🚀 NEW: INTENT CHART RENDER ---
//     if (intentEl && window.deep_data_global) {
//         intentChartInstance = new Chart(intentEl.getContext("2d"), {
//             type: 'pie',
//             data: {
//                 labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
//                 datasets: [{
//                     data: [
//                         window.deep_data_global.intents.question, 
//                         window.deep_data_global.intents.appreciation, 
//                         window.deep_data_global.intents.request, 
//                         window.deep_data_global.intents.discussion
//                     ],
//                     backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
//                     borderColor: '#050505',
//                     borderWidth: 1
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10, font: {size: 9} } } }
//             }
//         });
//     }
// }


// let sentimentChartInstance = null;
// let emotionRadarInstance = null;
// let intentChartInstance = null;

// // --- 🚀 LANDING PAGE LOGIC ---
// document.addEventListener("DOMContentLoaded", async () => {
//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         const titleEl = document.getElementById("ytTitle");
//         const thumbEl = document.getElementById("ytThumb");
//         const btn = document.getElementById("analyzeBtn");

//         if (tab && tab.url && tab.url.includes("youtube.com/watch")) {
//             const urlParams = new URLSearchParams(new URL(tab.url).search);
//             const vidId = urlParams.get("v") || tab.url.split('v=')[1].split('&')[0];
            
//             thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
//             thumbEl.style.display = "block";
            
//             let cleanTitle = tab.title.replace(" - YouTube", "");
//             titleEl.innerText = cleanTitle;
//             btn.disabled = false;
//         } else {
//             if(titleEl) {
//                 titleEl.innerText = "⚠️ Please open a YouTube Video to begin.";
//                 titleEl.style.color = "#FF2E63";
//             }
//             if(btn) btn.disabled = true;
//         }
//     } catch(e) { }
// });

// // --- TABS LOGIC ---
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// // --- MAIN ANALYZE LOGIC ---
// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");
//     const landing = document.getElementById("landingPage");

//     btn.disabled = true;
//     if(landing) landing.classList.add("hidden");
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();
//     if (intentChartInstance) intentChartInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         // 🔴 FIX: Extracting deep_data properly
//         const { stats, meta, comments, keywords, deep_data } = data;

//         // --- 1. METRICS ---
//         const displayTotal = meta.total || meta.analyzed_total || 0;
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = "stat-label"; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // --- 2. SENTIMENT BAR ---
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // --- 3. AI VERDICT & CHAT QUALITY ---
//         let verdict = "📊 Mixed Reactions";
//         let vColor = "#FFD700";
//         if (toxicPct > 15) { verdict = "⚠️ Controversial"; vColor = "#FF2E63"; }
//         else if (p >= 60) { verdict = "💎 Highly Loved"; vColor = "#00FF9D"; }
//         else if (n >= 40) { verdict = "🛑 Poorly Received"; vColor = "#FF2E63"; }
//         else if (neu >= 60) { verdict = "📚 Informative"; vColor = "#00E5FF"; }
//         else if (p > n) { verdict = "👍 Mostly Positive"; vColor = "#00FF9D"; }

//         const vEl = document.getElementById("aiVerdict");
//         if (vEl) { vEl.innerText = verdict; vEl.style.color = vColor; }

//         let chatQ = "Quick Reactions ⚡";
//         let cColor = "#00E5FF";
//         if (meta.avg_len >= 25) { chatQ = "Deep Discussions 🧠"; cColor = "#8A2BE2"; }
//         else if (meta.avg_len >= 12) { chatQ = "Good Engagement 💬"; cColor = "#00FF9D"; }
//         else if (meta.avg_len < 5) { chatQ = "Spam / Short 🤖"; cColor = "#FF2E63"; }

//         const cEl = document.getElementById("chatQuality");
//         if (cEl) { cEl.innerText = chatQ; cEl.style.color = cColor; }

//         // --- 4. COMMENTS LIST ---
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // --- 5. ☁️ TRUE WORD CLOUD ---
//         const kwBox = document.getElementById("keywordCloud");
//         if (kwBox && keywords && keywords.length > 0) {
//             const maxCount = Math.max(...keywords.map(k => k[1]));
//             const minCount = Math.min(...keywords.map(k => k[1]));
//             const cloudColors = ['#00E5FF', '#00FF9D', '#FFD700', '#8A2BE2', '#FFFFFF', '#FF2E63'];
//             const shuffledKeywords = [...keywords].sort(() => Math.random() - 0.5);

//             kwBox.innerHTML = shuffledKeywords.map(([word, count], index) => {
//                 let fontSize = 12; 
//                 if (maxCount > minCount) {
//                     fontSize = 12 + ((count - minCount) / (maxCount - minCount)) * 28; 
//                 } else { fontSize = 20; }
//                 let color = cloudColors[index % cloudColors.length];
//                 return `<span class="cloud-word" style="font-size: ${Math.round(fontSize)}px; color: ${color};" title="Used ${count} times">${word}</span>`;
//             }).join(" ");
//         }

//         // --- 6. 🚀 SAFE DEEP DATA POPULATION ---
//         if (deep_data) {
//             const phraseBox = document.getElementById("phraseCloud");
//             if(phraseBox && deep_data.bigrams) {
//                 phraseBox.innerHTML = deep_data.bigrams.map(([k,v]) => `<span class="phrase-tag">"${k}"</span>`).join("");
//             }

//             const emojiBox = document.getElementById("emojiCloud");
//             if(emojiBox && deep_data.emojis) {
//                 emojiBox.innerHTML = deep_data.emojis.map(([k,v]) => `<span>${k}</span>`).join("");
//             }
//         }

//         // --- 7. CHARTS (Pass deep_data safely) ---
//         renderCharts(stats, deep_data);

//         // --- 8. SUMMARY ---
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             const el = document.getElementById("summaryText");
//             if(el) el.innerText = d.summary;
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// // 🔴 FIX: Accepting deep_data as a parameter to avoid global variable crashes
// function renderCharts(stats, deep_data) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");
//     const intentEl = document.getElementById("intentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false, cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }

//     // --- 🚀 INTENT CHART (Safe Render) ---
//     if (intentEl && deep_data && deep_data.intents) {
//         intentChartInstance = new Chart(intentEl.getContext("2d"), {
//             type: 'pie',
//             data: {
//                 labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
//                 datasets: [{
//                     data: [
//                         deep_data.intents.question, 
//                         deep_data.intents.appreciation, 
//                         deep_data.intents.request, 
//                         deep_data.intents.discussion
//                     ],
//                     backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
//                     borderColor: '#050505',
//                     borderWidth: 1
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10, font: {size: 9} } } }
//             }
//         });
//     }
// }


// let sentimentChartInstance = null;
// let emotionRadarInstance = null;
// let intentChartInstance = null;

// // --- 🚀 LANDING PAGE LOGIC ---
// document.addEventListener("DOMContentLoaded", async () => {
//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         const titleEl = document.getElementById("ytTitle");
//         const thumbEl = document.getElementById("ytThumb");
//         const btn = document.getElementById("analyzeBtn");

//         if (tab && tab.url && tab.url.includes("youtube.com/watch")) {
//             const urlParams = new URLSearchParams(new URL(tab.url).search);
//             const vidId = urlParams.get("v") || tab.url.split('v=')[1].split('&')[0];
            
//             thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
//             thumbEl.style.display = "block";
            
//             let cleanTitle = tab.title.replace(" - YouTube", "");
//             titleEl.innerText = cleanTitle;
//             btn.disabled = false;
//         } else {
//             if(titleEl) {
//                 titleEl.innerText = "⚠️ Please open a YouTube Video to begin.";
//                 titleEl.style.color = "#FF2E63";
//             }
//             if(btn) btn.disabled = true;
//         }
//     } catch(e) { }
// });

// // --- TABS LOGIC ---
// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// // --- MAIN ANALYZE LOGIC ---
// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");
//     const landing = document.getElementById("landingPage");

//     btn.disabled = true;
//     if(landing) landing.classList.add("hidden");
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();
//     if (intentChartInstance) intentChartInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         if (!tab.url.includes("youtube.com/watch")) throw new Error("⚠️ Open YouTube Video First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords, deep_data } = data;

//         // --- 1. METRICS ---
//         const displayTotal = meta.total || meta.analyzed_total || 0;
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = "stat-label"; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         // --- 2. SENTIMENT BAR ---
//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         // --- 3. AI VERDICT & CHAT QUALITY ---
//         let verdict = "📊 Mixed Reactions";
//         let vColor = "#FFD700";
//         if (toxicPct > 15) { verdict = "⚠️ Controversial"; vColor = "#FF2E63"; }
//         else if (p >= 60) { verdict = "💎 Highly Loved"; vColor = "#00FF9D"; }
//         else if (n >= 40) { verdict = "🛑 Poorly Received"; vColor = "#FF2E63"; }
//         else if (neu >= 60) { verdict = "📚 Informative"; vColor = "#00E5FF"; }
//         else if (p > n) { verdict = "👍 Mostly Positive"; vColor = "#00FF9D"; }

//         const vEl = document.getElementById("aiVerdict");
//         if (vEl) { vEl.innerText = verdict; vEl.style.color = vColor; }

//         let chatQ = "Quick Reactions ⚡";
//         let cColor = "#00E5FF";
//         if (meta.avg_len >= 25) { chatQ = "Deep Discussions 🧠"; cColor = "#8A2BE2"; }
//         else if (meta.avg_len >= 12) { chatQ = "Good Engagement 💬"; cColor = "#00FF9D"; }
//         else if (meta.avg_len < 5) { chatQ = "Spam / Short 🤖"; cColor = "#FF2E63"; }

//         const cEl = document.getElementById("chatQuality");
//         if (cEl) { cEl.innerText = chatQ; cEl.style.color = cColor; }

//         // --- 4. COMMENTS LIST ---
//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         // --- 5. ☁️ TRUE WORD CLOUD ---
//         const kwBox = document.getElementById("keywordCloud");
//         if (kwBox && keywords && keywords.length > 0) {
//             const maxCount = Math.max(...keywords.map(k => k[1]));
//             const minCount = Math.min(...keywords.map(k => k[1]));
//             const cloudColors = ['#00E5FF', '#00FF9D', '#FFD700', '#8A2BE2', '#FFFFFF', '#FF2E63'];
//             const shuffledKeywords = [...keywords].sort(() => Math.random() - 0.5);

//             kwBox.innerHTML = shuffledKeywords.map(([word, count], index) => {
//                 let fontSize = 12; 
//                 if (maxCount > minCount) {
//                     fontSize = 12 + ((count - minCount) / (maxCount - minCount)) * 28; 
//                 } else { fontSize = 20; }
//                 let color = cloudColors[index % cloudColors.length];
//                 return `<span class="cloud-word" style="font-size: ${Math.round(fontSize)}px; color: ${color};" title="Used ${count} times">${word}</span>`;
//             }).join(" ");
//         }

//         // --- 6. 🚀 SAFE DEEP DATA POPULATION ---
//         if (deep_data) {
//             const phraseBox = document.getElementById("phraseCloud");
//             if(phraseBox && deep_data.bigrams) {
//                 phraseBox.innerHTML = deep_data.bigrams.map(([k,v]) => `<span class="phrase-tag">"${k}"</span>`).join("");
//             }

//             const emojiBox = document.getElementById("emojiCloud");
//             if(emojiBox && deep_data.emojis) {
//                 emojiBox.innerHTML = deep_data.emojis.map(([k,v]) => `<span>${k}</span>`).join("");
//             }
//         }

//         // --- 7. CHARTS ---
//         renderCharts(stats, deep_data);

//         // --- 8. ⏳ SUMMARY (Updated Waiting Text) ---
//         const sumEl = document.getElementById("summaryText");
//         if(sumEl) {
//             sumEl.innerHTML = "<b style='color:#00E5FF;'>⏳ AI is reading the video... Please wait 15-20 seconds.</b>";
//         }
        
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             if(sumEl) sumEl.innerText = d.summary;
//         }).catch(err => {
//             if(sumEl) sumEl.innerText = "⚠️ Failed to connect to AI server.";
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats, deep_data) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");
//     const intentEl = document.getElementById("intentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false, cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }

//     // --- 🚀 INTENT CHART ---
//     if (intentEl && deep_data && deep_data.intents) {
//         intentChartInstance = new Chart(intentEl.getContext("2d"), {
//             type: 'pie',
//             data: {
//                 labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
//                 datasets: [{
//                     data: [
//                         deep_data.intents.question, 
//                         deep_data.intents.appreciation, 
//                         deep_data.intents.request, 
//                         deep_data.intents.discussion
//                     ],
//                     backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
//                     borderColor: '#050505',
//                     borderWidth: 1
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10, font: {size: 9} } } }
//             }
//         });
//     }
// }




// let sentimentChartInstance = null;
// let emotionRadarInstance = null;
// let intentChartInstance = null;

// document.addEventListener("DOMContentLoaded", async () => {
//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
//         const titleEl = document.getElementById("ytTitle");
//         const thumbEl = document.getElementById("ytThumb");
//         const btn = document.getElementById("analyzeBtn");

//         const isYT = tab && tab.url && (tab.url.includes("youtube.com/watch") || tab.url.includes("youtube.com/shorts/") || tab.url.includes("youtube.com/live/"));

//         if (isYT) {
//             let vidId = "";
//             if (tab.url.includes("v=")) vidId = tab.url.split('v=')[1].split('&')[0];
//             else if (tab.url.includes("/shorts/")) vidId = tab.url.split('/shorts/')[1].split('?')[0];
//             else if (tab.url.includes("/live/")) vidId = tab.url.split('/live/')[1].split('?')[0];
            
//             thumbEl.src = `https://i.ytimg.com/vi/${vidId}/hqdefault.jpg`;
//             thumbEl.style.display = "block";
            
//             let cleanTitle = tab.title.replace(/^\(\d+\)\s*/, "").replace(" - YouTube", "");
//             titleEl.innerText = cleanTitle;
//             btn.disabled = false;
//         } else {
//             if(titleEl) {
//                 titleEl.innerText = "Please open a YouTube Video or Short to begin.";
//                 titleEl.style.color = "#FF2E63";
//             }
//             if(btn) btn.disabled = true;
//         }
//     } catch(e) { }
// });

// document.querySelectorAll(".tab-btn").forEach(btn => {
//     btn.addEventListener("click", () => {
//         document.querySelectorAll(".tab-btn, .tab-content").forEach(el => el.classList.remove("active"));
//         btn.classList.add("active");
//         document.getElementById(btn.dataset.tab).classList.add("active");
//     });
// });

// document.getElementById("analyzeBtn").addEventListener("click", async () => {
//     const btn = document.getElementById("analyzeBtn");
//     const loader = document.getElementById("loader");
//     const main = document.getElementById("mainContent");
//     const error = document.getElementById("error");
//     const landing = document.getElementById("landingPage");

//     btn.disabled = true;
//     if(landing) landing.classList.add("hidden");
//     loader.classList.remove("hidden");
//     main.classList.add("hidden");
//     error.classList.add("hidden");

//     if (sentimentChartInstance) sentimentChartInstance.destroy();
//     if (emotionRadarInstance) emotionRadarInstance.destroy();
//     if (intentChartInstance) intentChartInstance.destroy();

//     try {
//         let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
//         const isYT = tab && tab.url && (tab.url.includes("youtube.com/watch") || tab.url.includes("youtube.com/shorts/") || tab.url.includes("youtube.com/live/"));
//         if (!isYT) throw new Error("Open a YouTube Video or Short First!");

//         const res = await fetch("http://127.0.0.1:8000/analyze", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         });

//         const data = await res.json();
//         if (data.error) throw new Error(data.error);

//         const { stats, meta, comments, keywords, deep_data } = data;

//         const displayTotal = meta.total || meta.analyzed_total || 0;
//         document.getElementById("totalComments").innerText = new Intl.NumberFormat().format(displayTotal);
//         document.getElementById("avgLength").innerText = (meta.avg_len || 0) + " words";
        
//         const toxicPct = Math.round((stats.toxic_count / (meta.analyzed_total || 1)) * 100);
//         const toxEl = document.getElementById("toxicScore");
//         if(toxEl) {
//             toxEl.innerText = toxicPct + "%";
//             toxEl.className = "stat-label"; 
//             if(toxicPct < 5) toxEl.classList.add("safe");
//             else if(toxicPct < 20) toxEl.classList.add("warning");
//             else toxEl.classList.add("danger");
//         }

//         const emos = stats.emotion_counts;
//         const topEmo = Object.keys(emos).sort((a,b) => emos[b] - emos[a])[0];
//         document.getElementById("topEmotion").innerText = (topEmo || "NEUTRAL").toUpperCase();

//         const total = stats.positive + stats.neutral + stats.negative || 1;
//         const p = Math.round((stats.positive / total) * 100);
//         const n = Math.round((stats.negative / total) * 100);
//         const neu = 100 - (p + n);

//         document.getElementById("bar-pos").style.width = p + "%";
//         document.getElementById("bar-neu").style.width = neu + "%";
//         document.getElementById("bar-neg").style.width = n + "%";
        
//         const setTxt = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
//         setTxt("lbl-pos", p + "%");
//         setTxt("lbl-neu", neu + "%");
//         setTxt("lbl-neg", n + "%");

//         let verdict = "Mixed Reactions";
//         let vColor = "#FFD700";
//         if (toxicPct > 15) { verdict = "Controversial"; vColor = "#FF2E63"; }
//         else if (p >= 60) { verdict = "Highly Loved"; vColor = "#00FF9D"; }
//         else if (n >= 40) { verdict = "🛑 Poorly Received"; vColor = "#FF2E63"; }
//         else if (neu >= 60) { verdict = "Informative"; vColor = "#00E5FF"; }
//         else if (p > n) { verdict = "👍 Mostly Positive"; vColor = "#00FF9D"; }

//         const vEl = document.getElementById("aiVerdict");
//         if (vEl) { vEl.innerText = verdict; vEl.style.color = vColor; }

//         let chatQ = "Quick Reactions ⚡";
//         let cColor = "#00E5FF";
//         if (meta.avg_len >= 25) { chatQ = "Deep Discussions "; cColor = "#8A2BE2"; }
//         else if (meta.avg_len >= 12) { chatQ = "Good Engagement 💬"; cColor = "#00FF9D"; }
//         else if (meta.avg_len < 5) { chatQ = "Spam / Short "; cColor = "#FF2E63"; }

//         const cEl = document.getElementById("chatQuality");
//         if (cEl) { cEl.innerText = chatQ; cEl.style.color = cColor; }

//         const list = document.getElementById("commentsList");
//         list.innerHTML = "";
//         comments.forEach(c => {
//             let sClass = "NEU";
//             if(c.sentiment === "POSITIVE") sClass = "POS";
//             if(c.sentiment === "NEGATIVE") sClass = "NEG";
            
//             list.innerHTML += `
//                 <div class="comment-card">
//                     <div class="comment-header">
//                         <div class="badge-group">
//                             <span class="badge badge-sent ${sClass}">${c.sentiment.substr(0,3)}</span>
//                             <span class="badge badge-emo">${c.emotion.toUpperCase()}</span>
//                         </div>
//                     </div>
//                     <div class="comment-body">"${c.text}"</div>
//                 </div>`;
//         });

//         const kwBox = document.getElementById("keywordCloud");
//         if (kwBox && keywords && keywords.length > 0) {
//             const maxCount = Math.max(...keywords.map(k => k[1]));
//             const minCount = Math.min(...keywords.map(k => k[1]));
//             const cloudColors = ['#00E5FF', '#00FF9D', '#FFD700', '#8A2BE2', '#FFFFFF', '#FF2E63'];
//             const shuffledKeywords = [...keywords].sort(() => Math.random() - 0.5);

//             kwBox.innerHTML = shuffledKeywords.map(([word, count], index) => {
//                 let fontSize = 12; 
//                 if (maxCount > minCount) {
//                     fontSize = 12 + ((count - minCount) / (maxCount - minCount)) * 28; 
//                 } else { fontSize = 20; }
//                 let color = cloudColors[index % cloudColors.length];
//                 return `<span class="cloud-word" style="font-size: ${Math.round(fontSize)}px; color: ${color};" title="Used ${count} times">${word}</span>`;
//             }).join(" ");
//         }

//         if (deep_data) {
//             const phraseBox = document.getElementById("phraseCloud");
//             if(phraseBox && deep_data.bigrams) {
//                 phraseBox.innerHTML = deep_data.bigrams.map(([k,v]) => `<span class="phrase-tag">"${k}"</span>`).join("");
//             }

//             const emojiBox = document.getElementById("emojiCloud");
//             if(emojiBox && deep_data.emojis) {
//                 emojiBox.innerHTML = deep_data.emojis.map(([k,v]) => `<span>${k}</span>`).join("");
//             }
//         }

//         renderCharts(stats, deep_data);

//         const sumEl = document.getElementById("summaryText");
//         if(sumEl) {
//             sumEl.innerHTML = `<div style="padding: 10px; text-align: center;"><b style="color:#00E5FF;">⏳ AI is analyzing audience discussions and demands...</b></div>`;
//         }
        
//         fetch("http://127.0.0.1:8000/summarize", {
//             method: "POST", headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ video_id: tab.url })
//         }).then(r=>r.json()).then(d => {
//             if(sumEl) {
//                 let demandsHTML = "";
                
//                 if (d.demands && d.demands.length > 0) {
//                     demandsHTML = d.demands.map(dem => 
//                         `<div style="background: rgba(255, 46, 99, 0.1); border-left: 3px solid #FF2E63; padding: 8px; margin-top: 8px; font-size: 12px; color: #fff; border-radius: 0 4px 4px 0; font-style: italic;">
//                             💬 "${dem}"
//                         </div>`
//                     ).join("");
//                 } else {
//                     demandsHTML = `<div style="color: #888; font-size: 12px; margin-top: 8px;">ℹ️ No specific demands or requests found in this discussion.</div>`;
//                 }

//                 sumEl.innerHTML = `
//                     <div style="text-align: left;">
//                         <h4 style="color: #00E5FF; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🧠 Audience Discussion</h4>
//                         <p style="color: #ddd; font-size: 13px; line-height: 1.5; margin-bottom: 15px;">${d.summary}</p>
                        
//                         <h4 style="color: #FFD700; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🔥 Top Public Demands</h4>
//                         ${demandsHTML}
//                     </div>
//                 `;
//             }
//         }).catch(err => {
//             if(sumEl) sumEl.innerHTML = "<b style='color:#FF2E63;'>Failed to analyze audience demands.</b>";
//         });

//         loader.classList.add("hidden");
//         main.classList.remove("hidden");

//     } catch (e) {
//         loader.classList.add("hidden");
//         error.innerText = e.message;
//         error.classList.remove("hidden");
//     } finally {
//         btn.disabled = false;
//     }
// });

// function renderCharts(stats, deep_data) {
//     const radarEl = document.getElementById("emotionRadarChart");
//     const sentEl = document.getElementById("sentimentChart");
//     const intentEl = document.getElementById("intentChart");

//     if (radarEl) {
//         const labels = ['joy', 'surprise', 'sadness', 'anger', 'fear', 'disgust'];
//         const data = labels.map(l => stats.emotion_counts[l]);
        
//         emotionRadarInstance = new Chart(radarEl.getContext("2d"), {
//             type: 'radar',
//             data: {
//                 labels: labels.map(l => l.toUpperCase()),
//                 datasets: [{
//                     label: 'Intensity',
//                     data: data,
//                     backgroundColor: 'rgba(138, 43, 226, 0.2)',
//                     borderColor: '#8A2BE2',
//                     borderWidth: 2,
//                     pointBackgroundColor: '#00E5FF'
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 scales: {
//                     r: {
//                         angleLines: { color: 'rgba(255,255,255,0.1)' },
//                         grid: { color: 'rgba(255,255,255,0.1)' },
//                         pointLabels: { color: '#ccc', font: {size: 10} },
//                         ticks: { display: false, callback: ()=>"" }
//                     }
//                 },
//                 plugins: { legend: { display: false } }
//             }
//         });
//     }

//     if (sentEl) {
//         sentimentChartInstance = new Chart(sentEl.getContext("2d"), {
//             type: 'doughnut',
//             data: {
//                 labels: ['Pos', 'Neu', 'Neg'],
//                 datasets: [{
//                     data: [stats.positive, stats.neutral, stats.negative],
//                     backgroundColor: ['#00FF9D', '#444', '#FF2E63'],
//                     borderColor: '#050505',
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false, cutout: '75%',
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10 } } }
//             }
//         });
//     }

//     if (intentEl && deep_data && deep_data.intents) {
//         intentChartInstance = new Chart(intentEl.getContext("2d"), {
//             type: 'pie',
//             data: {
//                 labels: ['Questions ❓', 'Appreciation 👏', 'Requests 🙏', 'Discussion 💬'],
//                 datasets: [{
//                     data: [
//                         deep_data.intents.question, 
//                         deep_data.intents.appreciation, 
//                         deep_data.intents.request, 
//                         deep_data.intents.discussion
//                     ],
//                     backgroundColor: ['#FFD700', '#00FF9D', '#FF2E63', '#8A2BE2'],
//                     borderColor: '#050505',
//                     borderWidth: 1
//                 }]
//             },
//             options: {
//                 responsive: true, maintainAspectRatio: false,
//                 plugins: { legend: { position: 'right', labels: { color: '#ccc', boxWidth: 10, font: {size: 9} } } }
//             }
//         });
//     }
// }



// 🚀 DEPLOYMENT URL SETUP
// Abhi local testing ke liye ye hai. Jab Render pe live karoge to isko change kar dena:
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

        // 🚀 Using API_BASE_URL here
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
        
        // 🚀 Using API_BASE_URL here
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