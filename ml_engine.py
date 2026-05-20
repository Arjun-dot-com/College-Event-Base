import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
import models

def get_personalized_events(user_id: int, db: Session, top_n: int = 3):
    # 1. Fetch the user and their past registrations
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return []

    past_regs = db.query(models.Registration).filter(models.Registration.user_id == user_id).all()
    registered_event_ids = [reg.event_id for reg in past_regs]

    # 2. Fetch all events and their categories
    all_events = db.query(models.Event).all()
    if not all_events:
        return []

    events_data = []
    for event in all_events:
        category = db.query(models.Category).filter(models.Category.id == event.category_id).first()
        cat_name = category.name if category else ""
        
        # Combine text fields to create a rich 'content' string for the ML model
        content = f"{event.title} {event.description} {cat_name}"
        events_data.append({
            "id": event.id,
            "content": content,
            "is_registered": event.id in registered_event_ids,
            "original_event": event
        })
        
    df = pd.DataFrame(events_data)

    # 3. Build the "User Profile Vector"
    # We combine their branch, year, and the content of events they already attended
    past_event_content = " ".join(df[df['is_registered'] == True]['content'].tolist())
    
    # If they have no history, the system relies entirely on their branch and year
    user_profile_text = f"{user.branch} {user.year} {past_event_content}"

    # 4. Vectorize and Calculate Similarity
    tfidf = TfidfVectorizer(stop_words='english')
    
    # We fit the model on the user profile PLUS all event content to build the vocabulary
    all_text = [user_profile_text] + df['content'].tolist()
    tfidf_matrix = tfidf.fit_transform(all_text)
    
    # Calculate cosine similarity between the User Profile (index 0) and all Events (index 1 onwards)
    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Add the computed scores back to our DataFrame
    df['similarity_score'] = similarity_scores
    
    # 5. Filter and Sort
    # Remove events they are already registered for, sort by highest score
    recommendations_df = df[df['is_registered'] == False].sort_values(by='similarity_score', ascending=False)
    
    # Extract the top N original event objects
    top_events = recommendations_df.head(top_n)['original_event'].tolist()
    
    return top_events