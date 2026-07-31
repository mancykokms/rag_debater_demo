import uuid

from sentence_transformers import SentenceTransformer
import streamlit as st
import chromadb

            
def chunk_text(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        start = start + (chunk_size - overlap)
    return chunks

@st.cache_resource
def get_embedding_model(model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model
    
def embed_chunks(chunks):
    model = get_embedding_model()
    return model.encode(chunks)

@st.cache_resource    
def get_chroma_collection():
    client = chromadb.PersistentClient(path="./chroma_data") 
    collection = client.get_or_create_collection(name="motion_sources")
    return collection    


def store_source(text, team_id, motion_id):
    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)
    collection = get_chroma_collection()
    collection.add(
        ids=[str(uuid.uuid4().hex[:8]) for _ in chunks], 
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"team_id": team_id, "motion_id": motion_id} for _ in chunks]
    )
    
    
    






if __name__ == "__main__":
    # sample_text = "This is a test sentence to check if the chunking function works correctly and produces overlapping segments as expected for our debate practice tool"
    # result = chunk_text(sample_text, chunk_size=10, overlap=3)
    # for i, chunk in enumerate(result):
    #     print(f"Chunk {i}: {chunk}")
        
    # test_chunks = ["This is about climate policy", "This is about economic growth"]
    # embeddings = embed_chunks(test_chunks)
    # print(type(embeddings))
    # print(len(embeddings))
    # print(len(embeddings[0]))
    
    store_source(
    "This is a test source about climate policy. Governments around the world have debated carbon taxes for decades. Some argue they effectively reduce emissions, while others claim they disproportionately harm lower income households.",
    team_id="test_team",
    motion_id="test_motion"
    )

    collection = get_chroma_collection()
    results = collection.get()
    print(results)