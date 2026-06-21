
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np


TRAINING_DATA = [
    # Welfare
    ("I will improve student welfare, health services and mental health support", "Welfare"),
    ("My focus is on student wellbeing, counselling and health facilities", "Welfare"),
    ("I will ensure every student has access to proper healthcare and support", "Welfare"),
    ("I will fight for better hostel conditions and student welfare packages", "Welfare"),
    ("My priority is the welfare of students including food, health and accommodation", "Welfare"),
    ("I will create a welfare fund to support students in financial need", "Welfare"),
    ("Better medical facilities and student support systems are my top priority", "Welfare"),

    # Academic
    ("I will improve academic resources, library facilities and lecture materials", "Academic"),
    ("My goal is to enhance the quality of education and academic support", "Academic"),
    ("I will push for better lecturers, course materials and academic calendars", "Academic"),
    ("I will advocate for examination reforms and better academic policies", "Academic"),
    ("My priority is ensuring students have access to quality education and research", "Academic"),
    ("I will work to improve the library, laboratories and academic infrastructure", "Academic"),
    ("I will fight for better grading systems and academic fairness", "Academic"),

    # Financial
    ("I will reduce student levies and ensure transparent financial management", "Financial"),
    ("My goal is to manage student union funds transparently and accountably", "Financial"),
    ("I will ensure proper budgeting and financial accountability in the union", "Financial"),
    ("I will fight for scholarship opportunities and financial aid for students", "Financial"),
    ("My priority is reducing unnecessary fees and managing union funds properly", "Financial"),
    ("I will create financial support systems for indigent students", "Financial"),
    ("Transparent financial reporting and reduced levies are my key goals", "Financial"),

    # Infrastructure
    ("I will improve campus facilities, roads, classrooms and student spaces", "Infrastructure"),
    ("My focus is on fixing classrooms, hostels and campus infrastructure", "Infrastructure"),
    ("I will advocate for better electricity, water and internet on campus", "Infrastructure"),
    ("I will push for renovation of lecture halls and student common rooms", "Infrastructure"),
    ("Better campus facilities and infrastructure development is my priority", "Infrastructure"),
    ("I will ensure the campus environment is conducive for learning", "Infrastructure"),
    ("My goal is to improve sporting facilities and recreational spaces", "Infrastructure"),

    # General
    ("I will represent all students fairly and ensure their voices are heard", "General"),
    ("My goal is to unite students and build a stronger student community", "General"),
    ("I will ensure effective communication between students and management", "General"),
    ("I will be a voice for all students regardless of department or level", "General"),
    ("My priority is student representation and advocacy at all levels", "General"),
    ("I will organize events, programs and activities that benefit all students", "General"),
    ("I will work hard to make this university a better place for everyone", "General"),
]

TEXTS  = [item[0] for item in TRAINING_DATA]
LABELS = [item[1] for item in TRAINING_DATA]

vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
X_train    = vectorizer.fit_transform(TEXTS)

classifier = MultinomialNB()
classifier.fit(X_train, LABELS)



def score_manifesto(text):
    """
    Score manifesto strength based on:
    - Word count
    - Specificity (presence of action words)
    - Length and detail
    """
    words        = text.split()
    word_count   = len(words)

    action_words = [
        'will', 'ensure', 'improve', 'fight', 'advocate', 'push',
        'create', 'build', 'develop', 'establish', 'implement',
        'provide', 'support', 'enhance', 'reduce', 'increase'
    ]

    action_count = sum(1 for w in words if w.lower() in action_words)

    if word_count >= 80 and action_count >= 4:
        return 'Strong'
    elif word_count >= 40 and action_count >= 2:
        return 'Moderate'
    else:
        return 'Weak'



def analyse_manifesto(text):
    """
    Analyse a manifesto and return theme, score and confidence.
    Returns a dict with ai_theme, ai_score, ai_confidence.
    """
    if not text or len(text.strip()) < 10:
        return {
            'ai_theme':      'General',
            'ai_score':      'Weak',
            'ai_confidence': 0.0
        }

    # Vectorize input
    X_input = vectorizer.transform([text])

    # Predict theme
    theme       = classifier.predict(X_input)[0]
    proba       = classifier.predict_proba(X_input)[0]
    confidence  = round(float(np.max(proba)) * 100, 1)

    # Score manifesto
    score = score_manifesto(text)

    return {
        'ai_theme':      theme,
        'ai_score':      score,
        'ai_confidence': confidence
    }