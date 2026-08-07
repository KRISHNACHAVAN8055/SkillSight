from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, make_response
import sqlite3
import re
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import io
from extensions import limiter
from PyPDF2 import PdfReader
from docx import Document

bp = Blueprint('main', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'skillsight.db')

LEARNING_RESOURCES = {
    'Python': {'why': 'Python is the #1 language for AI, data science, and automation. Demand has grown 85% in 3 years.', 'learn': 'Start with Python.org docs, then move to Automate the Boring Stuff. Practice on HackerRank.', 'time': '4-6 weeks'},
    'JavaScript': {'why': 'JavaScript powers every website. Full-stack JS (React + Node) is among the highest paying skills.', 'learn': 'The Odin Project (free), then build 3 projects. MDN Web Docs for reference.', 'time': '6-8 weeks'},
    'React': {'why': 'React is used by Meta, Netflix, Airbnb. 60% of frontend job postings require React.', 'learn': 'Official React docs (react.dev), then build a todo app, weather app, and portfolio.', 'time': '4-6 weeks'},
    'TypeScript': {'why': 'TypeScript is replacing JavaScript in large codebases. Microsoft, Google, and Airbnb all use it.', 'learn': 'TypeScript Handbook (official), then rewrite a JS project in TS.', 'time': '2-3 weeks'},
    'AWS': {'why': 'Cloud is mandatory. AWS has 32% cloud market share. AWS certified engineers earn 40% more.', 'learn': 'AWS Free Tier + A Cloud Guru. Aim for AWS Cloud Practitioner certification first.', 'time': '6-8 weeks'},
    'Docker': {'why': 'Every modern deployment uses containers. Docker knowledge is expected in all DevOps and backend roles.', 'learn': 'Docker official docs + Play with Docker (free browser lab). Build and containerize a Flask app.', 'time': '2-3 weeks'},
    'Kubernetes': {'why': 'Kubernetes orchestrates containers at scale. Used by every major tech company for production.', 'learn': 'Kubernetes.io docs + KodeKloud free course. Practice on Minikube locally.', 'time': '4-6 weeks'},
    'Machine Learning': {'why': 'ML is the defining skill of the decade. Every company is hiring ML engineers at premium salaries.', 'learn': 'Andrew Ng Coursera ML course (start here), then Kaggle competitions for practice.', 'time': '8-12 weeks'},
    'Deep Learning': {'why': 'Deep Learning powers ChatGPT, image recognition, and recommendations. Fastest growing AI subfield.', 'learn': 'Fast.ai (practical, free), then deeplearning.ai specialization. Build CNN and RNN projects.', 'time': '8-12 weeks'},
    'NLP': {'why': 'NLP is behind every AI assistant, search engine, and chatbot. Demand up 120% since ChatGPT launch.', 'learn': 'Hugging Face course (free), NLTK book (free online), then build a sentiment analyzer.', 'time': '6-8 weeks'},
    'PostgreSQL': {'why': 'PostgreSQL is the most loved database. Used in production by Instagram, Spotify, and Reddit.', 'learn': 'PostgreSQL Tutorial (official), then PgExercises.com for SQL practice.', 'time': '3-4 weeks'},
    'MongoDB': {'why': 'MongoDB leads the NoSQL market. Essential for real-time apps, content platforms, and microservices.', 'learn': 'MongoDB University (free official courses). Build a REST API with Node + MongoDB.', 'time': '3-4 weeks'},
    'Flask': {'why': 'Flask is the go-to Python web framework for APIs and microservices. Lightweight and industry standard.', 'learn': 'Flask Mega-Tutorial by Miguel Grinberg (free). Build a full CRUD app.', 'time': '2-3 weeks'},
    'FastAPI': {'why': 'FastAPI is the fastest growing Python API framework. Used by Netflix and Microsoft for high-performance APIs.', 'learn': 'FastAPI official docs (best docs in Python ecosystem). Build and deploy an API.', 'time': '2-3 weeks'},
    'Git': {'why': 'Git is non-negotiable. Every software job requires it. No Git knowledge = no job.', 'learn': 'Pro Git book (free at git-scm.com), then Oh My Git! (interactive game).', 'time': '1-2 weeks'},
    'DevOps': {'why': 'DevOps engineers are among the highest paid in IT. CI/CD, automation, and reliability are critical skills.', 'learn': 'The Phoenix Project (book), then learn Git + Docker + Jenkins + AWS together.', 'time': '10-12 weeks'},
    'Terraform': {'why': 'Infrastructure as Code is now standard. Terraform lets you manage cloud infra with code.', 'learn': 'HashiCorp Learn (free official tutorials). Build an AWS infrastructure project.', 'time': '3-4 weeks'},
    'Pandas': {'why': 'Pandas is the backbone of all data analysis in Python. Every data role requires it.', 'learn': 'Pandas official docs + Kaggle Pandas micro-course (free, 4 hours).', 'time': '2-3 weeks'},
    'Power BI': {'why': 'Power BI is the most used BI tool in Indian enterprises. Strong demand in analytics roles.', 'learn': 'Microsoft Learn Power BI path (free). Build 3 dashboards from real datasets.', 'time': '3-4 weeks'},
    'Tableau': {'why': 'Tableau is the gold standard for data visualization. Required in most data analyst job postings.', 'learn': 'Tableau Public (free), Tableau eLearning, then publish dashboards on Tableau Public.', 'time': '3-4 weeks'},
    'Go': {'why': 'Go is used by Google, Uber, and Dropbox for high-performance backend systems. Salaries 30% above average.', 'learn': 'Tour of Go (official, interactive), then Go by Example website.', 'time': '4-6 weeks'},
    'Rust': {'why': 'Rust is the most loved language 8 years running. Used in systems programming, WebAssembly, and blockchain.', 'learn': 'The Rust Book (free official). Start with small CLI tools before big projects.', 'time': '8-10 weeks'},
    'Flutter': {'why': 'Flutter lets you build iOS and Android apps from one codebase. Google-backed and rapidly growing.', 'learn': 'Flutter official docs + Angela Yu Flutter course on Udemy.', 'time': '6-8 weeks'},
    'React Native': {'why': 'React Native powers Facebook, Instagram, and Shopify mobile apps. Biggest cross-platform mobile framework.', 'learn': 'React Native official docs, then Expo for quick start. Build a habit tracker app.', 'time': '4-6 weeks'},
    'Kafka': {'why': 'Kafka handles real-time data streams at LinkedIn, Netflix, and Uber. Critical for data engineering roles.', 'learn': 'Confluent Kafka tutorials (free). Build a real-time data pipeline project.', 'time': '4-6 weeks'},
    'Spark': {'why': 'Apache Spark is the industry standard for big data processing. Required in all data engineering roles.', 'learn': 'Spark: The Definitive Guide (book) + Databricks free community edition.', 'time': '6-8 weeks'},
    'GraphQL': {'why': 'GraphQL is replacing REST in modern APIs. Used by GitHub, Shopify, and Twitter.', 'learn': 'GraphQL official docs + HowToGraphQL (free full-stack tutorial).', 'time': '2-3 weeks'},
    'Microservices': {'why': 'Microservices is the dominant architecture for scalable systems. Every large company uses it.', 'learn': 'Microservices.io patterns site, then build a 3-service app with Docker + Flask.', 'time': '6-8 weeks'},
    'Azure': {'why': 'Azure is the dominant cloud in Indian enterprises and MNCs. AZ-900 cert is easy and highly valued.', 'learn': 'Microsoft Learn Azure path (free). Start with AZ-900 certification.', 'time': '4-6 weeks'},
    'GCP': {'why': 'Google Cloud powers YouTube, Google Search, and Spotify. Strong in ML/AI cloud services.', 'learn': 'Google Cloud Skills Boost (free labs). Start with Associate Cloud Engineer path.', 'time': '4-6 weeks'},
    'Scikit-learn': {'why': 'Scikit-learn is the most used ML library for classical algorithms. Every ML engineer needs it.', 'learn': 'Scikit-learn official docs + Kaggle ML course (free).', 'time': '2-3 weeks'},
    'TensorFlow': {'why': 'TensorFlow is Google deep learning framework. Used in production AI at massive scale.', 'learn': 'TensorFlow.org tutorials, then Deep Learning with Python book by Francois Chollet.', 'time': '6-8 weeks'},
    'PyTorch': {'why': 'PyTorch dominates AI research and is rapidly taking over production. Meta, Tesla, and OpenAI use it.', 'learn': 'PyTorch official tutorials + Fast.ai course (built on PyTorch).', 'time': '6-8 weeks'},
    'Node.js': {'why': 'Node.js enables JavaScript on the server. Powers Netflix, PayPal, and LinkedIn backends.', 'learn': 'Node.js official docs + The Odin Project backend path.', 'time': '4-6 weeks'},
    'Spring Boot': {'why': 'Spring Boot is the standard Java framework for enterprise applications in India.', 'learn': 'Baeldung.com (best Spring resource), then build a REST API.', 'time': '4-6 weeks'},
    'Kotlin': {'why': 'Kotlin is the preferred language for Android development, replacing Java. Google-official.', 'learn': 'Kotlin official docs + Android Developer course on developer.android.com.', 'time': '4-6 weeks'},
    'Swift': {'why': 'Swift is Apple language for iOS apps. Required for all native iPhone app development.', 'learn': '100 Days of SwiftUI by Paul Hudson (free, excellent).', 'time': '6-8 weeks'},
    'Redis': {'why': 'Redis is the most popular in-memory cache and message broker. Used by Twitter, GitHub, and Snapchat.', 'learn': 'Redis University (free official courses). Add caching to an existing project.', 'time': '2-3 weeks'},
    'Linux': {'why': 'Linux runs 96% of the worlds servers. Every DevOps, backend, and cloud role requires Linux skills.', 'learn': 'The Linux Command Line book (free online), then practice on a free VPS.', 'time': '3-4 weeks'},
    'jQuery': {'why': 'jQuery is declining fast replaced by modern frameworks. Learn React or Vue instead.', 'learn': 'If required: jQuery official docs. But prioritize React or Vue for your career.', 'time': '1 week'},
    'Hadoop': {'why': 'Hadoop is being replaced by Spark and cloud data warehouses. Low priority for new learners.', 'learn': 'If required: Hadoop: The Definitive Guide. Consider learning Spark instead.', 'time': '4-6 weeks'},
    'PHP': {'why': 'PHP powers 75% of the web (WordPress) but is declining in new projects. Learn for maintenance roles.', 'learn': 'PHP The Right Way (free). Focus on Laravel framework if building new projects.', 'time': '4-6 weeks'},
    'NumPy': {'why': 'NumPy is the foundation of scientific computing in Python. Required for all ML and data roles.', 'learn': 'NumPy official docs + Kaggle micro-course.', 'time': '2-3 weeks'},
    'Vue': {'why': 'Vue is a progressive frontend framework popular in startups and Indian product companies.', 'learn': 'Vue official docs (best docs in frontend ecosystem). Build a SPA project.', 'time': '3-4 weeks'},
    'Angular': {'why': 'Angular is used heavily in Indian enterprise and banking applications.', 'learn': 'Angular official tour of heroes tutorial, then build a dashboard.', 'time': '4-6 weeks'},
    'Django': {'why': 'Django is the batteries-included Python web framework. Used by Instagram and Pinterest.', 'learn': 'Django Girls tutorial (free), then Django for APIs book.', 'time': '4-6 weeks'},
    'MySQL': {'why': 'MySQL is the most widely deployed database in Indian web applications.', 'learn': 'MySQL tutorial on w3schools, then practice on HackerRank SQL.', 'time': '3-4 weeks'},
    'Excel': {'why': 'Excel is still required in most business analyst and data analyst roles in India.', 'learn': 'ExcelJet.net for formulas, then build 3 dashboard projects.', 'time': '2-3 weeks'},
    'Jenkins': {'why': 'Jenkins is the most used CI/CD automation tool in Indian IT services companies.', 'learn': 'Jenkins official docs + Udemy Jenkins course. Set up a pipeline for a Flask app.', 'time': '2-3 weeks'},
    'REST API': {'why': 'REST API design is fundamental to all backend and full stack development roles.', 'learn': 'RESTful Web APIs book + build 3 APIs using Flask or FastAPI.', 'time': '2-3 weeks'},
    'Computer Vision': {'why': 'Computer Vision powers autonomous vehicles, medical imaging, and retail analytics.', 'learn': 'OpenCV Python tutorial + fast.ai vision course. Build an object detection project.', 'time': '8-10 weeks'},
    'C++': {'why': 'C++ is essential for systems programming, game development, and competitive coding.', 'learn': 'LearnCpp.com (free, comprehensive). Practice on Codeforces.', 'time': '10-12 weeks'},
    'C#': {'why': 'C# is the primary language for .NET development and Unity game engine.', 'learn': 'Microsoft Learn C# path (free). Build a web app with ASP.NET Core.', 'time': '6-8 weeks'},
    'Ruby': {'why': 'Ruby on Rails is used by GitHub and Shopify. Declining but still relevant for legacy systems.', 'learn': 'Ruby on Rails tutorial by Michael Hartl (free online).', 'time': '4-6 weeks'},
    'Cassandra': {'why': 'Cassandra handles massive write workloads at Netflix and Apple. Niche but high paying.', 'learn': 'DataStax Academy free courses. Build a time-series data project.', 'time': '4-6 weeks'},
    'SQLite': {'why': 'SQLite is the most deployed database in the world. Essential for mobile and embedded apps.', 'learn': 'SQLite official docs + Python sqlite3 module tutorial.', 'time': '1-2 weeks'},
}

