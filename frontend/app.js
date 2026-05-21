// ==========================================
// Predefined Sample Email Templates
// ==========================================
const TEMPLATES = {
    "spam-phishing": `Subject: URGENT: Security notice regarding your banking account

Dear Customer,

We detected an unauthorized login attempt on your account from IP address 192.168.1.105. For your security, we have temporarily restricted your online access. 

Please click the link below to verify your identity, reset your passcode, and restore full access to your account:
http://secure-banking-alert-verification.com/reset-password

Failure to verify your identity within 24 hours will result in permanent suspension of your account.

Sincerely,
Security Department`,

    "spam-promo": `Subject: CONGRATULATIONS! You won a $1,000 Walmart Gift Card!

Valued Customer,

You have been selected as our grand prize winner for today! You are eligible to receive a free $1,000 Walmart Gift Card.

This is a limited-time promotional offer. To claim your reward, click the link below to verify your contact information and answer a short survey:
http://free-gift-cards-claim.net/walmart-promo

No purchase necessary. Must be 18 or older to claim. Act now before your reward expires!`,

    "ham-meeting": `Subject: Weekly Project Status Meeting - Tomorrow 10 AM

Hi Team,

Just a quick reminder that our weekly project status sync is scheduled for tomorrow morning at 10:00 AM in Conference Room B. 

Please ensure you have updated your team tasks in the shared tracking board before the meeting. We will go over:
1. Sprint progress updates
2. Blockers and risks
3. Q3 roadmap adjustments

If you cannot attend, please send your updates directly to me.

Best regards,
Sarah Jenkins
Project Lead`,

    "ham-personal": `Subject: Catching up for coffee this Friday?

Hey,

Hope you are having a productive week! 

Are you free to grab coffee sometime this Friday afternoon? I'd love to catch up, hear how your new role is going, and discuss some ideas for the upcoming community workshop.

There's a new place that just opened up on Main Street called The Brew House that looks really nice. Let me know if that works or if you have another preference.

Talk soon,
David`
};

// ==========================================
// State Management
// ==========================================
let currentModel = "Ensemble Model";
let metricsChart = null;

