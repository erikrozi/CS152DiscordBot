from PIL import Image
import pytesseract

def process_image(loc, lang=None):
    custom_config = r"--oem 3 --psm 3"
    try:
        img = Image.open(loc)
        #img = img.convert('1')
        parsed_string = pytesseract.image_to_string(img, lang=lang, config=custom_config, timeout=5)
        parsed_string = " ".join(parsed_string.split()) 
        return parsed_string
    except RuntimeError as timeout_error:
        return ""

