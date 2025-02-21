from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List
from models import Review  # Import the Review model

class Settings(BaseSettings):
    PORT: int
    DATABASE_URL: str

    model_config = ConfigDict(env_file='.env')
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        cred = credentials.Certificate('credentials.json')
        firebase_app = firebase_admin.initialize_app(cred, {
            'databaseURL': settings.DATABASE_URL
        })
        db = firestore.client(app=firebase_app, database_id="reviews")
        reviews_ref = db.collection("reviews")
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")

    app.state.reviews_ref = reviews_ref
    yield

    # --- Shutdown ---
    try:
        if db:
            print("Closing Firestore client...")
            db.close()
            print("Firestore client closed.")
        if firebase_app:
            firebase_admin.delete_app(firebase_app)
            print("Firebase Admin SDK app deleted successfully.")
    except Exception as e:
        print(f"Error deleting Firebase Admin SDK app: {e}")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/", response_model=List[Review])
async def get_reviews():
    reviews_ref = app.state.reviews_ref
    docs = reviews_ref.stream()
    reviews = []
    for doc in docs:
        data = doc.to_dict()
        try:
            review_obj = Review.model_validate(data)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Error parsing review: {exc}")
        reviews.append(review_obj)
    return reviews

@app.post("/", response_model=Review)
async def create_review(review: Review):
    review_data = review.model_dump(by_alias=True)
    reviews_ref = app.state.reviews_ref
    review_ref = reviews_ref.document(review.reviewId)
    # Check if the review already exists
    existing = review_ref.get()
    if existing.exists:
        raise HTTPException(status_code=400, detail="Review already exists")
    try:
        review_ref.set(review_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating review document: {exc}")
    return review

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)