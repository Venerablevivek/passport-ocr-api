from fastapi import (
    FastAPI,
    UploadFile,
    File
)

import shutil
import os

from passport_ocr import (
    ocr_passport
)

app = FastAPI(
    title="Passport OCR API"
)

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


@app.get("/")

def home():

    return {
        "success": True,
        "message":
            "Passport OCR API Running"
    }


@app.post("/passport-ocr")

async def passport_ocr_api(

    passport: UploadFile = File(...)
):

    path = os.path.join(

        UPLOAD_DIR,

        passport.filename
    )

    with open(

        path,

        "wb"

    ) as buffer:

        shutil.copyfileobj(

            passport.file,

            buffer
        )

    try:

        details = ocr_passport(
            path
        )

        return {

            "success": True,

            "details": details
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }

    finally:

        if os.path.exists(path):

            os.remove(path)