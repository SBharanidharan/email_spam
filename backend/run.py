import uvicorn
import os

if __name__ == "__main__":
    # Start the server on port 8000
    print("Starting FastAPI Backend Server on http://127.0.0.1:8000")
    print("Swagger docs available at http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
