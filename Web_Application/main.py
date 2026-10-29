from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
from pathlib import Path
import base64

app = FastAPI()

@app.get("/", response_class=FileResponse)
def home():
    return "index.html"

@app.get("/api/data")
def get_data():
    return {
        "status": "success",
        "message": "This is a JSON response",
        "data": [1, 2, 3]
    }

@app.get("/api/images")
def get_images():
    sample_images = Path('sample_images/')
    extension = '*.jpg'

    image_files = [file for file in sample_images.glob(extension) if file.is_file()]

    dict_package = {}
    for file in image_files:
        with open(file, "rb") as opened_file:
            dict_package[file.name] = f"data:image/jpeg;base64,{base64.b64encode(opened_file.read()).decode('utf-8')}"

    return dict_package

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

