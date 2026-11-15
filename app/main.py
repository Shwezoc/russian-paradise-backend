from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from .config import settings
from .db import Base, engine, get_db
from .models import User, InventoryItem, AuctionLot, LedgerEntry
from .schemas import TelegramAuthIn, AuctionCreateIn
from .auth import verify_telegram_init_data, issue_token, current_user

app = FastAPI(title="RUSSIAN PARADISE API", version="0.1.0")

@app.on_event("startup")
def startup():
    # Convenient for the first local test. Use Alembic migrations in production.
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok", "service": "russian-paradise-api", "version": "0.1.0"}

@app.post("/auth/telegram")
def telegram_auth(body: TelegramAuthIn, db: Session = Depends(get_db)):
    tg = verify_telegram_init_data(body.init_data)
    telegram_id = int(tg["id"])
    user = db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, username=tg.get("username"), first_name=tg.get("first_name") or "Игрок")
        db.add(user)
    else:
        user.username = tg.get("username")
        user.first_name = tg.get("first_name") or user.first_name
    db.commit(); db.refresh(user)
    return {"access_token": issue_token(user), "token_type": "bearer", "user": {"id": user.id, "first_name": user.first_name, "balance": user.balance}}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "first_name": user.first_name, "username": user.username, "balance": user.balance}

@app.get("/inventory")
def inventory(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(InventoryItem).where(InventoryItem.owner_id == user.id)).all()
    return [{"id": x.id, "type": x.item_type, "code": x.code, "title": x.title, "rarity": x.rarity, "estimated_value": x.estimated_value, "locked": x.locked_in_auction} for x in rows]

@app.get("/auctions")
def auctions(db: Session = Depends(get_db)):
    rows = db.execute(select(AuctionLot, InventoryItem).join(InventoryItem, AuctionLot.item_id == InventoryItem.id).where(AuctionLot.status == "active").order_by(AuctionLot.created_at.desc()).limit(100)).all()
    return [{"id": lot.id, "seller_id": lot.seller_id, "item_id": item.id, "title": item.title, "rarity": item.rarity, "price": lot.price, "status": lot.status} for lot, item in rows]

@app.post("/auctions", status_code=201)
def create_auction(body: AuctionCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(InventoryItem).where(InventoryItem.id == body.item_id).with_for_update())
    if not item or item.owner_id != user.id:
        raise HTTPException(404, "Предмет не найден в вашем инвентаре")
    if item.locked_in_auction:
        raise HTTPException(409, "Предмет уже выставлен на аукцион")
    item.locked_in_auction = True
    lot = AuctionLot(seller_id=user.id, item_id=item.id, price=body.price)
    db.add(lot); db.commit(); db.refresh(lot)
    return {"id": lot.id, "item_id": item.id, "title": item.title, "price": lot.price, "status": lot.status}

@app.post("/auctions/{lot_id}/cancel")
def cancel_auction(lot_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lot = db.scalar(select(AuctionLot).where(AuctionLot.id == lot_id).with_for_update())
    if not lot or lot.status != "active":
        raise HTTPException(404, "Активный лот не найден")
    if lot.seller_id != user.id:
        raise HTTPException(403, "Это не ваш лот")
    item = db.get(InventoryItem, lot.item_id)
    lot.status = "cancelled"
    if item: item.locked_in_auction = False
    db.commit()
    return {"status": "cancelled"}
