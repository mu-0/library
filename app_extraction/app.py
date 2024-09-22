import pdf2image
import io
import base64
import flask
import werkzeug
from pydantic import BaseModel, ValidationError
from openai import OpenAI
import json
import dotenv
import os

# must load OPENAI_API_KEY
dotenv.load_dotenv()

app = flask.Flask(__name__)
client = OpenAI()


# requests metadata extraction from gpt based on image of page (in b64)
def get_metadata(filename, base64_image = None):

    # create class for data structure
    class BookInfo(BaseModel):
        title: str
        authors: list[str]


    if base64_image is not None:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at data extraction. You will be given the cover page and filename of a book. Use those to determine the title and authors."},
                {"role": "user", "content": [
                    {
                      "type": "image_url",
                      "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                      }
                    }
        		]
        		},
                {"role": "user", "content": f"The book file is {filename}. What are the book title and authors?"}
            ],
        	response_format=BookInfo,
        )
    else:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at structured data extraction. You will be given the filename of a book and should convert it into the given structure based on context and your knowledge. The title field should be the book title, and authors the book's authors."},
                {"role": "user", "content": f"{filename}"}
            ],
        	response_format=BookInfo,
        )

    
    content = completion.choices[0].message.content
    
    try:
        json_content = json.loads(content)
        validated_content = BookInfo(**json_content)
        return content
    except ValidationError as e:
        print("response not in format:")
        print(e)
        return None


# returns first page of pdf as b64 data
def get_page_image(pdf_bytes):

    # Convert the first page of the PDF to an image
    images = pdf2image.convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
    
    # Convert the image to a byte buffer
    img_buffer = io.BytesIO()
    images[0].save(img_buffer, format='JPEG')
    
    # Encode the byte data to base64
    return base64.b64encode(img_buffer.getvalue()).decode('utf-8')


# returns file metadata in json
@app.route("/extract", methods=["POST"])
def extract():

    # validate post contents
    if "file" not in flask.request.files:
        return "no file uploaded", 400

    file = flask.request.files["file"]

    # validate file exists
    if not file:
        return "invalid file", 400

    filename = werkzeug.utils.secure_filename(file.filename)

    if "use_image" in flask.request.form:
        json_data = get_metadata(filename, base64_image = get_page_image(file.read()))
    else: 
        json_data = get_metadata(filename)

    return json_data


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
