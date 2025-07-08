from fastapi import FastAPI, APIRouter, HTTPException, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import qrcode
import io
import base64
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="La Ferme des Mini-Pousses API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models for the farm zones
class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "quiz", "true_false", "audio_riddle", "image_riddle", "observation"
    question: str
    options: List[str] = []
    correct_answer: str
    explanation: str = ""
    
class Zone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image_base64: str = ""
    video_url: str = ""
    audio_base64: str = ""
    cta_text: str = "Découvrir"
    cta_url: str = ""
    game: Optional[Game] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class ZoneCreate(BaseModel):
    name: str
    description: str
    image_base64: str = ""
    video_url: str = ""
    audio_base64: str = ""
    cta_text: str = "Découvrir"
    cta_url: str = ""
    game: Optional[Game] = None

class VisitorSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    visited_zones: List[str] = []
    total_zones: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class GameResponse(BaseModel):
    zone_id: str
    selected_answer: str
    is_correct: bool
    explanation: str

# Helper function to generate QR code
def generate_qr_code(zone_id: str) -> str:
    """Generate QR code for a zone"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    # In production, this would be your actual domain
    qr_url = f"https://ferme-mini-pousses.com/zone/{zone_id}"
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Zone endpoints
@api_router.get("/zones", response_model=List[Zone])
async def get_zones():
    """Get all farm zones"""
    zones = await db.zones.find().to_list(1000)
    return [Zone(**zone) for zone in zones]

@api_router.post("/zones", response_model=Zone)
async def create_zone(zone_data: ZoneCreate):
    """Create a new farm zone"""
    zone_dict = zone_data.dict()
    zone_obj = Zone(**zone_dict)
    result = await db.zones.insert_one(zone_obj.dict())
    return zone_obj

@api_router.get("/zones/{zone_id}", response_model=Zone)
async def get_zone(zone_id: str):
    """Get a specific zone by ID"""
    zone = await db.zones.find_one({"id": zone_id})
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return Zone(**zone)

@api_router.put("/zones/{zone_id}", response_model=Zone)
async def update_zone(zone_id: str, zone_data: ZoneCreate):
    """Update a zone"""
    zone_dict = zone_data.dict()
    zone_dict["updated_at"] = datetime.utcnow()
    
    result = await db.zones.update_one(
        {"id": zone_id},
        {"$set": zone_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    updated_zone = await db.zones.find_one({"id": zone_id})
    return Zone(**updated_zone)

@api_router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: str):
    """Delete a zone"""
    result = await db.zones.delete_one({"id": zone_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone deleted successfully"}

# QR Code endpoint
@api_router.get("/zones/{zone_id}/qr")
async def get_zone_qr_code(zone_id: str):
    """Generate QR code for a zone"""
    zone = await db.zones.find_one({"id": zone_id})
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    qr_base64 = generate_qr_code(zone_id)
    return {"qr_code": qr_base64, "zone_name": zone["name"]}

# Game endpoints
@api_router.post("/zones/{zone_id}/game/answer", response_model=GameResponse)
async def answer_game(zone_id: str, selected_answer: str = Form(...)):
    """Submit an answer to a zone's game"""
    zone = await db.zones.find_one({"id": zone_id})
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    if not zone.get("game"):
        raise HTTPException(status_code=404, detail="No game found for this zone")
    
    game = zone["game"]
    is_correct = selected_answer == game["correct_answer"]
    
    return GameResponse(
        zone_id=zone_id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        explanation=game.get("explanation", "")
    )

# Visitor session endpoints
@api_router.post("/session", response_model=VisitorSession)
async def create_session():
    """Create a new visitor session"""
    total_zones = await db.zones.count_documents({})
    session = VisitorSession(total_zones=total_zones)
    await db.sessions.insert_one(session.dict())
    return session

@api_router.get("/session/{session_id}", response_model=VisitorSession)
async def get_session(session_id: str):
    """Get visitor session"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return VisitorSession(**session)

@api_router.post("/session/{session_id}/visit/{zone_id}")
async def mark_zone_visited(session_id: str, zone_id: str):
    """Mark a zone as visited in the session"""
    session = await db.sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    visited_zones = session.get("visited_zones", [])
    if zone_id not in visited_zones:
        visited_zones.append(zone_id)
        
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "visited_zones": visited_zones,
                    "last_activity": datetime.utcnow()
                }
            }
        )
    
    return {"message": "Zone marked as visited", "visited_count": len(visited_zones)}

# Initialize with sample data
@api_router.post("/init-sample-data")
async def initialize_sample_data():
    """Initialize with sample farm zones"""
    # Check if data already exists
    existing_count = await db.zones.count_documents({})
    if existing_count > 0:
        return {"message": "Sample data already exists"}
    
    sample_zones = [
        {
            "id": str(uuid.uuid4()),
            "name": "Poulailler",
            "description": "Découvrez nos poules et coqs colorés ! Apprenez comment ils vivent, ce qu'ils mangent et comment ils nous donnent des œufs frais chaque jour.",
            "image_base64": "",
            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "audio_base64": "",
            "cta_text": "Nourrir les poules",
            "cta_url": "#",
            "game": {
                "id": str(uuid.uuid4()),
                "type": "quiz",
                "question": "Combien d'œufs une poule peut-elle pondr par jour ?",
                "options": ["1 œuf", "5 œufs", "10 œufs"],
                "correct_answer": "1 œuf",
                "explanation": "Une poule pond généralement un œuf par jour, parfois un peu moins."
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Wallaby",
            "description": "Rencontrez notre wallaby ! Ces petits marsupiaux ressemblent à des kangourous miniatures. Observez comment ils sautent et découvrez leurs habitudes.",
            "image_base64": "",
            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "audio_base64": "",
            "cta_text": "Observer le wallaby",
            "cta_url": "#",
            "game": {
                "id": str(uuid.uuid4()),
                "type": "quiz",
                "question": "Quel est le cri du wallaby ?",
                "options": ["Meuglement", "Couinement", "Coin-coin"],
                "correct_answer": "Couinement",
                "explanation": "Le wallaby fait un petit couinement, un son très doux et discret."
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Rosie la vache avec Yukie le poulain",
            "description": "Venez dire bonjour à Rosie, notre vache gentille, et à Yukie, son petit poulain. Apprenez comment ils vivent ensemble et ce qu'ils aiment manger.",
            "image_base64": "",
            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "audio_base64": "",
            "cta_text": "Caresser Rosie",
            "cta_url": "#",
            "game": {
                "id": str(uuid.uuid4()),
                "type": "true_false",
                "question": "Les vaches mangent seulement de l'herbe ?",
                "options": ["Vrai", "Faux"],
                "correct_answer": "Faux",
                "explanation": "Les vaches mangent principalement de l'herbe, mais aussi du foin, des légumes et des céréales."
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    await db.zones.insert_many(sample_zones)
    return {"message": "Sample data initialized successfully", "zones_created": len(sample_zones)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()