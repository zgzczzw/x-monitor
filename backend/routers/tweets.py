import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from database import get_db
from models import Tweet

router = APIRouter()


@router.get("")
def list_tweets(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    author: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Tweet)
    if author:
        query = query.filter(Tweet.author.ilike(f"%{author}%"))

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    items = query.order_by(desc(Tweet.tweeted_at)).offset((page - 1) * size).limit(size).all()

    return {
        "items": [
            {
                "id": t.id,
                "author": t.author,
                "content": t.content,
                "content_zh": t.content_zh,
                "url": t.url,
                "source_id": t.source_id,
                "tweeted_at": t.tweeted_at.isoformat() if t.tweeted_at else None,
                "saved_at": t.saved_at.isoformat() if t.saved_at else None,
            }
            for t in items
        ],
        "total": total,
        "page": page,
        "pages": pages,
    }
