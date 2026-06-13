from passporteye import read_mrz
from datetime import datetime, date
import cv2
import os
import tempfile


MIN_VALID_SCORE = 70


def preprocess_variants(image):

    variants = []

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    variants.append(gray)

    blurred = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    sharpened = cv2.addWeighted(
        gray,
        2,
        blurred,
        -1,
        0
    )

    variants.append(sharpened)

    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    variants.append(adaptive)

    otsu = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )[1]

    variants.append(otsu)

    return variants


def try_mrz(image):

    variants = preprocess_variants(
        image
    )

    scales = [1, 2, 3]

    best = None
    best_score = -1

    for img in variants:

        for scale in scales:

            try:

                if scale > 1:

                    processed = cv2.resize(
                        img,
                        None,
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_CUBIC
                    )

                else:

                    processed = img

                temp = tempfile.mktemp(
                    suffix=".jpg"
                )

                cv2.imwrite(
                    temp,
                    processed
                )
                print("Trying MRZ...")
                mrz = read_mrz(
                    temp,
                    save_roi=True
                )
                print("MRZ:", mrz)

                if mrz:

                    data = mrz.to_dict()

                    score = data.get(
                        "valid_score",
                        0
                    )

                    print(
                        f"Scale={scale} Score={score}"
                    )

                    if score > best_score:

                        best_score = score
                        best = mrz

            except Exception as e:

                print(
                    "MRZ attempt failed:",
                    e
                )

            finally:

                if (
                    "temp" in locals()
                    and os.path.exists(temp)
                ):

                    os.remove(temp)

    return best


def clean_name(value):

    return (
        value.replace("<", " ")
        .replace("  ", " ")
        .strip()
    )


def convert_dob(dob):

    try:

        d = datetime.strptime(
            dob,
            "%y%m%d"
        )

        if d.date() > date.today():

            d = d.replace(
                year=d.year - 100
            )

        return d.strftime(
            "%d/%m/%Y"
        )

    except:

        return dob


def convert_expiry(expiry):

    try:

        d = datetime.strptime(
            expiry,
            "%y%m%d"
        )

        return d.strftime(
            "%d/%m/%Y"
        )

    except:

        return expiry


def extract_fields(mrz):

    data = mrz.to_dict()

    print("\nMRZ DATA:")
    print(data)

    return {

        "firstName":
            clean_name(
                data.get(
                    "names",
                    ""
                )
            ),

        "lastName":
            clean_name(
                data.get(
                    "surname",
                    ""
                )
            ),

        "passportNumber":
            data.get(
                "number",
                ""
            ).replace(
                "<",
                ""
            ),

        "nationality":
            data.get(
                "nationality"
            ) or data.get(
                "country",
                ""
            ),

        "gender":
            data.get(
                "sex",
                ""
            ),

        "dateOfBirth":
            convert_dob(
                data.get(
                    "date_of_birth",
                    ""
                )
            ),

        "expiryDate":
            convert_expiry(
                data.get(
                    "expiration_date",
                    ""
                )
            ),

        "mrzValidation": {

            "validScore":
                data.get(
                    "valid_score"
                ),

            "validPassportNumber":
                data.get(
                    "valid_number"
                ),

            "validDateOfBirth":
                data.get(
                    "valid_date_of_birth"
                ),

            "validExpiryDate":
                data.get(
                    "valid_expiration_date"
                ),

            "validComposite":
                data.get(
                    "valid_composite"
                )
        }
    }


def ocr_passport(path):

    image = cv2.imread(path)

    if image is None:

        raise Exception(
            "Unable to read image"
        )

    angles = [
        0,
        90,
        180,
        270
    ]

    best = None
    best_score = -1

    for angle in angles:

        rotated = image.copy()

        if angle == 90:

            rotated = cv2.rotate(
                image,
                cv2.ROTATE_90_CLOCKWISE
            )

        elif angle == 180:

            rotated = cv2.rotate(
                image,
                cv2.ROTATE_180
            )

        elif angle == 270:

            rotated = cv2.rotate(
                image,
                cv2.ROTATE_90_COUNTERCLOCKWISE
            )

        mrz = try_mrz(
            rotated
        )

        if mrz:

            score = mrz.to_dict().get(
                "valid_score",
                0
            )

            print(
                f"Rotation={angle} Score={score}"
            )

            if score > best_score:

                best_score = score
                best = mrz

    if best is None:

        raise Exception(
            "Passport MRZ not detected"
        )

    data = best.to_dict()

    if (
        best_score < MIN_VALID_SCORE
        or not data.get(
            "valid_date_of_birth"
        )
    ):

        raise Exception(
            "Low confidence passport extraction. Please upload a clearer image."
        )

    return extract_fields(
        best
    )