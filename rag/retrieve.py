from rag.ingest import get_embedding_model, get_chroma_collection

def retrieve_relevant_chunks(query_text, team_id, motion_id, n_results=3):
    embedding_model = get_embedding_model()
    query_embeddings = embedding_model.encode(query_text)
    collection = get_chroma_collection()
    
    results = collection.query(
        query_embeddings=[query_embeddings],
        n_results=n_results,
        where={"$and": [{"team_id": team_id}, {"motion_id": motion_id}]}
    )
    return results



if __name__ == "__main__":
    results = retrieve_relevant_chunks(
        query_text="Are carbon taxes fair to poor people?",
        team_id="test_team",
        motion_id="test_motion",
        n_results=3
    )
    print(results)