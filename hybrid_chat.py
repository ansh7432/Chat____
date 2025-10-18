# hybrid_chat.py
import json
from typing import List
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from neo4j import GraphDatabase
import config

# -----------------------------
# Config
# -----------------------------
CHAT_MODEL = "gemini-2.0-flash-exp"  # FREE Gemini model
TOP_K = 5

INDEX_NAME = config.PINECONE_INDEX_NAME

# -----------------------------
# Initialize clients
# -----------------------------
# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(CHAT_MODEL)

# Load FREE embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # FREE, 384 dimensions
print("Embedding model loaded!")

# Connect to Pinecone
pc = Pinecone(api_key=config.PINECONE_API_KEY)

# Connect to Pinecone index
if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating managed index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=config.PINECONE_VECTOR_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east1-gcp")
    )

index = pc.Index(INDEX_NAME)

# Connect to Neo4j
driver = GraphDatabase.driver(
    config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)

# -----------------------------
# Helper functions
# -----------------------------
def embed_text(text: str) -> List[float]:
    """Get embedding for a text string using FREE sentence-transformers."""
    embedding = embedding_model.encode(text, show_progress_bar=False)
    return embedding.tolist()

def pinecone_query(query_text: str, top_k=TOP_K):
    """Query Pinecone index using embedding."""
    vec = embed_text(query_text)
    res = index.query(
        vector=vec,
        top_k=top_k,
        include_metadata=True,
        include_values=False
    )
    print("DEBUG: Pinecone top 5 results:")
    print(len(res["matches"]))
    return res["matches"]

def fetch_graph_context(node_ids: List[str], neighborhood_depth=1):
    """Fetch neighboring nodes from Neo4j."""
    facts = []
    with driver.session() as session:
        for nid in node_ids:
            q = (
                "MATCH (n:Entity {id:$nid})-[r]-(m:Entity) "
                "RETURN type(r) AS rel, labels(m) AS labels, m.id AS id, "
                "m.name AS name, m.type AS type, m.description AS description "
                "LIMIT 10"
            )
            recs = session.run(q, nid=nid)
            for r in recs:
                facts.append({
                    "source": nid,
                    "rel": r["rel"],
                    "target_id": r["id"],
                    "target_name": r["name"],
                    "target_desc": (r["description"] or "")[:400],
                    "labels": r["labels"]
                })
    print("DEBUG: Graph facts:")
    print(len(facts))
    return facts

def build_prompt(user_query, pinecone_matches, graph_facts):
    """Build a chat prompt combining vector DB matches and graph facts."""
    
    vec_context = []
    for m in pinecone_matches:
        meta = m["metadata"]
        score = m.get("score", None)
        snippet = f"- id: {m['id']}, name: {meta.get('name','')}, type: {meta.get('type','')}, score: {score}"
        if meta.get("city"):
            snippet += f", city: {meta.get('city')}"
        vec_context.append(snippet)

    graph_context = [
        f"- ({f['source']}) -[{f['rel']}]-> ({f['target_id']}) {f['target_name']}: {f['target_desc']}"
        for f in graph_facts
    ]

    # Build prompt for Gemini (single string format)
    prompt_text = f"""You are a helpful travel assistant specializing in Vietnam travel planning.

Use the provided semantic search results and graph facts to answer the user's query in a comprehensive and helpful manner.

USER QUERY: {user_query}

TOP SEMANTIC MATCHES (from vector database):
{chr(10).join(vec_context[:10])}

GRAPH FACTS (neighboring relations):
{chr(10).join(graph_context[:20])}

Based on the above information, please:
1. Answer the user's question comprehensively
2. Provide specific recommendations with details
3. Create a structured itinerary if requested
4. Reference node IDs when mentioning specific places or attractions
5. Include practical travel tips where relevant

Your response:"""
    
    return prompt_text

def call_chat(prompt_text):
    """Call Gemini API for chat completion."""
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"

# -----------------------------
# Interactive chat
# -----------------------------
def interactive_chat():
    print("Hybrid travel assistant. Type 'exit' to quit.")
    while True:
        query = input("\nEnter your travel question: ").strip()
        if not query or query.lower() in ("exit","quit"):
            break

        matches = pinecone_query(query, top_k=TOP_K)
        match_ids = [m["id"] for m in matches]
        graph_facts = fetch_graph_context(match_ids)
        prompt = build_prompt(query, matches, graph_facts)
        answer = call_chat(prompt)
        print("\n=== Assistant Answer ===\n")
        print(answer)
        print("\n=== End ===\n")

if __name__ == "__main__":
    interactive_chat()
