from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models import Meeting
from app.routers import meetings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure all database tables exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Reset any stale/orphaned tasks left from a previous crash or Ctrl+C
    db = SessionLocal()
    try:
        stale_count = db.query(Meeting).filter(
            Meeting.status.in_(["pending", "transcribing", "summarizing"])
        ).update(
            {"status": "failed", "error_message": "Process interrupted by server restart"},
            synchronize_session=False
        )
        db.commit()
        if stale_count > 0:
            print(f"[STARTUP] Reset {stale_count} interrupted meeting job(s) to 'failed'.")
    except Exception as e:
        print(f"[STARTUP] Error resetting stale meeting states: {e}")
    finally:
        db.close()
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "whisper_device": settings.WHISPER_DEVICE
    }