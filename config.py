# config.py — Configuration for Hybrid Travel Assistant
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"  # Fixed: Changed from 'hybridchat' to 'neo4j'
NEO4J_PASSWORD = "123456789"

# Gemini API (FREE - replace with your NEW key after revoking the old one!)
GEMINI_API_KEY = "AIzaSyAyccoJJ6T2_JnyVJ8glyJrVomGRZ74TVU"  # Get from https://aistudio.google.com/apikey

# Pinecone
PINECONE_API_KEY = "pcsk_2EvniE_GWWZq4g7B9Yb4dedq26VgSQqeKxn8CBSDEh2e3Z7ym2mznpdRqgqxsQkvk8ia2M" # your Pinecone API key
PINECONE_ENV = "us-east-1"   # example
PINECONE_INDEX_NAME = "hybridchat"
# Using sentence-transformers 'all-MiniLM-L6-v2' model -> 384 dimensions (FREE!)
PINECONE_VECTOR_DIM = 384  # Changed from 1536 to 384 for sentence-transformers
