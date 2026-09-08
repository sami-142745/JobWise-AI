import re

SKILLS_TAXONOMY = [
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r",
    "react", "react native", "angular", "vue", "svelte", "node.js", "nodejs",
    "django", "flask", "fastapi", "express", "spring boot", "rails", "laravel",
    "html", "css", "sass", "tailwind", "bootstrap",
    "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle", "sql server",
    "mongodb", "redis", "dynamodb", "cassandra", "elasticsearch",
    "aws", "azure", "gcp", "google cloud", "terraform", "kubernetes", "docker",
    "jenkins", "ci/cd", "git", "github", "gitlab", "pipeline",
    "machine learning", "deep learning", "nlp", "neural networks", "tensorflow",
    "pytorch", "keras", "scikit-learn", "pandas", "numpy", "data science",
    "data analysis", "data engineering", "data visualization", "etl", "spark",
    "hadoop", "kafka", "airflow", "tableau", "power bi", "looker",
    "computer vision", "llm", "openai", "langchain", "generative ai", "rag",
    "fastapi", "graphql", "rest api", "restful", "microservices", "grpc",
    "linux", "unix", "bash", "shell scripting", "powershell", "networking",
    "security", "cybersecurity", "penetration testing", "iam", "encryption",
    "blockchain", "solidity", "web3",
    "agile", "scrum", "kanban", "jira", "product management", "product owner",
    "ui/ux", "figma", "sketch", "prototyping", "user research",
    "testing", "pytest", "jest", "selenium", "cypress", "mocha", "unit testing",
    "project management", "leadership", "communication", "teamwork",
    "sap", "salesforce", "oracle erp", "workday",
    "excel", "word", "powerpoint", "google sheets", "notion", "confluence",
    "customer success", "sales", "marketing", "seo", "content writing",
    "fintech", "healthcare", "e-commerce", "saas",
    "c", "objective-c", "haskell", "elixir", "clojure", "dart", "flutter",
]

EXPERIENCE_PATTERNS = [
    (r"(\d{2})\s*(?:plus)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|work)", "explicit"),
    (r"(\d)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|work)", "explicit"),
    (r"20\d{2}\s*(?:–|-|to)\s*(?:present|current|now)\s*", "range"),
    (r"(19|20)\d{2}\s*(?:–|-|to)\s*(?:19|20)\d{2}", "range"),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").lower().strip()


def extract_skills(text: str) -> list[str]:
    """Extract skills from a resume/job text using a taxonomy of known skills.

    Skills are matched as whole words (not substrings) so that short skills
    such as "c" or "r" are not falsely detected inside longer words.
    """
    if not text:
        return []
    normalized = normalize(text)
    found: list[str] = []
    for skill in SKILLS_TAXONOMY:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, normalized):
            found.append(skill)
    return sorted(set(found))


def extract_years_experience(text: str) -> float:
    """Estimate years of professional experience from a resume."""
    if not text:
        return 0.0
    days = 0.0
    for pattern, kind in EXPERIENCE_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for m in matches:
            if kind == "explicit":
                try:
                    days += float(m) * 365
                except ValueError:
                    continue
            elif kind == "range":
                matches_range = re.findall(pattern, text, flags=re.IGNORECASE)
                continue
    # Date ranges (jobs): sum them up conservatively
    for m in re.finditer(r"(19|20)\d{2}\s*(?:–|-|to)\s*(?:19|20)\d{2}", text):
        start, end = m.group(0).replace("–", "-").split("-")
        try:
            days += max(0, (int(end) - int(start))) * 365
        except ValueError:
            continue
    return round(days / 365, 1)


def summarize(text: str, limit: int = 300) -> str:
    if not text:
        return ""
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:limit] + ("…" if len(clean) > limit else "")