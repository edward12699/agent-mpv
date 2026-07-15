from fastapi import FastAPI
from .routes import router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(
    title="Contract Agent API",
    description="AI 合同分析服务",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api"
)


@app.get("/health",tags=["Health"])
def health() -> dict[str,str]:
    return {
        "status": "ok"
    }

