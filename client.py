from openai import OpenAI
from pinecone import Pinecone

from consts import openai_api_key, pinecone_api, pinecone_index_name

openai_client = OpenAI(
    api_key=openai_api_key
)

pc = Pinecone(api_key=pinecone_api)
pinecone_index = pc.Index(pinecone_index_name)
