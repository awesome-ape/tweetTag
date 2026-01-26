from fastapi import APIRouter, FastAPI
from contextlib import asynccontextmanager
from .db.database import connect_to_mongo, close_mongo_connection 
from .controller.auth_controller import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
   try:
    await connect_to_mongo()
    print("MongoDB connected successfully.")
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


#############################
# route linking down here #
#############################
# app/controllers/auth_controller.py
app.include_router(auth_router)