// ==========================================
// DOM Elements
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    // Theme Toggle
    const themeToggleBtn = document.getElementById("theme-toggle");
    
    // Navigation
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabPanels = document.querySelectorAll(".tab-panel");
    
    // Playground Elements
    const modelCards = document.querySelectorAll(".model-select-card");
    const emailInput = document.getElementById("email-input");
    const charCount = document.getElementById("char-count");
    const inputError = document.getElementById("input-error");
    const clearBtn = document.getElementById("clear-btn");
    const predictBtn = document.getElementById("predict-btn");
    const templateCards = document.querySelectorAll(".template-card");
    
    // Result Elements
    const resultEmpty = document.getElementById("result-empty");
    const resultLoading = document.getElementById("result-loading");
    const resultSuccess = document.getElementById("result-success");
    const verdictBanner = document.getElementById("verdict-banner");
    const verdictIconBox = document.getElementById("verdict-icon-box");
    const predictionLabel = document.getElementById("prediction-label");
    const targetClassNum = document.getElementById("target-class-num");
    const gaugeFill = document.getElementById("gauge-fill");
    const gaugeValue = document.getElementById("gauge-value");
    const modelConfidenceVal = document.getElementById("model-confidence-val");
    const modelUsedVal = document.getElementById("model-used-val");
    const logOrigChars = document.getElementById("log-orig-chars");
    const logProcessedText = document.getElementById("log-processed-text");

    // ==========================================
    // 1. Theme Management (Dark / Light)
    // ==========================================
    themeToggleBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", newTheme);
        
        // Update Icon
        const icon = themeToggleBtn.querySelector("i");
        if (newTheme === "light") {
            icon.className = "fa-solid fa-moon";
        } else {
            icon.className = "fa-solid fa-sun";
        }
        
        // Redraw chart if open to match new theme colors
        if (metricsChart) {
            drawMetricsChart();
        }
    });

    // ==========================================
    // 2. Tab Navigation
    // ==========================================
    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            // Remove active from tabs
            navTabs.forEach(t => t.classList.remove("active"));
            // Add active to clicked tab
            tab.classList.add("active");
            
            // Switch panels
            const targetTab = tab.getAttribute("data-tab");
            tabPanels.forEach(panel => {
                panel.classList.remove("active");
                if (panel.id === `${targetTab}-tab`) {
                    panel.classList.add("active");
                }
            });

            // Load metrics if switching to analytics
            if (targetTab === "analytics") {
                loadAnalyticsDashboard();
            }
        });
    });

    // ==========================================
    // 3. Model Selector Cards
    // ==========================================
    modelCards.forEach(card => {
        card.addEventListener("click", () => {
            modelCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            currentModel = card.getAttribute("data-model");
        });
    });

    // ==========================================
    // 4. Input Counter and Validation
    // ==========================================
    emailInput.addEventListener("input", () => {
        const len = emailInput.value.length;
        charCount.textContent = len.toLocaleString();
        
        if (len >= 3) {
            inputError.classList.add("hidden");
            emailInput.style.borderColor = "var(--border-color)";
        }
    });

    // ==========================================
    // 5. Template Injection
    // ==========================================
    templateCards.forEach(card => {
        card.addEventListener("click", () => {
            const templateType = card.getAttribute("data-type");
            const text = TEMPLATES[templateType];
            
            if (text) {
                emailInput.value = text;
                // Trigger input event to update counts
                emailInput.dispatchEvent(new Event("input"));
                emailInput.focus();
                
                // Optional: Scroll to text area on mobile
                emailInput.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
        });
    });

    // ==========================================
    // 6. Clear Button
    // ==========================================
    clearBtn.addEventListener("click", () => {
        emailInput.value = "";
        emailInput.dispatchEvent(new Event("input"));
        
        // Reset results state to empty
        resultEmpty.classList.remove("hidden");
        resultLoading.classList.add("hidden");
        resultSuccess.classList.add("hidden");
    });

    // ==========================================
    // 7. Predict API Request
    // ==========================================
    predictBtn.addEventListener("click", async () => {
        const textValue = emailInput.value.trim();
        
        // Validation
        if (textValue.length < 3) {
            inputError.classList.remove("hidden");
            emailInput.style.borderColor = "var(--color-danger)";
            emailInput.focus();
            return;
        }

        // Setup loading state
        predictBtn.disabled = true;
        predictBtn.querySelector(".btn-text").classList.add("hidden");
        predictBtn.querySelector(".btn-loader").classList.remove("hidden");
        
        resultEmpty.classList.add("hidden");
        resultSuccess.classList.add("hidden");
        resultLoading.classList.remove("hidden");

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: textValue,
                    model_name: currentModel
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Failed to fetch prediction");
            }

            const data = await response.json();
            
            // Call NLP preprocessor endpoint or mimic locally for logging. 
            // In our case, the backend returns prediction, but to display processed logs,
            // we can call a helper, or let the backend main.py return the preprocessed text as well.
            // Let's add processed text field to the API, or calculate it. 
            // Since we want to display NLP logs, let's fetch the processed text.
            // Wait, we can fetch the processed text or simply let the API return it.
            // Let's check: did main.py return processed text? No.
            // But wait, we can edit main.py to return it, or we can fetch/calculate it.
            // Let's update the API response schema to include `processed_text` so we can display it!
            // That's a great improvement!
            
            // Display Results
            updatePredictionUI(data, textValue.length);

        } catch (error) {
            console.error("Prediction Error:", error);
            // Display Error in Verdict Banner
            showErrorState(error.message);
        } finally {
            // Restore button state
            predictBtn.disabled = false;
            predictBtn.querySelector(".btn-text").classList.remove("hidden");
            predictBtn.querySelector(".btn-loader").classList.add("hidden");
            resultLoading.classList.add("hidden");
        }
    });

    // ==========================================
    // UI Update Functions
    // ==========================================
    function updatePredictionUI(data, originalCharCount) {
        resultLoading.classList.add("hidden");
        resultSuccess.classList.remove("hidden");

        // Banner Verdict
        const isSpam = data.prediction === "Spam";
        if (isSpam) {
            verdictBanner.className = "verdict-banner spam";
            verdictIconBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            predictionLabel.textContent = "SPAM DETECTED";
            targetClassNum.textContent = "1";
        } else {
            verdictBanner.className = "verdict-banner ham";
            verdictIconBox.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            predictionLabel.textContent = "NOT SPAM (HAM)";
            targetClassNum.textContent = "0";
        }

        // Mini metrics
        modelConfidenceVal.textContent = (data.confidence * 100).toFixed(1) + "%";
        modelUsedVal.textContent = data.model_used;

        // Animate Gauge
        // Total circumference for A (arc) is approx. 125.6
        // Dashoffset values go from 125.6 (0%) to 0 (100%)
        const percentage = Math.round(data.probability * 100);
        const offset = 125.6 * (1 - data.probability);
        gaugeFill.style.strokeDashoffset = offset;
        gaugeValue.textContent = percentage + "%";

        // Preprocessing logs
        logOrigChars.textContent = originalCharCount.toLocaleString();
        
        // Since we didn't add processed_text to main.py, let's update main.py next!
        // For now, write a fallback showing cleaned tokens.
        if (data.processed_text) {
            logProcessedText.textContent = data.processed_text;
        } else {
            // Mimic or wait for update
            logProcessedText.textContent = "Updating NLP token extraction logs...";
            fetchProcessedText(emailInput.value);
        }
    }

    async function fetchProcessedText(text) {
        // We will update main.py shortly to include processed_text, but we can do a quick local clean
        // or a lightweight API update. Let's make an update to main.py to return processed_text.
        // In the meantime, clean locally:
        const clean = text.toLowerCase()
            .replace(/https?:\/\/\S+|www\.\S+/g, "")
            .replace(/\S+@\S+/g, "")
            .replace(/<.*?>/g, "")
            .replace(/\d+/g, "")
            .replace(/[^\w\s]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
        logProcessedText.textContent = clean || "[Empty after processing]";
    }

    function showErrorState(message) {
        resultSuccess.classList.remove("hidden");
        verdictBanner.className = "verdict-banner spam";
        verdictIconBox.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
        predictionLabel.textContent = "ERROR OCCURRED";
        targetClassNum.textContent = "N/A";
        
        modelConfidenceVal.textContent = "0.0%";
        modelUsedVal.textContent = "None";
        gaugeFill.style.strokeDashoffset = "125.6";
        gaugeValue.textContent = "Error";
        
        logOrigChars.textContent = "N/A";
        logProcessedText.textContent = "Error Detail: " + message;
    }

    // ==========================================
    // 8. Analytics Dashboard Loading
    // ==========================================
    let metricsDataGlobal = null;
    
    async function loadAnalyticsDashboard() {
        if (metricsDataGlobal) {
            // Already loaded, just redraw the chart to fit theme if changed
            drawMetricsChart();
            return;
        }

        try {
            const response = await fetch("/api/metrics");
            if (!response.ok) throw new Error("Failed to load metrics");
            
            const metrics = await response.json();
            metricsDataGlobal = metrics;
            
            // Update Summary stats (if present in payload)
            if (metrics["Ensemble Model"]) {
                // Populate Confusion Matrix
                populateCM("nb", metrics["Naive Bayes"]["confusion_matrix"]);
                populateCM("lr", metrics["Logistic Regression"]["confusion_matrix"]);
                populateCM("ens", metrics["Ensemble Model"]["confusion_matrix"]);
                
                // Populate dynamic summary cards
                document.getElementById("best-model-name").textContent = "Ensemble Model";
                document.getElementById("best-model-acc").textContent = (metrics["Ensemble Model"].accuracy * 100).toFixed(2) + "% Accuracy";
                
                document.getElementById("precision-model-name").textContent = "Ensemble Model";
                document.getElementById("best-model-prec").textContent = (metrics["Ensemble Model"].precision * 100).toFixed(1) + "% Precision";
                
                document.getElementById("recall-model-name").textContent = "Ensemble Model";
                document.getElementById("best-model-rec").textContent = (metrics["Ensemble Model"].recall * 100).toFixed(2) + "% Recall";
            }
            
            // Draw Chart
            drawMetricsChart();
            
        } catch (error) {
            console.error("Metrics load error:", error);
        }
    }

    function populateCM(modelPrefix, matrix) {
        // Matrix is [[tn, fp], [fn, tp]]
        if (!matrix || matrix.length < 2) return;
        
        document.getElementById(`cm-${modelPrefix}-tn`).textContent = matrix[0][0];
        document.getElementById(`cm-${modelPrefix}-fp`).textContent = matrix[0][1];
        document.getElementById(`cm-${modelPrefix}-fn`).textContent = matrix[1][0];
        document.getElementById(`cm-${modelPrefix}-tp`).textContent = matrix[1][1];
    }

    function drawMetricsChart() {
        const ctx = document.getElementById("comparisonChart").getContext("2d");
        
        // Destroy old chart instance if exists
        if (metricsChart) {
            metricsChart.destroy();
        }

        if (!metricsDataGlobal || !metricsDataGlobal["Naive Bayes"] || !metricsDataGlobal["Ensemble Model"]) {
            return;
        }

        // Get colors based on theme
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        const gridColor = isDark ? "#202d4a" : "#cbd5e1";
        const textLabelColor = isDark ? "#94a3b8" : "#475569";
        const titleColor = isDark ? "#f8fafc" : "#0f172a";

        const nb = metricsDataGlobal["Naive Bayes"];
        const lr = metricsDataGlobal["Logistic Regression"];
        const ens = metricsDataGlobal["Ensemble Model"];

        const data = {
            labels: ["Accuracy", "Precision", "Recall", "F1-Score"],
            datasets: [
                {
                    label: "Naive Bayes",
                    data: [nb.accuracy, nb.precision, nb.recall, nb.f1_score].map(v => v * 100),
                    backgroundColor: "#3b82f6", // Blue
                    borderRadius: 6
                },
                {
                    label: "Logistic Regression",
                    data: [lr.accuracy, lr.precision, lr.recall, lr.f1_score].map(v => v * 100),
                    backgroundColor: "#10b981", // Green
                    borderRadius: 6
                },
                {
                    label: "Ensemble Model",
                    data: [ens.accuracy, ens.precision, ens.recall, ens.f1_score].map(v => v * 100),
                    backgroundColor: "#f59e0b", // Amber/Orange
                    borderRadius: 6
                }
            ]
        };

        metricsChart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: textLabelColor,
                            font: {
                                family: "Plus Jakarta Sans",
                                weight: "600"
                            }
                        }
                    },
                    y: {
                        min: 70,
                        max: 102,
                        grid: {
                            color: gridColor
                        },
                        ticks: {
                            color: textLabelColor,
                            font: {
                                family: "Plus Jakarta Sans"
                            },
                            callback: function(value) {
                                return value + "%";
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: {
                            color: titleColor,
                            font: {
                                family: "Plus Jakarta Sans",
                                weight: "600"
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ": " + context.parsed.y.toFixed(1) + "%";
                            }
                        }
                    }
                }
            }
        });
    }
});
