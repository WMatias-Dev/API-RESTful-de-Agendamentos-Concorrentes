from fastapi import FastAPI

app = FastAPI(
    title="API de Agendamentos Concorrentes",
    description="API RESTful para agendamentos com controle de concorrência",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
