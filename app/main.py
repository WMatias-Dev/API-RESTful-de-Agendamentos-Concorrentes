from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes.auth import router as auth_router
from app.exceptions import AppException

app = FastAPI(
    title="API de Agendamentos Concorrentes",
    description="API RESTful para agendamentos com controle de concorrência",
    version="0.1.0",
)


# Handler global para converter nossas exceções de negócio em respostas JSON
@app.exception_handler(AppException)
def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Registro de rotas
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
