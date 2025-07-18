from pinecone import Pinecone
import os

def delete_pinecone_namespace(machine_id):
    client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = client.Index(os.getenv("PINECONE_INDEX"))
    print(f"[delete_pinecone_namespace] Deleting namespace: {machine_id}")

    # Use the proper delete method
    try:
        response = index.delete_namespace(namespace=machine_id)
        print(f"[delete_pinecone_namespace] delete_namespace response: {response}")
        return response
    except Exception as e:
        print(f"[delete_pinecone_namespace] delete_namespace error: {e}")
        raise