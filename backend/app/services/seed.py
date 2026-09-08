from datetime import datetime, timedelta, timezone

SAMPLE_JOBS = [
    {
        "title": "Senior Python Backend Engineer",
        "company": "CloudWorks",
        "description": "Build scalable microservices with Python and FastAPI. Experience with PostgreSQL, Redis and containerized deployments on AWS.",
        "location": "Remote",
        "salary": "$130k - $160k",
        "skills": ["python", "fastapi", "django", "postgresql", "redis", "aws", "docker", "kubernetes", "microservices", "rest api"],
        "experience_level": "senior",
        "url": "https://example.com/jobs/senior-python",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "DataMind Labs",
        "description": "Design and train ML models for NLP applications. Strong Python, PyTorch, and experience deploying models to production.",
        "location": "New York, NY",
        "salary": "$140k - $180k",
        "skills": ["python", "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas", "numpy", "aws", "docker"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/ml-engineer",
    },
    {
        "title": "Frontend Developer (React)",
        "company": "PixelForge",
        "description": "Create beautiful user interfaces with React, TypeScript and Tailwind. Work closely with designers on our SaaS product.",
        "location": "Austin, TX",
        "salary": "$110k - $140k",
        "skills": ["javascript", "typescript", "react", "html", "css", "tailwind", "git", "rest api"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/frontend-react",
    },
    {
        "title": "Data Scientist",
        "company": "Insightful Inc",
        "description": "Apply statistics and machine learning to large customer datasets. Build dashboards with Tableau and automate analysis in Python.",
        "location": "Seattle, WA",
        "salary": "$125k - $160k",
        "skills": ["python", "data science", "data analysis", "data visualization", "pandas", "numpy", "tableau", "sql", "machine learning"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/data-scientist",
    },
    {
        "title": "DevOps Engineer",
        "company": "PipelinePro",
        "description": "Own CI/CD pipelines, infrastructure as code with Terraform, and Kubernetes clusters on Azure and AWS.",
        "location": "Remote",
        "salary": "$120k - $150k",
        "skills": ["aws", "azure", "terraform", "kubernetes", "docker", "jenkins", "ci/cd", "linux", "bash", "git"],
        "experience_level": "senior",
        "url": "https://example.com/jobs/devops",
    },
    {
        "title": "Junior Full Stack Developer",
        "company": "Startify",
        "description": "Join our startup team to build web apps end-to-end with React, Node.js, and MongoDB. Great learning environment.",
        "location": "Remote",
        "salary": "$70k - $95k",
        "skills": ["javascript", "typescript", "react", "node.js", "express", "mongodb", "html", "css", "git"],
        "experience_level": "entry",
        "url": "https://example.com/jobs/junior-fullstack",
    },
    {
        "title": "Product Manager - AI Platform",
        "company": "NovaMinds",
        "description": "Lead roadmap for an enterprise AI platform. Experience with LLMs, product analytics, and agile delivery.",
        "location": "San Francisco, CA",
        "salary": "$150k - $190k",
        "skills": ["product management", "agile", "scrum", "llm", "generative ai", "data analysis", "leadership", "jira"],
        "experience_level": "manager",
        "url": "https://example.com/jobs/product-manager-ai",
    },
    {
        "title": "Backend Developer (Node.js)",
        "company": "NodeSea",
        "description": "Develop scalable REST and GraphQL APIs with Node.js, Express, and PostgreSQL. Hands-on AWS experience expected.",
        "location": "Chicago, IL",
        "salary": "$105k - $135k",
        "skills": ["javascript", "typescript", "node.js", "express", "graphql", "rest api", "postgresql", "aws", "docker"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/node-backend",
    },
    {
        "title": "Data Engineer",
        "company": "Streamline Data",
        "description": "Build robust ETL pipelines with Python, Spark, and Airflow. Manage data lakes on AWS and GCP.",
        "location": "Denver, CO",
        "salary": "$115k - $145k",
        "skills": ["python", "data engineering", "etl", "spark", "hadoop", "kafka", "airflow", "aws", "gcp", "sql"],
        "experience_level": "senior",
        "url": "https://example.com/jobs/data-engineer",
    },
    {
        "title": "Security Engineer",
        "company": "ShieldNet",
        "description": "Protect cloud infrastructure, perform penetration testing, and embed security into our CI/CD pipeline.",
        "location": "Remote",
        "salary": "$130k - $170k",
        "skills": ["security", "cybersecurity", "penetration testing", "aws", "azure", "linux", "networking", "ci/cd", "iam"],
        "experience_level": "senior",
        "url": "https://example.com/jobs/security-engineer",
    },
    {
        "title": "Mobile Developer (Flutter)",
        "company": "AppCraft",
        "description": "Build cross-platform mobile applications with Flutter and Dart, integrating REST APIs and backend services.",
        "location": "Toronto, Canada",
        "salary": "$90k - $130k",
        "skills": ["dart", "flutter", "javascript", "rest api", "git", "firebase", "mobile"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/flutter-dev",
    },
    {
        "title": "UX/UI Designer",
        "company": "DesignHub",
        "description": "Design intuitive product experiences with Figma. Conduct user research and build design systems for web products.",
        "location": "Remote",
        "salary": "$85k - $115k",
        "skills": ["ui/ux", "figma", "prototyping", "user research", "html", "css", "communication"],
        "experience_level": "mid-level",
        "url": "https://example.com/jobs/ux-designer",
    },
]


def seed_jobs(force: bool = False) -> int:
    from ..database import get_db
    jobs = get_db().jobs
    if jobs.count_documents({}) > 0 and not force:
        return 0
    if force:
        jobs.delete_many({})
    now = datetime.now(timezone.utc)
    base = [dict(job) for job in SAMPLE_JOBS]
    for idx, job in enumerate(base):
        job["posted_at"] = now - timedelta(days=idx % 14)
        job["skills"] = list(dict.fromkeys(s.lower() for s in job["skills"]))
    jobs.insert_many(base)
    return len(base)