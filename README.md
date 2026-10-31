# LearnSense AI — Online Learning Engagement Analysis

**Project ID:** DA-015 &nbsp;|&nbsp; **Group ID:** BCA_AI_15 &nbsp;|&nbsp; **Domain:** EdTech Analytics
**Innovative solution:** LearnSense AI — Intelligent Learning Friction Detection and Recovery System
**Tagline:** *Understand Learning. Detect Friction. Support Progress.*

> All student and module data in this project is **simulated sample data — not real student records**.
> LearnSense AI is a **rule-based prototype**. It is **not** a trained machine-learning model.

---

## 1. Project overview
A web-based learning analytics application. It analyses course activity (attendance, assignment completion, revision sessions) and quiz scores, compares modules and learner groups, and uses transparent rules to detect possible *learning friction* and suggest supportive recovery steps.

## 2. Problem statement
Online courses produce a lot of activity data, but activity alone does not show understanding. Teachers need a simple, explainable way to notice when a learner may be struggling and to decide what support to offer — without labelling or punishing the learner.

## 3. Objectives
- Analyse attendance, assignment completion, revision activity and quiz performance.
- Separate **activity indicators** from **performance indicators**.
- Compare modules and learner groups (synthetic data).
- Detect possible learning friction using documented rules.
- Give personalised, **explainable** recovery suggestions.
- Propose a follow-up (post-intervention) assessment process.

## 4. Features
| Page | What it does |
|---|---|
| Home Dashboard | Summary cards, activity overview, performance comparison, auto-generated insights |
| Engagement Analysis | Activity vs performance indicators, indicator table, combined-score explanation, module and group comparison |
| Student Data | Searchable, filterable, sortable table of 5 simulated students with a detail panel |
| Data Visualisation | 6 Chart.js charts + 5 Matplotlib charts, each with a short explanation |
| LearnSense AI | Friction analysis demo, 5 scenarios, explainable recommendations, proposed reassessment tool |
| Responsible Data Use | Limits, privacy, bias, teacher oversight |
| About | Project details, contributions, objectives, methodology, limitations, editable team list |

**Combined learning-progress score (illustrative):**
`Attendance×0.25 + Quiz%×0.30 + Revision%×0.20 + Assignment×0.25`
Results: S01 88.25, S02 42.25, S03 65.75, S04 62.75, S05 70.50. This is *not* a validated measure.

**Experimental Friction Index (0–100):** sum of four weighted signals — completion time (30), unsuccessful attempts (30), hints (20), repeated attempts (20). Full rules are written at the top of `logic/friction_engine.py`.

## 5. Technology stack
HTML5 · CSS3 · Vanilla JavaScript · Python · Flask · Pandas · NumPy · Chart.js · Matplotlib · CSV · Git/GitHub

## 6. Folder structure
```
LearnSense-AI/
├── app.py                    # Flask app: pages + JSON routes
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── students.csv          # 5 simulated students
│   └── modules.csv           # synthetic module/group data (separate dataset)
├── analysis/
│   ├── data_analysis.py      # Pandas/NumPy calculations
│   └── visualisations.py     # Matplotlib charts -> static/images/charts
├── logic/
│   └── friction_engine.py    # LearnSense AI rule-based logic
├── templates/                # base, index, analytics, students, charts,
│                             # learnsense, responsible, about, error
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/charts/        # generated PNG charts
└── docs/screenshots/         # put your screenshots here
```

## 7. Installation and running locally (VS Code)
Open the `LearnSense-AI` folder in VS Code, then open **Terminal > New Terminal**.

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
If PowerShell blocks activation, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open **http://127.0.0.1:5000** in your browser. Stop the server with `Ctrl + C`.

The page needs internet for Chart.js and Google Fonts. Without internet the pages still work, and the Matplotlib charts still show.

## 8. Common errors
| Problem | Fix |
|---|---|
| `python` not recognised | Install Python from python.org and tick "Add Python to PATH", or try `py` instead of `python` |
| `ModuleNotFoundError: flask` | Activate the venv first, then `pip install -r requirements.txt` |
| `Address already in use` | Another program uses port 5000. Close it, or change the last line of `app.py` to `app.run(debug=True, port=5001)` |
| Charts are empty | Check internet (Chart.js loads from a CDN). Press F12 > Console to see the message |
| Page shows "Something went wrong" | The message names the CSV problem. Check `data/*.csv` column names |
| Changes not showing | Hard refresh with `Ctrl + Shift + R` |

## 9. Example screenshots
Add screenshots to `docs/screenshots/` after running the app, then link them here:

| File to create | Page |
|---|---|
| `docs/screenshots/home.png` | Home Dashboard |
| `docs/screenshots/charts.png` | Data Visualisation |
| `docs/screenshots/learnsense.png` | LearnSense AI result |

## 10. Limitations
- Only 5 simulated students and a synthetic module dataset.
- Combined-score and friction-index weights are experimental and not validated.
- Rule-based prototype; no trained model, no measured accuracy.
- Reassessment is a proposed feature and has not been tested with learners.
- No login, database or real-time data.

## 11. Future scope
Automated follow-up assessment · adaptive learning pathways · trained machine-learning models (with proper validation) · larger-scale engagement analysis · real-time dashboards · teacher feedback loop.

## 12. Upload to GitHub
```bash
git init
git add .
git commit -m "LearnSense AI - DA-015 first version"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/LearnSense-AI.git
git push -u origin main
```
Create an **empty** repository named `LearnSense-AI` on github.com first (no README), then use its URL above.

## 13. Deployment options
GitHub Pages only hosts static files, so it **cannot run the Flask/Python backend**. Options for the full app:

- **Render (suggested):** New > Web Service > connect the GitHub repo. Build command `pip install -r requirements.txt`, start command `gunicorn app:app`. Free tier is fine for a demo (it may sleep when idle).
- **PythonAnywhere:** free Flask hosting; upload the code and point the WSGI file to `app`.
- **Railway / Fly.io:** similar, with a free-trial or paid plan.

> This project has **not** been deployed yet. Add the live link here after you deploy it.

## 14. Responsible use
*Support, not labels. Support, not punishment.* See the Responsible Data Use page.
