from passporteye import read_mrz
from datetime import datetime, date
import cv2
import os
import tempfile

MIN_VALID_SCORE = 70


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


def try_read(path):

    try:

        mrz = read_mrz(path)

        if mrz:

            print(
                "MRZ Score:",
                mrz.to_dict().get(
                    "valid_score",
                    0
                )
            )

        return mrz

    except Exception as e:

        print(
            "MRZ failed:",
            e
        )

        return None


def ocr_passport(path):

    image = cv2.imread(path)

    if image is None:

        raise Exception(
            "Unable to read image"
        )

    """
    ATTEMPT 1
    Original Image
    """

    mrz = try_read(path)

    """
    ATTEMPT 2
    Sharpened Image
    """

    if mrz is None:

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

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

        temp = tempfile.mktemp(
            suffix=".jpg"
        )

        cv2.imwrite(
            temp,
            sharpened
        )

        mrz = try_read(temp)

        os.remove(temp)

    """
    FINAL VALIDATION
    """

    if mrz is None:

        raise Exception(
            "Passport MRZ not detected. Please upload a clearer passport image."
        )

    data = mrz.to_dict()

    score = data.get(
        "valid_score",
        0
    )

    if (
        score < MIN_VALID_SCORE
        or not data.get(
            "valid_date_of_birth",
            False
        )
    ):

        raise Exception(
            "Low confidence passport extraction. Please upload a clearer image."
        )

    return extract_fields(
        mrz
    )