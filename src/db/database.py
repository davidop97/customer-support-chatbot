from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os
from datetime import datetime

# Cargar URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")


# Configuración del motor y la sesión
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    identificacion = Column(String(11), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(10), nullable=True)
    email = Column(String(255), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

def init_db():
    """
    Crea las tablas en la base de datos.
    Ejecutar al inicio de la aplicación o vía script.
    """
    Base.metadata.create_all(bind=engine)
def get_db() -> Generator[Session, None, None]:
    """
    Dependencia para obtener una sesión de DB.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.close()

# Operaciones CRUD básicas

def get_cliente_por_identificacion(db: Session, identificacion: str):
    return db.query(Cliente).filter(Cliente.identificacion == identificacion).first()

def create_cliente(db: Session, identificacion: str, nombre: str, telefono: str, email: str) -> Cliente:
    cliente = Cliente(
        identificacion=identificacion,
        nombre=nombre,
        telefono=telefono,
        email=email
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

# Ejemplo de uso en script
if __name__ == "__main__":
    # Inicializar base de datos
    init_db()
    print(" Tablas creadas en la base de datos.")
