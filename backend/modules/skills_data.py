"""
Curated skills database for the AI Resume Analyzer.

Contains ~250+ skills organized by category. Used by the NLP engine
to identify skills mentioned in resumes via case-insensitive matching.

WHY a curated list instead of ML-only?
- Resume skills are domain-specific; general NER models don't recognize them.
- A curated list gives high precision (no false positives like "Java" the island).
- Easy to extend: just add new skills to the relevant category.
"""

# ── Technical Skills by Category ──────────────────────────────────────

PROGRAMMING_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "perl", "lua", "dart", "objective-c", "shell",
    "bash", "powershell", "sql", "nosql", "graphql", "html", "css",
    "sass", "less", "assembly", "vba", "groovy", "elixir", "clojure",
    "haskell", "erlang", "fortran", "cobol", "julia",
}

FRAMEWORKS_AND_LIBRARIES = {
    "react", "react.js", "reactjs", "angular", "angularjs", "vue",
    "vue.js", "vuejs", "next.js", "nextjs", "nuxt.js", "nuxtjs",
    "svelte", "django", "flask", "fastapi", "spring", "spring boot",
    "express", "express.js", "node.js", "nodejs", "nest.js", "nestjs",
    ".net", "asp.net", "asp.net core", "ruby on rails", "rails",
    "laravel", "symfony", "gin", "echo", "fiber", "actix",
    "jquery", "bootstrap", "tailwind", "tailwindcss", "material ui",
    "chakra ui", "ant design", "redux", "mobx", "zustand",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "opencv", "spacy", "nltk", "hugging face", "transformers",
    "langchain", "llamaindex", "streamlit", "gradio",
    "selenium", "playwright", "cypress", "jest", "mocha",
    "pytest", "unittest", "junit", "testng",
    "flutter", "react native", "xamarin", "ionic", "electron",
    "three.js", "d3.js", "chart.js",
}

DATABASES = {
    "postgresql", "postgres", "mysql", "mariadb", "sqlite", "oracle",
    "sql server", "mssql", "mongodb", "dynamodb", "cassandra",
    "couchdb", "firebase", "firestore", "supabase", "redis",
    "memcached", "elasticsearch", "opensearch", "neo4j", "arangodb",
    "influxdb", "timescaledb", "cockroachdb", "planetscale",
}

CLOUD_AND_DEVOPS = {
    "aws", "amazon web services", "azure", "microsoft azure",
    "gcp", "google cloud", "google cloud platform",
    "docker", "kubernetes", "k8s", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci",
    "travis ci", "bitbucket pipelines", "argo cd", "helm",
    "prometheus", "grafana", "datadog", "new relic", "splunk",
    "cloudformation", "pulumi", "vagrant", "nginx", "apache",
    "caddy", "load balancer", "cdn", "cloudflare", "vercel",
    "netlify", "heroku", "render", "railway", "fly.io",
    "ec2", "s3", "lambda", "ecs", "eks", "fargate",
    "rds", "aurora", "sqs", "sns", "kinesis", "step functions",
    "api gateway", "cloudwatch", "iam",
    "linux", "unix", "windows server", "ubuntu", "centos", "debian",
}

DATA_SCIENCE_AND_AI = {
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "nlp", "computer vision",
    "reinforcement learning", "neural networks", "cnn", "rnn",
    "lstm", "transformer", "bert", "gpt", "generative ai",
    "large language models", "llm", "rag",
    "data analysis", "data engineering", "data pipeline",
    "etl", "data warehouse", "data lake", "data modeling",
    "feature engineering", "model deployment", "mlops",
    "a/b testing", "statistical analysis", "regression",
    "classification", "clustering", "dimensionality reduction",
    "time series", "recommendation systems",
    "tableau", "power bi", "looker", "apache spark", "hadoop",
    "airflow", "dbt", "kafka", "flink", "beam",
    "jupyter", "colab", "sagemaker", "vertex ai", "azure ml",
    "bigquery", "redshift", "snowflake", "databricks",
}

