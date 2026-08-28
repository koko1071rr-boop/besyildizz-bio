import io
import os
import uuid
from pathlib import Path
from typing import List, Optional

import qrcode
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
from database import DATA_DIR, Base, SessionLocal, engine

load_dotenv()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise RuntimeError(
        "ADMIN_TOKEN .env dosyasında tanımlı değil. backend/.env.example dosyasını "
        "backend/.env olarak kopyalayıp bir değer girin."
    )

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5500").split(",")
    if origin.strip()
]

# Bio sayfalarının yayında yaşadığı adres (QR kodların işaret ettiği URL).
# Production'da gerçek domain'inizle değiştirin, örn: https://besyildizz.bio
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "http://localhost:5500").rstrip("/")

UPLOAD_DIR = Path(DATA_DIR) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_UPLOAD_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Yönlendirme Merkezi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_admin_token(x_admin_token: Optional[str] = Header(default=None)):
    if not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Geçersiz veya eksik admin token")


@app.get("/api/bio/{slug}", response_model=schemas.BioPageOut)
def get_bio_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(models.BioPage).filter(models.BioPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")
    return page


@app.get(
    "/api/admin/bio",
    response_model=List[schemas.BioPageOut],
    dependencies=[Depends(verify_admin_token)],
)
def list_bio_pages(db: Session = Depends(get_db)):
    return db.query(models.BioPage).order_by(models.BioPage.created_at.desc()).all()


@app.post(
    "/api/admin/bio",
    response_model=schemas.BioPageOut,
    dependencies=[Depends(verify_admin_token)],
)
def create_bio_page(payload: schemas.BioPageCreate, db: Session = Depends(get_db)):
    existing = db.query(models.BioPage).filter(models.BioPage.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bu slug zaten kullanılıyor")

    page = models.BioPage(
        slug=payload.slug,
        business_name=payload.business_name,
        tagline=payload.tagline,
        logo_url=payload.logo_url,
        theme_color=payload.theme_color,
        links=[link.model_dump() for link in payload.links],
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@app.put(
    "/api/admin/bio/{slug}",
    response_model=schemas.BioPageOut,
    dependencies=[Depends(verify_admin_token)],
)
def update_bio_page(slug: str, payload: schemas.BioPageUpdate, db: Session = Depends(get_db)):
    page = db.query(models.BioPage).filter(models.BioPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")

    page.business_name = payload.business_name
    page.tagline = payload.tagline
    page.logo_url = payload.logo_url
    page.theme_color = payload.theme_color
    page.links = [link.model_dump() for link in payload.links]
    db.commit()
    db.refresh(page)
    return page


@app.delete(
    "/api/admin/bio/{slug}",
    dependencies=[Depends(verify_admin_token)],
)
def delete_bio_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(models.BioPage).filter(models.BioPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")

    db.delete(page)
    db.commit()
    return {"detail": "Silindi"}


@app.get(
    "/api/admin/bio/{slug}/qr",
    dependencies=[Depends(verify_admin_token)],
)
def get_bio_qr(slug: str, db: Session = Depends(get_db)):
    page = db.query(models.BioPage).filter(models.BioPage.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")

    target_url = f"{PUBLIC_SITE_URL}/{slug}"
    img = qrcode.make(target_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.post("/api/admin/upload", dependencies=[Depends(verify_admin_token)])
async def upload_logo(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=400, detail="Sadece PNG, JPEG veya WEBP dosyaları yüklenebilir"
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Dosya boyutu 5MB'ı geçemez")

    filename = f"{uuid.uuid4().hex}{ALLOWED_UPLOAD_TYPES[file.content_type]}"
    (UPLOAD_DIR / filename).write_bytes(contents)

    url = f"{str(request.base_url).rstrip('/')}/uploads/{filename}"
    return {"url": url}
