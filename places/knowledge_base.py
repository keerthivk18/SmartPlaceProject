
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


knowledge = [
    {
        "question": "How can I plan a trip?",
        "answer": "Open the Route Planner, enter your starting location and destination, add stops if needed, and calculate your route."
    },
    {
        "question": "How do I save my trip?",
        "answer": "Calculate your route in the Route Planner and click Save Trip to save it to your account."
    },
    {
        "question": "Where can I see my saved trips?",
        "answer": "Open your profile menu and select My Trip History to view your saved trips."
    },
    {
        "question": "How can I find a place?",
        "answer": "Use the search bar on the homepage to search for a place or destination."
    },
    {
        "question": "How do I get directions?",
        "answer": "Open the Route Planner, enter your starting point and destination, and calculate your route."
    },
    {
        "question": "How can I check the weather?",
        "answer": "Open the weather section or the relevant place details to view available weather information."
    },
    {
        "question": "How can I find parking?",
        "answer": "Check the parking information available for your selected destination. Availability depends on the data provided."
    },
    {
        "question": "How can I check crowd status?",
        "answer": "Check the crowd information available for your selected place. Live status depends on the data provided."
    },
    {
        "question": "How can I check waiting time?",
        "answer": "Look for estimated waiting-time information in the selected place's details, if available."
    },
    {
        "question": "How do I register?",
        "answer": "Open the Register page and enter the required details to create your SmartPlace account."
    },
    {
        "question": "How do I log in?",
        "answer": "Open the Login page and enter your account credentials."
    },
    {
        "question": "What is SmartPlace?",
        "answer": "SmartPlace helps users explore places, plan trips, check available place information, and access travel-related details in one application."
    },
    {
        "question": "What can you do?",
        "answer": "I can help with trip planning, saved trips, routes, place search, weather, parking, and other SmartPlace features."
    },
    {
        "question": "What is the best time to visit a place?",
        "answer": "Check the place's available visiting information and crowd details to help plan your visit. Actual conditions may vary."
    },
    {
        "question": "Thank you",
        "answer": "You're welcome! 😊 I'm here to help you with SmartPlace."
    },
    
    {
        "question": "What should I carry when visiting a temple?",
        "answer": "When visiting a temple, you may want to carry a small bag for essentials, a water bottle if permitted, and any required identification or booking confirmation. Check the temple's dress code and rules about bags, footwear, and permitted items before your visit."
    },
]


questions = [item["question"] for item in knowledge]

vectorizer = TfidfVectorizer()
question_vectors = vectorizer.fit_transform(questions)


def find_answer(user_question):
    user_vector = vectorizer.transform([user_question])
    scores = cosine_similarity(user_vector, question_vectors)[0]

    best_match_index = scores.argmax()
    best_score = scores[best_match_index]

    if best_score < 0.20:
        return (
            "I'm not sure about that yet. Try asking about trip planning, "
            "saved trips, routes, weather, parking, or place information."
        )

    return knowledge[best_match_index]["answer"]