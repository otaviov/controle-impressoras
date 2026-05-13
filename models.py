from __future__ import annotations
from datetime import datetime
import random
import string
from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Printer(Base):
    __tablename__ = "printers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patrimonio: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    serial: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="Operacional")
    local_atual: Mapped[str] = mapped_column(String(120), default="")
    
    # NOVOS CAMPOS
    marca: Mapped[str] = mapped_column(String(80), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="")
    ip_rede: Mapped[str] = mapped_column(String(15), default="")
    mac_address: Mapped[str] = mapped_column(String(17), default="")
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=True)
    proxima_revisao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    tecnico: Mapped[str] = mapped_column(String(120), default="")
    
    pecas_faltantes: Mapped[str] = mapped_column(Text, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    
    # NOVOS CAMPOS
    from_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    to_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    numero_recibo: Mapped[str] = mapped_column(String(50), default="")
    tecnico_id: Mapped[int] = mapped_column(Integer, nullable=True)
    custo_servico: Mapped[float] = mapped_column(Float, default=0.0)
    status_atividade: Mapped[str] = mapped_column(String(30), default="concluida")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(Text, default="")
    parts_used: Mapped[str] = mapped_column(Text, default="")
    from_location: Mapped[str] = mapped_column(String(120), default="")
    to_location: Mapped[str] = mapped_column(String(120), default="")

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), default="")
    endereco: Mapped[str] = mapped_column(String(255), default="")
    cidade: Mapped[str] = mapped_column(String(100), default="")
    uf: Mapped[str] = mapped_column(String(2), default="")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="cliente")
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    printer_id: Mapped[str] = mapped_column(String(36), default="")
    numero_os: Mapped[str] = mapped_column(String(50), default="")
    tipo: Mapped[str] = mapped_column(String(20), default="saida")
    from_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    to_company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    responsavel_entrega: Mapped[str] = mapped_column(String(120), default="")
    responsavel_recebimento: Mapped[str] = mapped_column(String(120), default="")
    data_saida: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_retorno_prev: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_retorno_real: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    observacao: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), default="")
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, default="")
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    preco_unitario: Mapped[float] = mapped_column(Float, default=0.0)
    modelo_compativel: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), default="")
    entity_id: Mapped[int] = mapped_column(Integer, default=0)
    filename: Mapped[str] = mapped_column(String(255), default="")
    original_name: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    mime_type: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    categoria: Mapped[str] = mapped_column(String(50), default="recibo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    uploader_id: Mapped[int] = mapped_column(Integer, nullable=True)

class Technician(Base):
    __tablename__ = "technicians"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String(80), default="")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def simple_uid() -> str:
    chars = string.ascii_lowercase + string.digits
    parts = [8, 4, 4, 4, 12]
    return "-".join("".join(random.choice(chars) for _ in range(n)) for n in parts)


