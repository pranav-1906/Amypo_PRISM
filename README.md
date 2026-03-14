# PRISM  
*Pixel-based Rendering and Interface Scoring Module*

PRISM is an automated **frontend assessment platform** that evaluates HTML, CSS, and JavaScript submissions using real browser rendering and AI-generated feedback.

The system renders student submissions in a headless browser, captures screenshots, analyzes visual and structural output, and generates intelligent feedback.

---

## 🚀 Features

- Automated **HTML/CSS/JS evaluation**
- **Headless browser rendering** using Puppeteer
- Screenshot-based visual comparison
- **AI-generated feedback** for submissions
- Modular architecture for easy integration
- Designed for coding assessments and educational platforms

---

## 🧠 How PRISM Works

1. A student uploads a frontend project (HTML, CSS, JS).
2. The system renders the project using **Puppeteer**.
3. A screenshot of the rendered page is captured.
4. The output is analyzed against expected UI behavior.
5. The **AI feedback module** generates evaluation comments.

---

## 🏗 Project Structure

```
PRISM
│
├── ai_module/           # AI feedback generation
│   └── ai_feedback.py
│
├── eval_engine/         # Puppeteer-based evaluation
│   └── evaluate.js
│
├── routes/              # Backend routes
├── static/              # Static assets
├── templates/           # HTML templates
│
├── app.py               # Main backend application
├── database.py          # Database management
├── requirements.txt     # Python dependencies
```

---

## ⚙️ Technologies Used

| Technology | Purpose |
|------------|--------|
| Python | Backend application |
| Puppeteer | Browser rendering & evaluation |
| Node.js | Evaluation engine |
| HTML/CSS/JS | Frontend submissions |
| AI API | Automated feedback generation |

---

## 🖥 Installation

### 1. Clone the repository

```
git clone https://github.com/pranav-1906/Amypo_PRISM.git
cd Amypo_PRISM
```

---

### 2. Install Python dependencies

```
pip install -r requirements.txt
```

---

### 3. Install Node dependencies

```
cd eval_engine
npm install
```

---

### 4. Configure environment variables

Create a `.env` file and add your API keys and configuration.

Example:

```
AI_API_KEY=your_api_key_here
```

---

### 5. Run the application

```
python app.py
```

---

## 📊 Use Cases

- Coding platform assessments
- Web development courses
- Hackathons and coding competitions
- Automated frontend evaluation systems

---

## 🔮 Future Improvements

- UI similarity scoring
- Code quality analysis
- Real-time feedback
- Multi-framework support (React, Vue, etc.)
- Performance scoring

---

## 🧑‍💻 Authors
- [@pranav-1906](https://github.com/pranav-1906)
- [@deva3019](https://github.com/deva3019)
- [@ram-1922](https://github.com/ram-1922)

---

## 📜 License

This project is intended for educational and research purposes.
