#!/usr/bin/env python3
"""
Test script to verify all dependencies and APIs are working
Run this before starting the main application
"""

import sys

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing imports...\n")
    
    tests = [
        ("neo4j", "Neo4j driver"),
        ("pinecone", "Pinecone client"),
        ("sentence_transformers", "Sentence Transformers"),
        ("google.generativeai", "Google Gemini API"),
        ("tqdm", "TQDM progress bars"),
        ("networkx", "NetworkX"),
        ("pyvis", "PyVis"),
    ]
    
    failed = []
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {e}")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("\n✅ All imports successful!\n")
    return True

def test_embedding_model():
    """Test sentence-transformers model loading"""
    print("🔍 Testing embedding model...\n")
    try:
        from sentence_transformers import SentenceTransformer
        print("Loading model 'all-MiniLM-L6-v2'...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test embedding
        test_text = "Vietnam travel guide"
        embedding = model.encode(test_text)
        
        print(f"✅ Model loaded successfully!")
        print(f"✅ Embedding dimension: {len(embedding)}")
        print(f"✅ Sample embedding (first 5 values): {embedding[:5]}\n")
        return True
    except Exception as e:
        print(f"❌ Embedding model test failed: {e}\n")
        return False

def test_config():
    """Test configuration file"""
    print("🔍 Testing configuration...\n")
    try:
        import config
        
        # Check required fields
        required = [
            'NEO4J_URI',
            'NEO4J_USER', 
            'NEO4J_PASSWORD',
            'GEMINI_API_KEY',
            'PINECONE_API_KEY',
            'PINECONE_INDEX_NAME',
            'PINECONE_VECTOR_DIM'
        ]
        
        missing = []
        for field in required:
            if not hasattr(config, field):
                missing.append(field)
            else:
                value = getattr(config, field)
                # Check if it's a placeholder
                if isinstance(value, str) and ('YOUR' in value.upper() or 'CHANGE' in value.upper()):
                    print(f"⚠️  {field}: Placeholder value detected - please update!")
                else:
                    print(f"✅ {field}: Set")
        
        if missing:
            print(f"\n❌ Missing config fields: {', '.join(missing)}")
            return False
        
        # Check vector dimension
        if config.PINECONE_VECTOR_DIM != 384:
            print(f"⚠️  PINECONE_VECTOR_DIM should be 384 (currently: {config.PINECONE_VECTOR_DIM})")
        
        print("\n✅ Configuration looks good!\n")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}\n")
        return False

def test_pinecone_connection():
    """Test Pinecone API connection"""
    print("🔍 Testing Pinecone connection...\n")
    try:
        from pinecone import Pinecone
        import config
        
        pc = Pinecone(api_key=config.PINECONE_API_KEY)
        indexes = pc.list_indexes()
        
        print(f"✅ Connected to Pinecone!")
        print(f"✅ Existing indexes: {indexes.names() if hasattr(indexes, 'names') else 'N/A'}\n")
        return True
    except Exception as e:
        print(f"❌ Pinecone connection failed: {e}\n")
        print("   Please check your PINECONE_API_KEY in config.py\n")
        return False

def test_gemini_api():
    """Test Gemini API connection"""
    print("🔍 Testing Gemini API...\n")
    try:
        import google.generativeai as genai
        import config
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'Hello from Gemini!' in exactly 3 words.")
        
        print(f"✅ Connected to Gemini API!")
        print(f"✅ Test response: {response.text}\n")
        return True
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}\n")
        print("   Please check your GEMINI_API_KEY in config.py\n")
        print("   Remember to revoke the old key and generate a new one!\n")
        return False

def test_neo4j_connection():
    """Test Neo4j database connection"""
    print("🔍 Testing Neo4j connection...\n")
    try:
        from neo4j import GraphDatabase
        import config
        
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        
        # Test connection
        driver.verify_connectivity()
        
        print(f"✅ Connected to Neo4j at {config.NEO4J_URI}!")
        
        # Check if data exists
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            print(f"✅ Current node count: {count}")
            if count == 0:
                print("   ⚠️  No nodes found - run 'python load_to_neo4j.py' to load data\n")
            else:
                print()
        
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}\n")
        print("   Make sure Neo4j is running and credentials in config.py are correct\n")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 HYBRID AI TRAVEL ASSISTANT - SYSTEM CHECK")
    print("="*60)
    print()
    
    print(f"Python version: {sys.version}\n")
    
    results = {
        "Imports": test_imports(),
        "Embedding Model": test_embedding_model(),
        "Configuration": test_config(),
        "Pinecone API": test_pinecone_connection(),
        "Gemini API": test_gemini_api(),
        "Neo4j Database": test_neo4j_connection(),
    }
    
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
    
    print("="*60)
    
    if all(results.values()):
        print("\n🎉 All tests passed! Your system is ready to go!")
        print("\n📋 Next steps:")
        print("   1. If Neo4j has no nodes, run: python load_to_neo4j.py")
        print("   2. Upload embeddings: python pinecone_upload.py")
        print("   3. Start chatting: python hybrid_chat.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before proceeding.")
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n   Failed: {', '.join(failed_tests)}")
    
    print()

if __name__ == "__main__":
    main()
