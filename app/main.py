from fastapi import FastAPI, HTTPException
import requests, os

RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
app = FastAPI(title="Hybrid Gemini Assistant")

@app.get("/")
def root():
    return {
        "message": "Hybrid Gemini Assistant API",
        "endpoints": {
            "/chat": "POST - Send a message to the assistant",
            "/health": "GET - Check API health status",
            "/docs": "GET - API documentation"
        },
        "usage": "POST to /chat with JSON body: {\"message\": \"your message here\"}"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        # Check if Rasa server is running
        rasa_health = requests.get("http://localhost:5005/", timeout=2)
        rasa_status = "connected" if rasa_health.status_code < 500 else "disconnected"
    except:
        rasa_status = "disconnected"
    
    return {
        "status": "healthy",
        "rasa_server": rasa_status,
        "rasa_url": RASA_URL
    }

@app.post("/chat")
def chat(user_msg: dict):
    """Send a message to the Rasa assistant"""
    if not user_msg.get("message"):
        raise HTTPException(status_code=400, detail="Missing 'message' field in request body")
    
    try:
        res = requests.post(RASA_URL, json={"sender": "user", "message": user_msg.get("message", "")}, timeout=10)
        res.raise_for_status()
        return {"reply": res.json()}
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Rasa server. Make sure Rasa is running on port 5005.")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request to Rasa server timed out.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Rasa server: {str(e)}")