TOOLS_AND_PLATFORMS = {
    "git", "github", "gitlab", "bitbucket", "svn",
    "jira", "confluence", "trello", "asana", "notion",
    "slack", "teams", "zoom",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "postman", "swagger", "insomnia",
    "vs code", "visual studio", "intellij", "pycharm", "webstorm",
    "vim", "emacs", "sublime text",
    "webpack", "vite", "rollup", "parcel", "esbuild",
    "npm", "yarn", "pnpm", "pip", "conda", "poetry",
    "rest api", "restful", "grpc", "websocket", "graphql",
    "oauth", "jwt", "saml", "openid connect",
    "agile", "scrum", "kanban", "waterfall",
    "ci/cd", "devops", "sre", "infrastructure as code",
    "microservices", "monolith", "serverless", "event-driven",
    "design patterns", "solid", "clean architecture",
    "tdd", "bdd", "unit testing", "integration testing",
    "api testing", "load testing", "performance testing",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "collaboration",
    "problem solving", "problem-solving", "critical thinking",
    "project management", "time management", "mentoring",
    "presentation", "public speaking", "negotiation",
    "strategic planning", "decision making", "adaptability",
    "creativity", "innovation", "analytical thinking",
    "conflict resolution", "stakeholder management",
    "cross-functional", "remote work", "team building",
}

# ── Aggregate all skills into a single set ────────────────────────────
ALL_SKILLS = (
    PROGRAMMING_LANGUAGES
    | FRAMEWORKS_AND_LIBRARIES
    | DATABASES
    | CLOUD_AND_DEVOPS
    | DATA_SCIENCE_AND_AI
    | TOOLS_AND_PLATFORMS
    | SOFT_SKILLS
)

# ── Category mapping (used for skill gap analysis) ────────────────────
SKILL_CATEGORIES = {
    "Programming Languages": PROGRAMMING_LANGUAGES,
    "Frameworks & Libraries": FRAMEWORKS_AND_LIBRARIES,
    "Databases": DATABASES,
    "Cloud & DevOps": CLOUD_AND_DEVOPS,
    "Data Science & AI": DATA_SCIENCE_AND_AI,
    "Tools & Platforms": TOOLS_AND_PLATFORMS,
    "Soft Skills": SOFT_SKILLS,
}


def get_skill_category(skill: str) -> str:
    """Return the category name for a given skill, or 'Other' if not found."""
    skill_lower = skill.lower()
    for category, skills_set in SKILL_CATEGORIES.items():
        if skill_lower in skills_set:
            return category
    return "Other"


# ── Common action verbs (used by feedback generator) ──────────────────
ACTION_VERBS = {
    "achieved", "administered", "analyzed", "architected", "automated",
    "built", "collaborated", "conducted", "consolidated", "coordinated",
    "created", "decreased", "delivered", "designed", "developed",
    "directed", "drove", "eliminated", "engineered", "established",
    "exceeded", "executed", "expanded", "facilitated", "formulated",
    "generated", "grew", "identified", "implemented", "improved",
    "increased", "initiated", "innovated", "integrated", "introduced",
    "launched", "led", "leveraged", "managed", "mentored",
    "migrated", "modernized", "negotiated", "optimized", "orchestrated",
    "overhauled", "pioneered", "planned", "produced", "programmed",
    "proposed", "published", "reduced", "refactored", "redesigned",
    "resolved", "restructured", "revamped", "scaled", "secured",
    "simplified", "spearheaded", "standardized", "streamlined",
    "strengthened", "supervised", "surpassed", "tested", "trained",
    "transformed", "upgraded",
}

# ── Education keywords ────────────────────────────────────────────────
DEGREE_KEYWORDS = {
    "bachelor", "bachelors", "bachelor's", "b.s.", "b.s", "bs",
    "b.a.", "b.a", "ba", "b.tech", "btech", "b.e.", "b.e", "be",
    "b.sc", "bsc", "b.com", "bcom",
    "master", "masters", "master's", "m.s.", "m.s", "ms",
    "m.a.", "m.a", "ma", "m.tech", "mtech", "m.e.", "m.e",
    "m.sc", "msc", "mba", "m.b.a",
    "ph.d", "phd", "ph.d.", "doctorate", "doctoral",
    "associate", "associates", "associate's",
    "diploma", "certificate", "certification",
}

EDUCATION_INSTITUTIONS_KEYWORDS = {
    "university", "college", "institute", "school", "academy",
    "polytechnic", "iit", "nit", "iiit", "bits",
}
