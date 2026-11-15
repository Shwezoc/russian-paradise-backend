from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(128), default="Игрок")
    balance: Mapped[int] = mapped_column(BigInteger, default=250000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    inventory: Mapped[list["InventoryItem"]] = relationship(back_populates="owner")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    item_type: Mapped[str] = mapped_column(String(24))
    code: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    rarity: Mapped[str] = mapped_column(String(24), default="Обычный")
    estimated_value: Mapped[int] = mapped_column(BigInteger, default=0)
    locked_in_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    owner: Mapped[User] = relationship(back_populates="inventory")

class AuctionLot(Base):
    __tablename__ = "auction_lots"
    __table_args__ = (CheckConstraint("price > 0"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), unique=True)
    price: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(64))
    reference: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
