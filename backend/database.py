import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATA_DIR: veritabanının ve yüklenen dosyaların yaşadığı dizin. Yerelde "." (bu
# klasör), Railway gibi platformlarda kalıcı bir Volume'un mount edildiği yola
# (örn. /data) ayarlanır — aksi halde her redeploy'da veriler kaybolur.
DATA_DIR = os.getenv("DATA_DIR", ".")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR}/biopages.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
