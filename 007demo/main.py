from fastapi import FastAPI
from app.api.routes import router, get_service
import uvicorn
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Manus Agent 007 Service")

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    service = get_service()
    await service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    service = get_service()
    await service.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
