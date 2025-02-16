from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dundie.routes import main_router

app = FastAPI(
    title="dundie",
    version="0.1.1",
    description="dundie is a rewards API",
)

app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://localhost",
        "https://server.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
