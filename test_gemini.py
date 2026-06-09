import json
import traceback
from services.gemini_service import generate_candidate_profile

sample_resume = '''John Doe

Experienced Software Engineer with 5 years of experience in Python, Flask, and cloud deployments. Proven track record building scalable REST APIs and working with PostgreSQL and Redis. Led a small team of developers to deliver features on schedule. Skilled in unit testing, CI/CD, Docker, and AWS.

Education:
B.S. in Computer Science

Work Experience:
Software Engineer at Acme Corp (2019-2023): Developed backend services, improved system performance by 30%.
Junior Developer at WebStart (2017-2019): Assisted in frontend and backend development.

Skills: Python, Flask, SQL, PostgreSQL, Redis, Docker, AWS, Kubernetes, REST APIs, Testing, CI/CD, Leadership

'''

try:
    profile = generate_candidate_profile(sample_resume)
    print(json.dumps(profile, indent=2))
except Exception as e:
    traceback.print_exc()
    print('ERROR:', e)
