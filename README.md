# PRISM  
### Pixel-based Rendering and Interface Scoring Module

PRISM is an automated **frontend assessment engine** that evaluates HTML, CSS, and JavaScript submissions using real browser rendering, visual comparison, and AI-generated feedback.

The platform executes student code inside a **sandboxed Chromium environment using Puppeteer**, analyzes the DOM structure, CSS styling, and JavaScript behavior, compares visual output with a reference design, and generates **rubric-based scoring and intelligent feedback**.

PRISM was developed as a solution to automate frontend evaluation where traditional coding platforms struggle to assess **visual UI correctness and interactive behavior**.

---

# 🏆 Hackathon Project

This project was built during a **24-hour national level hackathon**.

The system demonstrates how frontend assignments can be evaluated automatically using browser automation and visual diff techniques.

---

# 🚀 Core Features

### Automated Frontend Evaluation
PRISM evaluates **HTML, CSS, and JavaScript submissions** automatically.

### Headless Browser Execution
Student code runs inside a **sandboxed Chromium environment using Puppeteer**.

### DOM Structure Tests
Checks if required HTML elements exist using selectors.

### CSS Computed Style Validation
Validates layout and styling using computed CSS properties.

### JavaScript Behavior Tests
Simulates interactions like:

- Click
- Typing
- DOM updates
- Event handling

### Visual UI Comparison
Screenshots are captured and compared against the **reference UI using Pixelmatch**.

### Diff Heatmap Generation
The system generates visual difference maps showing mismatched UI regions.

Outputs include:

- Expected screenshot
- Student screenshot
- Diff heatmap

### Rubric-Based Partial Scoring
Marks are distributed across categories:

- HTML Structure
- CSS Styling
- JavaScript Behavior
- Visual Accuracy

### AI-Powered Feedback
PRISM integrates **Google Gemini API** to generate feedback explaining:

- layout issues
- styling differences
- missing UI elements
- improvement suggestions

### External Library Support
Assignments can allow controlled frontend libraries such as:

- Bootstrap
- Tailwind
- jQuery

Libraries are restricted using **whitelist-based network interception**.

---

# 🧠 How PRISM Works

### 1️⃣ Trainer Creates Assignment
Trainer uploads:

- Question description
- Starter files
- Reference solution
- Evaluation rubric

---

### 2️⃣ Baseline Generation
The system renders the **reference solution using Puppeteer** and captures baseline screenshots.

These screenshots become the **visual reference for evaluation**.

---

### 3️⃣ Student Submission
Students write HTML/CSS/JS code inside the platform and submit their solution.

---

### 4️⃣ Automated Evaluation Pipeline
```
Student Submission
        ↓
Flask Backend Receives Code
        ↓
Node.js Evaluation Engine Triggered
        ↓
Puppeteer Runs Submission in Headless Chromium
        ↓
DOM + CSS + JS Tests Executed
        ↓
Screenshot Captured
        ↓
Pixelmatch Visual Comparison
        ↓
Rubric-Based Score Generated
        ↓
AI Feedback Generated (Gemini)
        ↓
Results + Visual Diff Map Returned to Student
```

---

### 5️⃣ Result Generation

The student receives:

- Final Score
- Section-wise marks
- Failed tests list
- Visual diff heatmap
- AI-generated feedback

---

# 🏗 Project Architecture
```
PRISM
│
├── ai_module/ # AI feedback generation
│ └── ai_feedback.py
│
├── eval_engine/ # Puppeteer evaluation engine
│ ├── evaluate.js
│ └── visual_diff.js
│
├── routes/ # Flask backend routes
│
├── static/ # Static assets
│
├── templates/ # HTML templates
│
├── app.py # Main Flask application
├── database.py # MongoDB integration
│
├── requirements.txt # Python dependencies
```

---

# ⚙️ Technologies Used

| Technology | Purpose |
|------------|--------|
| Python (Flask) | Backend API |
| Node.js | Evaluation engine |
| Puppeteer | Browser automation |
| Pixelmatch | Visual UI comparison |
| MongoDB | Data storage |
| Tailwind CSS | Frontend styling |
| Google Gemini API | AI feedback generation |

---

# 📊 Evaluation Method

PRISM evaluates submissions using **multiple testing layers**.

### DOM Tests
Verify HTML structure using selectors.

Example:
`#submitBtn should exist`

---

### CSS Tests
Check computed styles.

Example:
`.container display should be flex`

---

### JavaScript Interaction Tests
Simulate actions.

Example:
`Type input → Click Add → Task appears`

---

### Visual Comparison
Screenshots are compared with reference UI.

Scoring example:

| Visual Difference | Score |
|-------------------|------|
| ≤1% | Full marks |
| 1–3% | 80% |
| 3–6% | 50% |
| >6% | 0 |

---

# 🖥 Installation

## 1️⃣ Clone Repository
```
git clone https://github.com/pranav-1906/Amypo_PRISM.git
cd Amypo_PRISM
```

---

## 2️⃣ Install Python Dependencies
`pip install -r requirements.txt`

---

## 3️⃣ Install Node Dependencies
```
cd eval_engine
npm install
```

---

## 4️⃣ Setup Environment Variables

Create a `.env` file.

Example:
`GEMINI_API_KEY=your_api_key_here`

---

## 5️⃣ Run the Application
`python app.py`

---

# 📌 Use Cases

PRISM can be used for:

- Coding assessment platforms
- Web development courses
- Frontend bootcamps
- Hackathons
- Technical interviews

---

# 🔮 Future Improvements

- Multi viewport testing (mobile + tablet)
- Region-based visual scoring
- React/Vue support
- Performance scoring
- Accessibility testing
- Code quality analysis

---

# 🧑‍💻 Authors

- [Pranav](https://github.com/pranav-1906)
- [Deva Veera Kumaran](https://github.com/deva3019)
- [Sri Ram](https://github.com/ram-1922)

---

# 📜 License

This project is developed for **educational and research purposes**.
