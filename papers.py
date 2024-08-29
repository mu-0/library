import pdf2image
import io
import base64
import dotenv
import os
import json
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# returns first page of pdf as b64 data
def get_page_image(pdf_path):

    # Convert the first page of the PDF to an image
    images = pdf2image.convert_from_path(pdf_path, first_page=1, last_page=1)
    
    # Convert the image to a byte buffer
    img_buffer = io.BytesIO()
    images[0].save(img_buffer, format='JPEG')
    
    # Encode the byte data to base64
    return base64.b64encode(img_buffer.getvalue()).decode('utf-8')


def test_get_page_image(pdf_path):
    from PIL import Image
    data = base64.b64decode(get_page_image(pdf_path))
    img = Image.open(io.BytesIO(data))
    img.show()


# requests metadata extraction from gpt based on image of page (in b64)
def get_metadata(base64_image):
    from pydantic import BaseModel, ValidationError
    from openai import OpenAI
    import json

    # create class for data structure
    class PaperInfo(BaseModel):
        title: str
        authors: list[str]
        keywords: list[str]
        doi: str

    # must load OPENAI_API_KEY
    dotenv.load_dotenv()
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure."},
            {"role": "user", "content": [
                {
                  "type": "image_url",
                  "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                  }
                }
    		]
    		}
        ],
    	response_format=PaperInfo,
    )
    
    content = completion.choices[0].message.content
    
    try:
        json_content = json.loads(content)
        validated_content = PaperInfo(**json_content)
        return content
    except ValidationError as e:
        print("response not in format:")
        print(e)
        return None


# Calculate MD5 hash of a file
def calculate_file_md5(file_path):
    import hashlib
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def get_filename(file_path):
    file_md5 = calculate_file_md5(file_path)
    new_filename = file_md5 + os.path.splitext(file_path)[-1]
    return new_filename

# Define the Papers model
Base = declarative_base()
class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = Column(Text, nullable=False)  # Storing as a comma-separated string
    keywords = Column(Text, nullable=False)  # Storing as a comma-separated string
    doi = Column(String, unique=True, nullable=False)
    file = Column(String, unique=True, nullable=False)

def handle_file(session, file_path, force=False):

    new_filename = get_filename(file_path)

    # Set up S3 client
    region = os.environ["AWS_REGION"]
    s3_bucket_name = os.environ["LIB_BUCKET_NAME"]
    s3_file = os.path.join("papers", new_filename)
    s3_client = boto3.client("s3", region_name=region)

    # Make sure file doesn't already exist
    if not force:
        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=s3_file)
            print("File already exists on server!")
            os.remove(file_path)
            return
        except ClientError as e:
            if int(e.response["Error"]["Code"]) != 404:
                print("Other client error:", e)
                return

    metadata_json = json.loads(get_metadata(get_page_image(file_path)))

    # create new paper object
    paper = Paper(
        title = metadata_json['title'],
        authors = ", ".join(metadata_json['authors']),
        keywords = ", ".join(metadata_json['keywords']),
        doi = metadata_json['doi'],
        file = new_filename,
    )

    # add paper to database
    session.add(paper)
    session.commit()

    # upload paper to s3
    response = s3_client.upload_file(file_path, s3_bucket_name, s3_file)

    os.remove(file_path)

# Returns list of files in intake_dir
def intake(intake_dir):
    full_paths = [os.path.join(intake_dir, f) for f in os.listdir(intake_dir) if os.path.isfile(os.path.join(intake_dir, f))]
    return full_paths

if __name__ == "__main__":
    dotenv.load_dotenv()
    engine = create_engine(os.environ["FILES_DB"])
    Session = sessionmaker(bind=engine)
    session = Session()
    files = intake("intake")
    for file in files:
        print(f"processing {file}...")
        handle_file(session, file)
