from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.ai import ChatRequest, ChatResponse, AIInsightOut
from app.services.ai_service import chat, generate_insights, check_ai_health
from app.models.ai_insight import AIInsight
from app.config import settings

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.get("/health", summary="Test AI provider connectivity (no key exposed)")
def ai_health(_=Depends(get_current_user)):
    """
    Probe the configured AI provider.
    Returns: status, provider name, model name, message.
    The API key is NEVER included in the response.
    """
    return check_ai_health()


@router.post("/chat", response_model=ChatResponse, summary="Chat with AI assistant")
def ai_chat(data: ChatRequest, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return chat(db, data.message)


@router.get("/insights", response_model=list[AIInsightOut], summary="Get latest AI insights")
def get_insights(db: Session = Depends(get_db), _=Depends(get_current_user)):
    insights = db.query(AIInsight).order_by(AIInsight.generated_at.desc()).limit(10).all()
    if not insights:
        insights = generate_insights(db)
    return insights


@router.post("/generate-insights", response_model=list[AIInsightOut],
             summary="Force regenerate AI insights")
def regen_insights(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return generate_insights(db)
