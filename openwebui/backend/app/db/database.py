"""
Database models and connection - PostgreSQL with asyncpg
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey, Index
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


def get_database_url() -> str:
    """Get database URL from settings or environment"""
    # Use DATABASE_URL if explicitly set
    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    # Default PostgreSQL connection
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/nexusai"


# Create async engine with connection pooling
DATABASE_URL = get_database_url()

# Configure engine based on environment
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}

if settings.DEBUG:
    # Debug mode: use NullPool for simpler debugging
    engine_kwargs["poolclass"] = NullPool
else:
    # Production: use connection pooling
    engine_kwargs["poolclass"] = AsyncAdaptedQueuePool
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def create_tables():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# ==================== MODELS ====================


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    api_key = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    provider_configs = relationship("ProviderConfig", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('ix_users_is_active', 'is_active'),
        Index('ix_users_created_at', 'created_at'),
    )


class ProviderConfig(Base):
    """AI Provider configuration"""
    __tablename__ = "provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)
    name = Column(String(100))
    api_key = Column(String(500))
    base_url = Column(String(500))
    default_model = Column(String(100))
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="provider_configs")

    # Indexes
    __table_args__ = (
        Index('ix_provider_configs_user_provider', 'user_id', 'provider'),
        Index('ix_provider_configs_is_default', 'user_id', 'is_default'),
    )


class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    provider = Column(String(50))
    model = Column(String(100))
    context_files = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('ix_chat_sessions_user_updated', 'user_id', 'updated_at'),
        Index('ix_chat_sessions_created_at', 'created_at'),
    )


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(100))
    tokens_used = Column(Integer)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('ix_chat_messages_session_created', 'session_id', 'created_at'),
        Index('ix_chat_messages_created_at', 'created_at'),
    )


class FileIndex(Base):
    """Indexed files for RAG"""
    __tablename__ = "file_indices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))
    content = Column(Text)
    embedding = Column(JSON)
    tokens_count = Column(Integer)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('ix_file_indices_user_id', 'user_id'),
        Index('ix_file_indices_file_type', 'file_type'),
        Index('ix_file_indices_indexed_at', 'indexed_at'),
    )


class CodeExecution(Base):
    """Code execution results"""
    __tablename__ = "code_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    output = Column(Text)
    error = Column(Text)
    execution_time = Column(Float)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('ix_code_executions_user_id', 'user_id'),
        Index('ix_code_executions_status', 'status'),
        Index('ix_code_executions_created_at', 'created_at'),
    )


# Import text for connection check
from sqlalchemy import text
