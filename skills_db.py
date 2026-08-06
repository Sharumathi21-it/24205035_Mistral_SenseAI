SKILLS_DB = {
    "programming_languages": [
        "python", "java", "c++", "c#", "c", "javascript", "typescript",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "dart", "objective c", "sql", "shell scripting",
        "bash", "powershell",
    ],
    "web_technologies": [
        "html", "css", "react", "react.js", "angular", "vue", "vue.js",
        "node.js", "nodejs", "express.js", "django", "flask", "fastapi",
        "spring", "spring boot", "asp.net", "next.js", "redux", "graphql",
        "rest api", "restful api", "bootstrap", "tailwind css", "jquery",
        "webpack",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "sqlite", "oracle",
        "sql server", "redis", "cassandra", "dynamodb", "firebase",
        "elasticsearch", "mariadb", "nosql",
    ],
    "cloud_devops": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible",
        "git", "github", "gitlab", "bitbucket", "linux", "nginx", "apache",
        "microservices", "devops",
    ],
    "data_ml": [
        "machine learning", "deep learning", "data science", "data analysis",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "nlp", "natural language processing", "computer vision",
        "data visualization", "tableau", "power bi", "excel", "statistics",
        "big data", "hadoop", "spark", "etl",
    ],
    "mobile": [
        "android", "ios", "flutter", "react native", "xamarin",
    ],
    "soft_skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "critical thinking", "time management", "adaptability",
        "collaboration", "project management", "agile", "scrum",
        "presentation skills", "analytical skills",
    ],
    "tools": [
        "jira", "confluence", "figma", "postman", "vs code", "visual studio",
        "intellij", "eclipse", "slack", "trello",
    ],
}

ALL_SKILLS = {
    skill.lower()
    for group in SKILLS_DB.values()
    for skill in group
}

MAX_SKILL_PHRASE_LEN = max(len(skill.split()) for skill in ALL_SKILLS)

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "for", "with", "at", "by", "from", "up", "down", "into",
    "over", "under", "again", "further", "is", "am", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "will", "would", "shall", "should", "can", "could",
    "may", "might", "must", "this", "that", "these", "those", "i", "you",
    "he", "she", "it", "we", "they", "them", "his", "her", "its", "our",
    "their", "as", "not", "no", "so", "than", "too", "very", "s", "t",
    "just", "about", "above", "after", "before", "between", "both", "each",
    "few", "more", "most", "other", "some", "such", "only", "own", "same",
    "out", "off", "any", "all",
}

EDUCATION_KEYWORDS = {
    "phd": 5, "doctorate": 5,
    "master": 4, "masters": 4, "m.tech": 4, "mtech": 4, "mca": 4, "msc": 4,
    "m.sc": 4, "mba": 4,
    "bachelor": 3, "bachelors": 3, "b.tech": 3, "btech": 3, "bca": 3,
    "bsc": 3, "b.sc": 3, "be": 3, "b.e": 3,
    "diploma": 2,
    "high school": 1, "hsc": 1, "12th": 1,
}
