from pydantic import BaseModel, Field
from datetime import datetime

class Review(BaseModel):
    reviewId: str = Field(..., alias="review_id")
    rideId: str = Field(..., alias="ride_id")
    reviewerId: str = Field(..., alias="reviewer_id")
    revieweeId: str = Field(..., alias="reviewee_id")
    rating: int
    comment: str | None = None
    createdAt: datetime = Field(..., alias="created_at")