from pydantic import BaseModel, Field

class TelegramAuthIn(BaseModel):
    init_data: str = Field(min_length=20)

class AuctionCreateIn(BaseModel):
    item_id: int = Field(gt=0)
    price: int = Field(gt=0, le=10_000_000_000)

class AuctionOut(BaseModel):
    id: int
    seller_id: int
    item_id: int
    price: int
    status: str
    title: str
    rarity: str
