# College T&P Resume Parsing & Placement System

An automated, robust Resume Parsing System built for a college Training and Placement (T&P) department.

---

## 🌟 Key Architecture & Strict AI Separation

1. **Strictly Deterministic Python Extraction (No AI Used)**:
   - **Profile**: Full Name, Email, Phone, Location, LinkedIn, GitHub, Portfolio URLs, and Career Objective / Summary parsed via regex, position heuristics, and keyword rules. Missing scalar values default strictly to `null`.
   - **Education**: Detects multiple qualifications, institution names, degrees (B.Tech, MCA, etc.), specialization, years, and preserves **CGPA and percentage as separate fields without invalid conversion**.
   - **Technical Skills**: Organizes explicitly listed skills into `programming_languages`, `frameworks`, `databases`, `tools`, and `other_skills` via category detection and dictionaries.
   - **Certifications**: Parses credential names, issuers (AWS, Google, Coursera, etc.), dates, IDs, and URLs.
   - **Achievements**: Captures titles, descriptions, organizations, and dates.

2. **AI Extraction Exclusively for Projects and Experience**:
   - **Projects**: Extracts project title, role (or `null`), description, and technical skills.
   - **Experience**: Extracts company, role, experience type (`internship`, `full_time`, `part_time`, `other`, `unknown`), dates, description, and technical skills.
   - **AI Safety & Isolation**: Only the isolated text of Projects and Experience is sent to the OpenAI API using structured JSON output. If both sections are absent or empty, the OpenAI API is **not called**. Untrusted resume text is isolated from instructions to prevent prompt injections.

3. **Single Canonical JSON Object**:
   - All deterministic and AI results are merged into one canonical schema validated with **Pydantic v2**.

4. **MongoDB Document Persistence**:
   - Every parsed resume is stored as **one MongoDB document** in the `resumes` collection with document ID, file hash (SHA-256 for deduplication), and parsing metadata.

---

## 📂 Project Structure

```text
epam resume/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── resumes.py            # POST /api/resumes/parse & GET /api/resumes/{id}
│   │   ├── core/
│   │   │   └── config.py                 # Pydantic BaseSettings & environment configs
│   │   ├── schemas/
│   │   │   └── resume_schema.py          # Canonical Pydantic schemas & response models
│   │   ├── services/
│   │   │   ├── text_extractor.py         # PyMuPDF & python-docx extractor with magic byte checks
│   │   │   ├── section_detector.py       # Regex and keyword section partitioning
│   │   │   ├── deterministic_parser.py   # Python-only rule extraction (5 sections)
│   │   │   ├── ai_extractor.py           # OpenAI extractor (Projects & Experience only)
│   │   │   └── resume_service.py         # Pipeline orchestrator
│   │   ├── repositories/
│   │   │   └── resume_repository.py      # PyMongo persistence & deduplication
│   │   └── main.py                       # FastAPI application & CORS
│   ├── tests/
│   │   └── test_resume_parser.py         # Pytest unit & integration test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx                # Header with T&P badge
│   │   │   ├── FileUpload.jsx            # Drag-and-drop file upload with validation
│   │   │   ├── ProfileSection.jsx        # Contact info & summary
│   │   │   ├── EducationSection.jsx      # Multiple qualifications & scores
│   │   │   ├── SkillsSection.jsx         # Categorized skills badges
│   │   │   ├── ProjectsSection.jsx       # AI-extracted projects
│   │   │   ├── ExperienceSection.jsx     # AI-extracted work/internships
│   │   │   ├── CertificationsSection.jsx # Deterministic certifications
│   │   │   ├── AchievementsSection.jsx   # Deterministic achievements
│   │   │   ├── RawJsonModal.jsx          # JSON schema inspector & copy
│   │   │   ├── StatusAlert.jsx           # Success/Warning/Error alerts
│   │   │   └── ParsedResultView.jsx      # Comprehensive results container
│   │   ├── services/
│   │   │   └── api.js                    # Fetch client for FastAPI backend
│   │   ├── App.jsx                       # Main application state
│   │   ├── main.jsx                      # React 18 DOM mount
│   │   └── index.css                     # Modern dark theme & design system
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── .env.example
└── README.md
```

---

## 🚀 Setup and Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- MongoDB running locally or a MongoDB Atlas URI

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
```

Configure your `.env` file:
```env
OPENAI_API_KEY=your_actual_openai_api_key
OPENAI_MODEL=gpt-4o-mini
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=resume_parser_db
MAX_UPLOAD_SIZE_MB=10
```

Start the FastAPI backend server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API docs will be available at: `http://localhost:8000/docs`

### 3. Frontend Setup

In a new terminal window:
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 🧪 Running Automated Tests

To execute the unit and integration tests (covering PDF/DOCX extraction, deterministic parsing, AI isolation, schema validation, and duplicate handling):

```bash
cd backend
pytest tests/ -v
```

---

## 📡 API Endpoints

### 1. `POST /api/resumes/parse`
- **Request**: `multipart/form-data` with `file` (PDF or DOCX).
- **Validation**: File extension, file signature (`%PDF` / `PK\x03\x04`), max file size (10 MB).
- **Response**:
```json
{
  "document_id": "664fa1e2b58872f23b2075ad",
  "status": "completed",
  "message": "Resume successfully parsed and processed.",
  "duplicate": false,
  "data": {
    "profile": { ... },
    "education": [ ... ],
    "technical_skills": { ... },
    "projects": [ ... ],
    "experience": [ ... ],
    "certifications": [ ... ],
    "achievements": [ ... ],
    "metadata": {
      "parser_version": "1.0",
      "status": "completed",
      "parsed_at": "2026-10-22T17:40:00Z",
      "file_name": "resume.pdf",
      "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "file_size_bytes": 1048576,
      "ai_called_for_projects_or_experience": true,
      "is_scanned_pdf": false
    }
  }
}
```

### 2. `GET /api/resumes/{document_id}`
- Returns the complete stored MongoDB document for a previously parsed resume.
