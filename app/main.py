from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Teacher Performance Dashboard API",
        version="0.1.0",
        description="Analyse classroom video recordings — transcription and voice fluctuation scoring.",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(analyze_router)

    return application


app = create_app()
