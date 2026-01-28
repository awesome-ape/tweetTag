from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from .db.database import connect_to_mongo, close_mongo_connection 
from .controller.auth_controller import router as auth_router
from app.controller.tweets_controller.tagger import router as tweets_router  
from app.controller.tweets_controller.elscalation_controller import router as escalation_router
from app.controller.tweets_controller.display_controller import router as display_router
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import working_collection, escalation_collection
from app.services.tweets.tagger import release_stale_locks
import asyncio
from asyncio import create_task


load_dotenv()
@asynccontextmanager
async def lifespan(app: FastAPI):
   try:
    await connect_to_mongo()
    print("MongoDB connected successfully.")
    cleanup_task = asyncio.create_task(release_stale_locks(working_collection))
    cleanup_task = asyncio.create_task(release_stale_locks(escalation_collection))
   except Exception as e:
     print(f"Error connecting to MongoDB: {e}")
     raise e
   finally:
     yield
     await close_mongo_connection()
     print("MongoDB connection closed.")
    
# the server object
app = FastAPI(
    title="Tweet Tag",
    description="a server that tags tweets based on their content",
    lifespan=lifespan
    )   

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, this allows any frontend to connect
    allow_methods=["*"],
    allow_headers=["*"],
)
#############################
# route linking down here #
#############################
# app/controllers/auth_controller.py
app.include_router(auth_router)
app.include_router(tweets_router, tags=["tweets"])
app.include_router(escalation_router, tags=["escalation"])
app.include_router(display_router, tags=["display"])

