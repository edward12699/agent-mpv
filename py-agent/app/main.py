from fastapi import FastAPI
from .routes import router


app = FastAPI(
    title="Contract Agent API",
    description="AI 合同分析服务",
)

app.include_router(
    router,
    prefix="/api"
)

@app.get("/")
def root():
    return {
        "message": "Contract Agent API running"
    }
