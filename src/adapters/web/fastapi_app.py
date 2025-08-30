from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from ..application.service import QRCodeService
from ..infrastructure.factory import default_encoders
from ..domain.models import QRCodeSpec

app = FastAPI(title="Text to QR API")
svc = QRCodeService(encoders=default_encoders())

class GenerateRequest(BaseModel):
    data: str = Field(..., min_length=1)
    fmt: str = Field("png", pattern="^(png|svg)$")
    error: str = Field("M", pattern="^[LMQH]$")
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    background: str = Field("white", pattern="^(white|transparent)$")

@app.post("/generate")
def generate(payload: GenerateRequest):
    spec = QRCodeSpec(
        data=payload.data,
        error=payload.error, box_size=payload.box_size, border=payload.border,
        fill_color=payload.fill_color, background=payload.background, fmt=payload.fmt
    )
    data = svc.generate_bytes(spec)
    media = "image/png" if payload.fmt == "png" else "image/svg+xml"
    return Response(content=data, media_type=media)