DEFAULT_RESOURCE = {
    'why': 'This is an emerging skill with growing demand in the Indian IT market.',
    'learn': 'Check official documentation and look for free courses on Coursera, edX, or YouTube.',
    'time': '4-6 weeks'
}

SKILL_EXTRA = {
    'Python': {'salary': 'Rs 6L-30L', 'difficulty': 'Beginner', 'time_to_learn': '4-6 weeks'},
    'JavaScript': {'salary': 'Rs 5L-25L', 'difficulty': 'Beginner', 'time_to_learn': '6-8 weeks'},
    'React': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'TypeScript': {'salary': 'Rs 8L-28L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'AWS': {'salary': 'Rs 10L-40L', 'difficulty': 'Intermediate', 'time_to_learn': '6-8 weeks'},
    'Docker': {'salary': 'Rs 8L-30L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'Kubernetes': {'salary': 'Rs 12L-45L', 'difficulty': 'Advanced', 'time_to_learn': '4-6 weeks'},
    'Machine Learning': {'salary': 'Rs 10L-40L', 'difficulty': 'Advanced', 'time_to_learn': '8-12 weeks'},
    'Deep Learning': {'salary': 'Rs 14L-50L', 'difficulty': 'Advanced', 'time_to_learn': '8-12 weeks'},
    'NLP': {'salary': 'Rs 12L-45L', 'difficulty': 'Advanced', 'time_to_learn': '6-8 weeks'},
    'PostgreSQL': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '3-4 weeks'},
    'MongoDB': {'salary': 'Rs 6L-22L', 'difficulty': 'Beginner', 'time_to_learn': '3-4 weeks'},
    'Flask': {'salary': 'Rs 5L-18L', 'difficulty': 'Beginner', 'time_to_learn': '2-3 weeks'},
    'FastAPI': {'salary': 'Rs 8L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'Git': {'salary': 'Rs 4L-15L', 'difficulty': 'Beginner', 'time_to_learn': '1-2 weeks'},
    'DevOps': {'salary': 'Rs 10L-40L', 'difficulty': 'Advanced', 'time_to_learn': '10-12 weeks'},
    'Terraform': {'salary': 'Rs 12L-40L', 'difficulty': 'Advanced', 'time_to_learn': '3-4 weeks'},
    'Pandas': {'salary': 'Rs 6L-20L', 'difficulty': 'Beginner', 'time_to_learn': '2-3 weeks'},
    'Power BI': {'salary': 'Rs 5L-18L', 'difficulty': 'Beginner', 'time_to_learn': '3-4 weeks'},
    'Tableau': {'salary': 'Rs 6L-20L', 'difficulty': 'Beginner', 'time_to_learn': '3-4 weeks'},
    'Go': {'salary': 'Rs 10L-35L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'Rust': {'salary': 'Rs 14L-45L', 'difficulty': 'Advanced', 'time_to_learn': '8-10 weeks'},
    'Flutter': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '6-8 weeks'},
    'React Native': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'Kafka': {'salary': 'Rs 12L-38L', 'difficulty': 'Advanced', 'time_to_learn': '4-6 weeks'},
    'Spark': {'salary': 'Rs 12L-40L', 'difficulty': 'Advanced', 'time_to_learn': '6-8 weeks'},
    'jQuery': {'salary': 'Rs 3L-10L', 'difficulty': 'Beginner', 'time_to_learn': '1 week'},
    'Hadoop': {'salary': 'Rs 6L-20L', 'difficulty': 'Advanced', 'time_to_learn': '4-6 weeks'},
    'PHP': {'salary': 'Rs 3L-12L', 'difficulty': 'Beginner', 'time_to_learn': '4-6 weeks'},
    'Java': {'salary': 'Rs 6L-28L', 'difficulty': 'Intermediate', 'time_to_learn': '8-12 weeks'},
    'Azure': {'salary': 'Rs 10L-38L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'GCP': {'salary': 'Rs 10L-38L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'Linux': {'salary': 'Rs 6L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '3-4 weeks'},
    'Kotlin': {'salary': 'Rs 7L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'Swift': {'salary': 'Rs 8L-28L', 'difficulty': 'Intermediate', 'time_to_learn': '6-8 weeks'},
    'Redis': {'salary': 'Rs 7L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'GraphQL': {'salary': 'Rs 8L-28L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'Microservices': {'salary': 'Rs 12L-40L', 'difficulty': 'Advanced', 'time_to_learn': '6-8 weeks'},
    'TensorFlow': {'salary': 'Rs 12L-40L', 'difficulty': 'Advanced', 'time_to_learn': '6-8 weeks'},
    'PyTorch': {'salary': 'Rs 14L-45L', 'difficulty': 'Advanced', 'time_to_learn': '6-8 weeks'},
    'Scikit-learn': {'salary': 'Rs 8L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '2-3 weeks'},
    'Node.js': {'salary': 'Rs 6L-25L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'Spring Boot': {'salary': 'Rs 7L-28L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'NumPy': {'salary': 'Rs 6L-20L', 'difficulty': 'Beginner', 'time_to_learn': '2-3 weeks'},
    'Vue': {'salary': 'Rs 5L-18L', 'difficulty': 'Intermediate', 'time_to_learn': '3-4 weeks'},
    'Angular': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
    'C++': {'salary': 'Rs 6L-25L', 'difficulty': 'Advanced', 'time_to_learn': '10-12 weeks'},
    'REST API': {'salary': 'Rs 5L-20L', 'difficulty': 'Beginner', 'time_to_learn': '2-3 weeks'},
    'Computer Vision': {'salary': 'Rs 12L-40L', 'difficulty': 'Advanced', 'time_to_learn': '8-10 weeks'},
    'MySQL': {'salary': 'Rs 4L-16L', 'difficulty': 'Beginner', 'time_to_learn': '3-4 weeks'},
    'Excel': {'salary': 'Rs 3L-12L', 'difficulty': 'Beginner', 'time_to_learn': '2-3 weeks'},
    'C#': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '6-8 weeks'},
    'Django': {'salary': 'Rs 6L-22L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'},
}

DEFAULT_EXTRA = {'salary': 'Rs 5L-20L', 'difficulty': 'Intermediate', 'time_to_learn': '4-6 weeks'}

CAREER_ROLES = {
    'Data Scientist': {
        'description': 'Analyze complex data to help companies make better decisions using ML and statistics.',
        'required': ['Python', 'Machine Learning', 'Pandas', 'NumPy', 'Scikit-learn', 'MySQL'],
        'salary': 'Rs 8L-25L per year',
        'roadmap_target': ['Machine Learning', 'Deep Learning', 'TensorFlow', 'MySQL']
    },
    'ML Engineer': {
        'description': 'Build and deploy machine learning models into production systems at scale.',
        'required': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Docker', 'AWS'],
        'salary': 'Rs 12L-35L per year',
        'roadmap_target': ['Deep Learning', 'Docker', 'AWS', 'PyTorch']
    },
    'Full Stack Developer': {
        'description': 'Build complete web applications handling both frontend and backend development.',
        'required': ['JavaScript', 'React', 'Node.js', 'Python', 'MySQL', 'Git', 'REST API'],
        'salary': 'Rs 6L-20L per year',
        'roadmap_target': ['React', 'Node.js', 'PostgreSQL', 'Docker']
    },
    'DevOps Engineer': {
        'description': 'Automate software delivery pipelines and manage cloud infrastructure at scale.',
        'required': ['Docker', 'Kubernetes', 'AWS', 'Linux', 'Git', 'Terraform', 'Jenkins'],
        'salary': 'Rs 10L-30L per year',
        'roadmap_target': ['Kubernetes', 'Terraform', 'AWS', 'Linux']
    },
    'Backend Developer': {
        'description': 'Design and build server-side logic, APIs, and databases for web applications.',
        'required': ['Python', 'Java', 'Node.js', 'PostgreSQL', 'MongoDB', 'REST API', 'Git'],
        'salary': 'Rs 6L-22L per year',
        'roadmap_target': ['FastAPI', 'PostgreSQL', 'Docker', 'Redis']
    },
    'Data Analyst': {
        'description': 'Collect, process, and analyze data to generate actionable business insights.',
        'required': ['Python', 'MySQL', 'Pandas', 'Excel', 'Tableau', 'Power BI'],
        'salary': 'Rs 5L-15L per year',
        'roadmap_target': ['Tableau', 'Power BI', 'PostgreSQL', 'Pandas']
    },
    'Cloud Architect': {
        'description': 'Design and oversee cloud computing strategies and infrastructure for organizations.',
        'required': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Linux'],
        'salary': 'Rs 15L-45L per year',
        'roadmap_target': ['AWS', 'Terraform', 'Kubernetes', 'Azure']
    },
    'Mobile Developer': {
        'description': 'Build native and cross-platform mobile applications for iOS and Android.',
        'required': ['Flutter', 'Kotlin', 'Swift', 'REST API', 'Git'],
        'salary': 'Rs 6L-22L per year',
        'roadmap_target': ['Flutter', 'Kotlin', 'Firebase', 'REST API']
    },
}

ROADMAP_TEMPLATES = {
    'data_science': [
        {'title': 'Python for data analysis', 'description': 'Master Pandas and NumPy the foundation of all data science work.', 'skills': ['Python', 'Pandas', 'NumPy'], 'duration': '3-4 weeks', 'resources': 'Kaggle micro-courses, Pandas docs'},
        {'title': 'Statistics and probability', 'description': 'Understand hypothesis testing, regression, and statistical inference.', 'skills': ['Statistics', 'NumPy'], 'duration': '3-4 weeks', 'resources': 'Khan Academy Statistics, Think Stats book'},
        {'title': 'Machine learning fundamentals', 'description': 'Learn classification, regression, clustering with Scikit-learn.', 'skills': ['Machine Learning', 'Scikit-learn'], 'duration': '6-8 weeks', 'resources': 'Andrew Ng Coursera, Kaggle ML course'},
        {'title': 'Data visualization', 'description': 'Tell stories with data using Tableau and Python visualization libraries.', 'skills': ['Tableau', 'Power BI'], 'duration': '3-4 weeks', 'resources': 'Tableau Public, Matplotlib docs'},
        {'title': 'SQL for data', 'description': 'Query and analyze large datasets using advanced SQL techniques.', 'skills': ['PostgreSQL', 'MySQL'], 'duration': '2-3 weeks', 'resources': 'Mode SQL Tutorial, PgExercises'},
        {'title': 'Deep learning and AI', 'description': 'Build neural networks with TensorFlow and PyTorch for advanced AI.', 'skills': ['Deep Learning', 'TensorFlow', 'PyTorch'], 'duration': '8-10 weeks', 'resources': 'Fast.ai, DeepLearning.AI'}
    ],
    'devops': [
        {'title': 'Linux and command line', 'description': 'Master the Linux command line essential for all DevOps work.', 'skills': ['Linux'], 'duration': '2-3 weeks', 'resources': 'The Linux Command Line book'},
        {'title': 'Git and version control', 'description': 'Master Git workflows used in professional software teams.', 'skills': ['Git'], 'duration': '1-2 weeks', 'resources': 'Pro Git book, Oh My Git!'},
        {'title': 'Containerization with Docker', 'description': 'Package applications in containers for consistent deployments.', 'skills': ['Docker'], 'duration': '2-3 weeks', 'resources': 'Docker official docs'},
        {'title': 'Container orchestration', 'description': 'Manage containers at scale with Kubernetes.', 'skills': ['Kubernetes'], 'duration': '4-6 weeks', 'resources': 'Kubernetes.io, KodeKloud'},
        {'title': 'Cloud infrastructure', 'description': 'Deploy and manage infrastructure on AWS or Azure.', 'skills': ['AWS', 'Azure', 'Terraform'], 'duration': '6-8 weeks', 'resources': 'AWS Free Tier, HashiCorp Learn'},
        {'title': 'CI/CD and automation', 'description': 'Build automated pipelines for testing and deployment.', 'skills': ['DevOps', 'Jenkins'], 'duration': '3-4 weeks', 'resources': 'GitHub Actions docs'}
    ],
    'general': [
        {'title': 'Strengthen your core language', 'description': 'Go deeper with your primary programming language and master advanced concepts.', 'skills': ['Python', 'JavaScript', 'Java'], 'duration': '3-4 weeks', 'resources': 'Official docs, LeetCode for practice'},
        {'title': 'Add cloud skills', 'description': 'Cloud is mandatory in modern IT. Start with AWS fundamentals.', 'skills': ['AWS', 'Docker'], 'duration': '4-6 weeks', 'resources': 'AWS Free Tier, A Cloud Guru'},
        {'title': 'Learn a database deeply', 'description': 'Master one SQL and one NoSQL database for full data handling capability.', 'skills': ['PostgreSQL', 'MongoDB'], 'duration': '3-4 weeks', 'resources': 'PostgreSQL Tutorial, MongoDB University'},
        {'title': 'Build AI/ML awareness', 'description': 'Every developer needs ML fundamentals in the current market.', 'skills': ['Machine Learning', 'Scikit-learn', 'Python'], 'duration': '6-8 weeks', 'resources': 'Andrew Ng Coursera, Kaggle'},
        {'title': 'Master DevOps basics', 'description': 'Learn Git, Docker, and basic CI/CD for professional deployments.', 'skills': ['Git', 'Docker', 'DevOps'], 'duration': '3-4 weeks', 'resources': 'Docker docs, GitHub Actions'},
        {'title': 'Build your portfolio', 'description': 'Build 3 real projects combining all your skills and deploy them online.', 'skills': ['GitHub', 'AWS', 'React'], 'duration': '4-6 weeks', 'resources': 'GitHub Pages, AWS Free Tier'}
    ]
}

JOB_TRENDS = [
    {'role': 'AI/ML Engineer', 'domain': 'AI/ML', 'description': 'Build, train, and deploy machine learning models into production systems.', 'demand_score': 96, 'growth': 87, 'openings': '12,400+', 'salary': 'Rs 12L-50L', 'color': '#7c83fd', 'is_hot': True, 'is_new': False, 'key_skills': ['Python', 'PyTorch', 'TensorFlow', 'Machine Learning', 'Docker', 'AWS'], 'why_trending': ['ChatGPT and generative AI created an explosion in ML hiring across all sectors', 'Every major Indian IT company is building AI/ML teams from scratch in 2025-26', 'NASSCOM reports 40% salary premium for ML engineers over traditional software roles']},
    {'role': 'DevOps / Platform Engineer', 'domain': 'Cloud', 'description': 'Automate software delivery, manage cloud infrastructure, and ensure system reliability at scale.', 'demand_score': 91, 'growth': 62, 'openings': '9,800+', 'salary': 'Rs 10L-42L', 'color': '#f87171', 'is_hot': True, 'is_new': False, 'key_skills': ['Docker', 'Kubernetes', 'AWS', 'Terraform', 'Linux', 'Git'], 'why_trending': ['Cloud adoption in Indian enterprises grew 38% in 2025 driving massive DevOps demand', 'Every startup and MNC is moving from on-premise to cloud-native architecture', 'CI/CD automation is now mandatory in all software delivery pipelines']},
    {'role': 'Generative AI Engineer', 'domain': 'AI/ML', 'description': 'Build products and APIs on top of large language models like GPT, Gemini, and open-source alternatives.', 'demand_score': 94, 'growth': 210, 'openings': '6,200+', 'salary': 'Rs 15L-60L', 'color': '#f472b6', 'is_hot': True, 'is_new': True, 'key_skills': ['Python', 'NLP', 'FastAPI', 'PyTorch', 'AWS'], 'why_trending': ['Entirely new job category created by the ChatGPT revolution', 'Indian product companies and startups are building GenAI features at record speed', 'Massive talent shortage demand outpaces supply by 8x']},
    {'role': 'Cloud Architect', 'domain': 'Cloud', 'description': 'Design enterprise cloud strategies and infrastructure across AWS, Azure, and GCP.', 'demand_score': 88, 'growth': 54, 'openings': '7,500+', 'salary': 'Rs 18L-55L', 'color': '#60a5fa', 'is_hot': False, 'is_new': False, 'key_skills': ['AWS', 'Azure', 'GCP', 'Kubernetes', 'Terraform'], 'why_trending': ['India is the number 2 country globally for cloud architect hiring behind only USA', 'Digital India initiative pushing government and PSUs to cloud at scale', 'Multi-cloud strategy adoption means architects need cross-platform expertise']},
    {'role': 'Full Stack Developer', 'domain': 'Web', 'description': 'Build complete web applications from database to user interface using modern frameworks.', 'demand_score': 85, 'growth': 38, 'openings': '24,000+', 'salary': 'Rs 6L-28L', 'color': '#4ade80', 'is_hot': False, 'is_new': False, 'key_skills': ['React', 'Node.js', 'TypeScript', 'PostgreSQL', 'Docker', 'AWS'], 'why_trending': ['Highest volume role in Indian IT every product company needs full stack engineers', 'React and Node.js have become the dominant stack replacing older Java-based setups', 'Startup ecosystem growth creating thousands of openings']},
    {'role': 'Data Engineer', 'domain': 'Data', 'description': 'Build and maintain data pipelines, warehouses, and infrastructure that power business analytics.', 'demand_score': 83, 'growth': 71, 'openings': '8,900+', 'salary': 'Rs 10L-38L', 'color': '#fbbf24', 'is_hot': True, 'is_new': False, 'key_skills': ['Python', 'Spark', 'Kafka', 'PostgreSQL', 'AWS'], 'why_trending': ['Every company wants data-driven decisions but needs engineers to build the data infrastructure first', 'Real-time data processing demand has tripled since 2023', 'Data engineering now pays more than data science in many Indian product companies']},
    {'role': 'Data Analyst', 'domain': 'Data', 'description': 'Transform raw business data into actionable insights using SQL, Python, and visualization tools.', 'demand_score': 71, 'growth': 29, 'openings': '18,000+', 'salary': 'Rs 5L-18L', 'color': '#38bdf8', 'is_hot': False, 'is_new': False, 'key_skills': ['Python', 'MySQL', 'Tableau', 'Power BI', 'Excel', 'Pandas'], 'why_trending': ['Highest volume entry-level tech role in India with 18,000+ openings across industries', 'Every domain from healthcare to fintech to retail hiring data analysts', 'Power BI and Tableau certifications dramatically improve hiring chances']},
    {'role': 'Flutter Mobile Developer', 'domain': 'Mobile', 'description': 'Build cross-platform mobile applications for iOS and Android from a single codebase.', 'demand_score': 74, 'growth': 45, 'openings': '6,800+', 'salary': 'Rs 6L-24L', 'color': '#a78bfa', 'is_hot': False, 'is_new': False, 'key_skills': ['Flutter', 'Dart', 'Firebase', 'REST API', 'Git'], 'why_trending': ['Flutter has overtaken React Native as the preferred cross-platform framework in India', 'India massive smartphone user base makes mobile development a high-priority investment', 'Google-backed with strong enterprise adoption']},
    {'role': 'NLP Engineer', 'domain': 'AI/ML', 'description': 'Build chatbots, voice assistants, and language understanding systems using NLP techniques.', 'demand_score': 78, 'growth': 125, 'openings': '4,200+', 'salary': 'Rs 12L-45L', 'color': '#34d399', 'is_hot': True, 'is_new': True, 'key_skills': ['Python', 'NLP', 'PyTorch', 'FastAPI'], 'why_trending': ['Every Indian bank, insurance company, and e-commerce platform building conversational AI', 'Government initiatives pushing NLP for Indian regional languages', 'Demand for multilingual Indian language model engineers is skyrocketing']},
    {'role': 'Cybersecurity Analyst', 'domain': 'Cloud', 'description': 'Protect organizational systems, networks, and data from cyber threats and breaches.', 'demand_score': 80, 'growth': 93, 'openings': '5,600+', 'salary': 'Rs 8L-35L', 'color': '#fb923c', 'is_hot': True, 'is_new': False, 'key_skills': ['Linux', 'Python', 'AWS', 'Networking'], 'why_trending': ['India saw 2.1 million cyber attacks in 2025 making security a boardroom priority', 'RBI and SEBI mandating cybersecurity frameworks for all regulated entities', 'Critical shortage India has less than 30% of the cybersecurity talent it needs']},
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            return redirect(url_for('main.index'))
        else:
            error = 'Invalid email or password.'
    return render_template('login.html', error=error)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not full_name or not email or not password:
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                hashed = generate_password_hash(password, method='pbkdf2:sha256')
                cursor.execute('INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)',
                               (full_name, email, hashed))
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                session['user_id'] = user_id
                session['user_name'] = full_name
                return redirect(url_for('main.index'))
            except sqlite3.IntegrityError:
                error = 'An account with this email already exists.'
    return render_template('signup.html', error=error)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))


@bp.route('/')
@login_required
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM skill_forecasts ORDER BY obsolescence_score ASC')
    skills = [dict(row) for row in cursor.fetchall()]
    stats = {
        'total': len(skills),
        'rising': sum(1 for s in skills if s['category'] == 'Rising'),
        'stable': sum(1 for s in skills if s['category'] == 'Stable'),
        'declining': sum(1 for s in skills if s['category'] == 'Declining'),
        'critical': sum(1 for s in skills if s['category'] == 'Critical'),
    }
    conn.close()
    return render_template('index.html', skills=skills, stats=stats,
                           resources=LEARNING_RESOURCES,
                           user_name=session.get('user_name', ''))


def generate_score_explanation(skill, historical_counts):
    slope = skill['slope']
    score = skill['obsolescence_score']
    category = skill['category']
    data_points = len(historical_counts)

    if data_points < 3:
        confidence = "Low"
        confidence_note = "Not enough historical data available yet for a reliable trend. This score may change significantly as more data is collected."
    elif data_points < 6:
        confidence = "Medium"
        confidence_note = f"Based on {data_points} months of data. More historical data will improve accuracy over time."
    else:
        confidence = "High"
        confidence_note = f"Based on {data_points} months of consistent market data."

    if category == 'Rising':
        trend_text = f"This skill's mentions in real job postings have been increasing (trend slope: {slope}). Demand is growing month over month."
    elif category == 'Stable':
        trend_text = f"This skill's demand has stayed roughly flat over time (trend slope: {slope}). Neither growing nor shrinking significantly."
    elif category == 'Declining':
        trend_text = f"This skill's mentions in job postings have been slowly decreasing (trend slope: {slope}). Worth monitoring, not yet urgent."
    else:
        trend_text = f"This skill's mentions in job postings have dropped sharply (trend slope: {slope}). Demand is fading quickly."

    return {
        'trend_text': trend_text,
        'confidence': confidence,
        'confidence_note': confidence_note,
        'formula_note': "Score is calculated from the rate of change (slope) in how often this skill appears in real job postings each month, not a fixed opinion."
    }


@bp.route('/skill/<skill_name>')
@login_required
def skill_detail(skill_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM skill_forecasts WHERE skill = ?', (skill_name,))
    row = cursor.fetchone()
    if not row:
        return redirect(url_for('main.index'))
    skill = dict(row)
    cursor.execute('SELECT month, normalized_count FROM skill_mentions WHERE skill = ? ORDER BY month ASC', (skill_name,))
    history = cursor.fetchall()
    conn.close()
    historical_months = [r['month'] for r in history]
    historical_counts = [r['normalized_count'] for r in history]
    forecast = json.loads(skill['forecast_json'])
    resource = LEARNING_RESOURCES.get(skill_name, DEFAULT_RESOURCE)
    explanation = generate_score_explanation(skill, historical_counts)
    return render_template('skill_detail.html', skill=skill,
                           historical_months=historical_months,
                           historical_counts=historical_counts,
                           explanation=explanation,
                           forecast=forecast, resource=resource,
                           user_name=session.get('user_name', ''))


@bp.route('/api/skill/<skill_name>')
def api_skill(skill_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM skill_forecasts WHERE skill = ?', (skill_name,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    skill = dict(row)
    cursor.execute('SELECT month, normalized_count FROM skill_mentions WHERE skill = ? ORDER BY month ASC', (skill_name,))
    history = cursor.fetchall()
    conn.close()
    historical_months = [r['month'] for r in history]
    historical_counts = [r['normalized_count'] for r in history]
    forecast = json.loads(skill['forecast_json'])
    resource = LEARNING_RESOURCES.get(skill_name, DEFAULT_RESOURCE)
    return jsonify({
        'skill': skill,
        'historical_months': historical_months,
        'historical_counts': historical_counts,
        'forecast': forecast,
        'resource': resource
    })


@bp.route('/compare')
@login_required
def compare():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT skill FROM skill_forecasts ORDER BY skill ASC')
    skills = [row['skill'] for row in cursor.fetchall()]
    conn.close()
    return render_template('compare.html', skills=skills,
                           skill_data=SKILL_EXTRA,
                           user_name=session.get('user_name', ''))


@bp.route('/api/compare')
def api_compare():
    s1 = request.args.get('skill1')
    s2 = request.args.get('skill2')
    conn = get_connection()
    cursor = conn.cursor()

    def get_trend(skill):
        cursor.execute('SELECT month, normalized_count FROM skill_mentions WHERE skill = ? ORDER BY month ASC', (skill,))
        rows = cursor.fetchall()
        return {'months': [r['month'] for r in rows], 'counts': [r['normalized_count'] for r in rows]}

    def get_info(skill):
        cursor.execute('SELECT * FROM skill_forecasts WHERE skill = ?', (skill,))
        row = cursor.fetchone()
        if not row:
            return {}
        res = LEARNING_RESOURCES.get(skill, DEFAULT_RESOURCE)
        extra = SKILL_EXTRA.get(skill, DEFAULT_EXTRA)
        return {
            'skill': skill,
            'obsolescence_score': dict(row)['obsolescence_score'],
            'slope': dict(row)['slope'],
            'category': dict(row)['category'],
            'why': res['why'],
            'learn': res['learn'],
            'salary': extra['salary'],
            'difficulty': extra['difficulty'],
            'time_to_learn': extra['time_to_learn']
        }

    def get_forecast(skill):
        cursor.execute('SELECT forecast_json FROM skill_forecasts WHERE skill = ?', (skill,))
        row = cursor.fetchone()
        if row:
            return json.loads(row['forecast_json'])
        return {}

    data = {
        'skill1': get_trend(s1),
        'skill2': get_trend(s2),
        'skill1_info': get_info(s1),
        'skill2_info': get_info(s2),
        'skill1_forecast': get_forecast(s1),
        'skill2_forecast': get_forecast(s2),
    }
    conn.close()
    return jsonify(data)


@bp.route('/gap')
@login_required
def gap():
    return render_template('gap.html', user_name=session.get('user_name', ''))


@bp.route('/api/gap', methods=['POST'])
def api_gap():
    user_skills = request.json.get('skills', [])
    conn = get_connection()
    cursor = conn.cursor()
    results = []
    not_found = []

    for skill in user_skills:
        cursor.execute('SELECT * FROM skill_forecasts WHERE LOWER(skill) = LOWER(?)', (skill,))
        row = cursor.fetchone()
        if row:
            res = LEARNING_RESOURCES.get(row['skill'], DEFAULT_RESOURCE)
            results.append({
                'skill': row['skill'],
                'score': row['obsolescence_score'],
                'slope': row['slope'],
                'category': row['category'],
                'why': res['why'],
                'learn': res['learn'],
                'time': res['time']
            })
        else:
            not_found.append(skill)

    user_skill_names = [r['skill'].lower() for r in results]
    user_categories = {
        'has_ml': any(s in user_skill_names for s in ['machine learning', 'deep learning', 'pytorch', 'tensorflow', 'scikit-learn']),
        'has_cloud': any(s in user_skill_names for s in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']),
        'has_frontend': any(s in user_skill_names for s in ['react', 'angular', 'vue', 'typescript']),
        'has_backend': any(s in user_skill_names for s in ['node.js', 'flask', 'fastapi', 'django', 'spring boot']),
        'has_data': any(s in user_skill_names for s in ['pandas', 'numpy', 'spark', 'kafka']),
        'has_db': any(s in user_skill_names for s in ['postgresql', 'mongodb', 'mysql', 'redis']),
        'has_devops': any(s in user_skill_names for s in ['devops', 'terraform', 'jenkins', 'kubernetes', 'docker']),
        'has_mobile': any(s in user_skill_names for s in ['flutter', 'react native', 'kotlin', 'swift']),
    }

    recommendation_map = [
        ('has_cloud', ['AWS', 'Docker', 'Azure']),
        ('has_ml', ['Machine Learning', 'Python', 'Scikit-learn']),
        ('has_frontend', ['React', 'TypeScript', 'Vue']),
        ('has_backend', ['FastAPI', 'Node.js', 'Flask']),
        ('has_data', ['Pandas', 'Spark', 'Kafka']),
        ('has_db', ['PostgreSQL', 'MongoDB', 'Redis']),
        ('has_devops', ['DevOps', 'Terraform', 'Kubernetes']),
        ('has_mobile', ['Flutter', 'React Native', 'Kotlin']),
    ]

    replacement_map = {
        'jQuery': ['React', 'TypeScript'],
        'Hadoop': ['Spark', 'Kafka'],
        'PHP': ['Python', 'Node.js'],
        'Ruby': ['Python', 'Go'],
        'Angular': ['React', 'Vue'],
        'Jenkins': ['DevOps', 'Terraform'],
        'Excel': ['Tableau', 'Power BI'],
    }

    declining_user_skills = [r['skill'] for r in results if r['category'] in ['Declining', 'Critical']]
    recommended_skill_names = set()
    recommendations = []

    for declining in declining_user_skills:
        for rep in replacement_map.get(declining, []):
            if rep.lower() not in user_skill_names and rep not in recommended_skill_names:
                res = LEARNING_RESOURCES.get(rep, DEFAULT_RESOURCE)
                cursor.execute('SELECT * FROM skill_forecasts WHERE LOWER(skill) = LOWER(?)', (rep,))
                row = cursor.fetchone()
                score = dict(row)['obsolescence_score'] if row else 20
                category = dict(row)['category'] if row else 'Rising'
                recommendations.append({
                    'skill': rep, 'score': score, 'category': category,
                    'why': f"Modern replacement for {declining}. " + res['why'],
                    'learn': res['learn'], 'time': res['time'],
                    'reason': f'Replaces your declining skill: {declining}'
                })
                recommended_skill_names.add(rep)

    for category_key, skill_list in recommendation_map:
        if not user_categories[category_key]:
            for skill_name in skill_list:
                if skill_name.lower() not in user_skill_names and skill_name not in recommended_skill_names:
                    res = LEARNING_RESOURCES.get(skill_name, DEFAULT_RESOURCE)
                    cursor.execute('SELECT * FROM skill_forecasts WHERE LOWER(skill) = LOWER(?)', (skill_name,))
                    row = cursor.fetchone()
                    score = dict(row)['obsolescence_score'] if row else 20
                    cat = dict(row)['category'] if row else 'Rising'
                    recommendations.append({
                        'skill': skill_name, 'score': score, 'category': cat,
                        'why': res['why'], 'learn': res['learn'], 'time': res['time'],
                        'reason': f'You have no {category_key.replace("has_", "").upper()} skills yet'
                    })
                    recommended_skill_names.add(skill_name)
                    break

    recommendations = recommendations[:6]
    conn.close()

    avg_score = round(sum(r['score'] for r in results) / len(results), 1) if results else 0
    overall_risk = 'High' if avg_score > 60 else ('Medium' if avg_score > 40 else 'Low')
    critical_skills = [r['skill'] for r in results if r['category'] == 'Critical']
    declining_skills = [r['skill'] for r in results if r['category'] == 'Declining']

    if critical_skills:
        summary = f"{len(critical_skills)} of your skills ({', '.join(critical_skills)}) are Critical and losing demand fast."
    elif declining_skills:
        summary = f"{len(declining_skills)} of your skills ({', '.join(declining_skills)}) are declining. Start learning replacements now."
    else:
        summary = "Your skill set looks healthy! Keep updating with emerging technologies to stay ahead."

    return jsonify({
        'analyzed': len(results),
        'avg_score': avg_score,
        'overall_risk': overall_risk,
        'summary_text': summary,
        'skill_results': results,
        'not_found': not_found,
        'recommendations': recommendations
    })


@bp.route('/api/gap/pdf', methods=['POST'])
def download_report():
    from fpdf import FPDF
    data = request.json
    skill_results = data.get('skill_results', [])
    recommendations = data.get('recommendations', [])
    user_name = data.get('user_name', 'User')
    avg_score = data.get('avg_score', 0)
    overall_risk = data.get('overall_risk', 'Unknown')
    summary_text = data.get('summary_text', '')

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(26, 29, 46)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(124, 131, 253)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, 'SkillSight', ln=True)
    pdf.set_text_color(160, 163, 177)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_x(10)
    pdf.cell(0, 6, 'AI-Driven Skill Obsolescence Predictor', ln=True)
    pdf.set_text_color(200, 200, 200)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(10)
    pdf.cell(0, 6, f'Personalized Learning Report   Prepared for: {user_name}', ln=True)
    pdf.set_xy(10, 42)

    risk_r = (231, 76, 60) if overall_risk == 'High' else (243, 156, 18) if overall_risk == 'Medium' else (39, 174, 96)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(26, 29, 46)
    pdf.cell(0, 8, 'Risk Summary', ln=True)
    pdf.ln(1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(63, 6, 'Skills Analyzed', align='C')
    pdf.cell(63, 6, 'Overall Risk', align='C')
    pdf.cell(63, 6, 'Avg Score', align='C', ln=True)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(26, 29, 46)
    pdf.cell(63, 10, str(len(skill_results)), align='C')
    pdf.set_text_color(*risk_r)
    pdf.cell(63, 10, overall_risk, align='C')
    pdf.set_text_color(26, 29, 46)
    pdf.cell(63, 10, str(avg_score), align='C', ln=True)
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, summary_text.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(4)

    pdf.set_text_color(26, 29, 46)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'Your Skill Analysis', ln=True, border='B')
    pdf.ln(3)
    for s in skill_results:
        cat = s['category']
        cr, cg, cb = (39,174,96) if cat=='Rising' else (52,152,219) if cat=='Stable' else (243,156,18) if cat=='Declining' else (231,76,60)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(26, 29, 46)
        pdf.cell(80, 7, s['skill'], border=0)
        pdf.set_text_color(cr, cg, cb)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 7, f'[{cat}]', border=0)
        pdf.set_text_color(120, 120, 120)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 7, f"Score: {s['score']}", ln=True)
        pdf.set_text_color(60, 60, 60)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'Why this matters:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, s['why'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'How to learn:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, s['learn'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'Time to learn:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, s['time'], ln=True)
        pdf.ln(3)

    pdf.set_text_color(26, 29, 46)
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(0, 8, 'Recommended Skills to Learn Next', ln=True, border='B')
    pdf.ln(3)
    for r in recommendations:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(39, 174, 96)
        pdf.cell(80, 7, r['skill'], border=0)
        pdf.set_text_color(120, 120, 120)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 7, f"Score: {r['score']}", ln=True)
        if r.get('reason'):
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(140, 140, 160)
            pdf.cell(0, 4, r['reason'].encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_text_color(60, 60, 60)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'Why learn this:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, r['why'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'How to start:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, r['learn'].encode('latin-1', 'replace').decode('latin-1'))
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, 'Time needed:', border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, r['time'], ln=True)
        pdf.ln(3)

    pdf.set_text_color(170, 170, 170)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(0, 5, 'Generated by SkillSight - AI-Driven Skill Obsolescence Predictor', align='C', ln=True)
    pdf_bytes = pdf.output()
    response = make_response(bytes(pdf_bytes))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=SkillSight_Report.pdf'
    return response


@bp.route('/resume')
@login_required
def resume():
    return render_template('resume.html', user_name=session.get('user_name', ''))


@bp.route('/history')
@login_required
def history():
    conn = get_connection()
    cursor = conn.cursor()
    user_id = session.get('user_id')
    cursor.execute(
        'SELECT id, filename, analysis_json, created_at FROM resume_history WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    history_items = []
    for row in rows:
        analysis = json.loads(row['analysis_json'])
        history_items.append({
            'id': row['id'],
            'filename': row['filename'],
            'created_at': row['created_at'],
            'avg_score': analysis.get('avg_score', 0),
            'overall_risk': analysis.get('overall_risk', 'Unknown'),
            'detected_count': len(analysis.get('detected_skills', []))
        })

    return render_template('history.html', user_name=session.get('user_name', ''), history=history_items)


@bp.route('/api/resume/upload', methods=['POST'])
def api_resume_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    filename = file.filename.lower()
    text = ''
    try:
        if filename.endswith('.pdf'):
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        elif filename.endswith('.docx'):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + '\n'
        elif filename.endswith('.txt'):
            text = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({'error': 'Unsupported file type. Please upload PDF, DOCX, or TXT.'}), 400
    except Exception as e:
        return jsonify({'error': f'Could not read file: {str(e)}'}), 400
    if not text.strip():
        return jsonify({'error': 'Could not extract any text from this file. It may be a scanned/image-based document.'}), 400
    return jsonify({'text': text})


@bp.route('/api/resume', methods=['POST'])
def api_resume():
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    text_lower = text.lower()
    ALL_SKILLS = list(LEARNING_RESOURCES.keys())
    conn = get_connection()
    cursor = conn.cursor()
    detected_skills = []
    detected_names = []

    for skill in ALL_SKILLS:
        escaped = re.escape(skill.lower())
        pattern = r'(?<![a-z0-9])' + escaped + r'(?![a-z0-9])'
        if re.search(pattern, text_lower):
            cursor.execute('SELECT * FROM skill_forecasts WHERE LOWER(skill) = LOWER(?)', (skill,))
            row = cursor.fetchone()
            if row:
                detected_skills.append({
                    'skill': row['skill'],
                    'score': row['obsolescence_score'],
                    'category': row['category'],
                    'slope': row['slope']
                })
                detected_names.append(skill.lower())

    rising_count = sum(1 for s in detected_skills if s['category'] == 'Rising')
    critical_count = sum(1 for s in detected_skills if s['category'] == 'Critical')
    avg_score = round(sum(s['score'] for s in detected_skills) / len(detected_skills), 1) if detected_skills else 0
    overall_risk = 'High' if avg_score > 60 else ('Medium' if avg_score > 40 else 'Low')

    cursor.execute('SELECT * FROM skill_forecasts WHERE category = ? ORDER BY obsolescence_score ASC LIMIT 15', ('Rising',))
    rising_skills = cursor.fetchall()
    missing_skills = []
    for r in rising_skills:
        if r['skill'].lower() not in detected_names:
            res = LEARNING_RESOURCES.get(r['skill'], DEFAULT_RESOURCE)
            missing_skills.append({'skill': r['skill'], 'score': r['obsolescence_score'], 'why': res['why']})
    missing_skills = missing_skills[:6]

    career_roles = []
    for role_name, role_data in CAREER_ROLES.items():
        required = role_data['required']
        matched = [s for s in required if s.lower() in detected_names]
        missing = [s for s in required if s.lower() not in detected_names]
        match_pct = round((len(matched) / len(required)) * 100)
        career_roles.append({
            'role': role_name,
            'description': role_data['description'],
            'match': match_pct,
            'required_skills': required,
            'matched': matched,
            'missing': missing[:4],
            'salary': role_data['salary']
        })

    career_roles.sort(key=lambda x: x['match'], reverse=True)
    career_roles = career_roles[:5]

    has_ml = any(s in detected_names for s in ['machine learning', 'deep learning', 'tensorflow', 'pytorch'])
    has_devops = any(s in detected_names for s in ['docker', 'kubernetes', 'aws', 'terraform'])

    if has_ml:
        roadmap = ROADMAP_TEMPLATES['data_science']
    elif has_devops:
        roadmap = ROADMAP_TEMPLATES['devops']
    else:
        roadmap = ROADMAP_TEMPLATES['general']

    result = {
        'detected_skills': detected_skills,
        'missing_skills': missing_skills,
        'career_roles': career_roles,
        'roadmap': roadmap,
        'avg_score': avg_score,
        'overall_risk': overall_risk
    }

    user_id = session.get('user_id')
    if user_id:
        cursor.execute(
            'INSERT INTO resume_history (user_id, filename, resume_text, analysis_json) VALUES (?, ?, ?, ?)',
            (user_id, 'Resume Analysis', text[:5000], json.dumps(result))
        )
        conn.commit()

    conn.close()
    return jsonify({
        'detected_skills': detected_skills,
        'detected_count': len(detected_skills),
        'rising_count': rising_count,
        'critical_count': critical_count,
        'avg_score': avg_score,
        'overall_risk': overall_risk,
        'missing_skills': missing_skills,
        'career_roles': career_roles,
        'roadmap': roadmap
    })


@bp.route('/trends')
@login_required
def trends():
    return render_template('trends.html', trends=JOB_TRENDS,
                           user_name=session.get('user_name', ''))