from sqlalchemy import create_engine, Column, String, Integer, Text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import dotenv

dotenv.load_dotenv()

# Set up the base
Base = declarative_base()

# Define the Article model
class Papers(Base):
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = Column(Text, nullable=False)  # Storing as a comma-separated string
    keywords = Column(Text, nullable=False)  # Storing as a comma-separated string
    doi = Column(String, unique=True, nullable=False)
    file = Column(String, unique=True, nullable=False)

# Create an engine
engine = create_engine(os.getenv('FILES_DB'))

# Create the table in the database
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

inspector = inspect(engine)
tables = inspector.get_table_names()

print(tables)

