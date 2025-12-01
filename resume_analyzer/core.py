# resume_analyzer/core.py
import re
from typing import List
import PyPDF2

# Try to import spaCy and load model. We'll lazy-load in module import.
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None  # We'll raise friendly error if not loaded when used.

# Comprehensive skill keywords list for software-related jobs
_SKILL_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "nosql", "html", "css",
    "react", "angular", "vue", "node.js", "node", "django", "flask", "spring", "hibernate",
    "rest", "api", "graphql", "jpa", "oop", "agile", "scrum", "kanban",
    "oracle", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
    "google cloud", "gcp", "ci/cd", "jenkins", "git", "github", "gitlab", "bitbucket",
    "unit testing", "integration testing", "selenium", "appium", "jira", "trello", "slack",
    "machine learning", "deep learning", "data analysis", "data science", "artificial intelligence",
    "nlp", "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "tableau", "power bi",
    "design patterns", "mvc", "microservices", "soap", "json", "xml", "web development",
    "backend development", "frontend development", "full stack development",
    "software architecture", "software design", "problem-solving", "team collaboration",
    "communication", "data structures and algorithm", "object oriented programming"
]

# Normalize keywords to lowercase and unique
_SKILL_KEYWORDS = list(dict.fromkeys(k.lower() for k in _SKILL_KEYWORDS))


def _ensure_nlp_available():
    global _nlp
    if _nlp is None:
        raise RuntimeError(
            "spaCy model not loaded. Install spaCy and the English model:\n"
            "pip install spacy && python -m spacy download en_core_web_sm"
        )


def extract_text_from_pdf(file_obj) -> str:
    """
    Read uploaded PDF file (Django InMemoryUploadedFile or file-like) and return extracted text.
    """
    try:
        reader = PyPDF2.PdfReader(file_obj)
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)
    except Exception as e:
        # Re-raise with informative message
        raise RuntimeError(f"Failed to read PDF file: {e}")


def extract_skills(text: str) -> List[str]:
    """
    Extract skills from the given text using keyword matching.
    This is simple and robust across different frameworks.
    """
    if not text:
        return []

    text_lower = text.lower()

    # Simple keyword presence detection
    found = set()
    for kw in _SKILL_KEYWORDS:
        # use word boundary for short tokens; for multi-word keywords just check substring
        if " " in kw:
            if kw in text_lower:
                found.add(kw)
        else:
            # word boundary match
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                found.add(kw)

    # Optionally, extend with spaCy named-entity / token scanning for recognized tokens if available
    # but keep it optional to avoid hard dependency
    try:
        if _nlp:
            doc = _nlp(text)
            for token in doc:
                t = token.text.lower()
                if t in _SKILL_KEYWORDS:
                    found.add(t)
    except Exception:
        pass

    # Return sorted list for deterministic output (and title-case for display)
    return sorted({s.title() for s in found})


def compare_skills(resume_skills: List[str], job_skills: List[str]) -> List[str]:
    """Return list of skills present in job_skills but missing in resume_skills."""
    resume_set = {s.lower() for s in resume_skills}
    missing = [s for s in job_skills if s.lower() not in resume_set]
    return missing


def calculate_ats_percentage(resume_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills:
        return 0.0
    matched = set(s.lower() for s in resume_skills) & set(s.lower() for s in job_skills)
    return (len(matched) / len(job_skills)) * 100.0


def analyze_resume_file_and_job(pdf_file_obj, job_description: str):
    """
    High-level function to be used by views. Returns a dict with keys:
    resumeSkills, jobSkills, missingSkills, atsPercentage
    """
    # Extract text from PDF
    resume_text = extract_text_from_pdf(pdf_file_obj)

    # Extract skills
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)

    missing = compare_skills(resume_skills, job_skills)
    ats = calculate_ats_percentage(resume_skills, job_skills)

    return {
        "resumeSkills": resume_skills,
        "jobSkills": job_skills,
        "missingSkills": missing,
        "atsPercentage": ats,
    }
