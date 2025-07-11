import os
from features.demo.requester import post, get

class PineconeService:
    def __init__(self):
        self.fastapi_base_url = os.getenv("FASTAPI_BASE_URL", "http://kong:8000/api")

    def upsert(self, vectors, namespace=None, batch_size=100):
        url = f"{self.fastapi_base_url}/pinecone_upsert"
        data = {
            "vectors": vectors,
            "namespace": namespace,
            "batch_size": batch_size
        }
        resp = post(url, json=data)
        return resp.json().get('result')

    def query(self, vector, top_k=10, namespace=None, filter=None, include_values=False, include_metadata=True):
        url = f"{self.fastapi_base_url}/pinecone_query"
        data = {
            "vector": vector,
            "top_k": top_k,
            "namespace": namespace,
            "filter": filter,
            "include_values": include_values,
            "include_metadata": include_metadata,
        }
        resp = post(url, json=data)
        return resp.json().get('result')

    def delete(self, ids=None, filter=None, namespace=None):
        url = f"{self.fastapi_base_url}/pinecone_delete"
        data = {
            "ids": ids,
            "filter": filter,
            "namespace": namespace,
        }
        resp = post(url, json=data)
        return resp.json().get('result')

    def fetch(self, ids, namespace=None):
        url = f"{self.fastapi_base_url}/pinecone_fetch"
        data = {
            "ids": ids,
            "namespace": namespace
        }
        resp = post(url, json=data)
        return resp.json().get('result')

    def info(self):
        url = f"{self.fastapi_base_url}/pinecone_info"
        resp = get(url)
        return resp.json().get('result')

    def describe_index(self):
        url = f"{self.fastapi_base_url}/pinecone_describe_index"
        resp = get(url)
        return resp.json().get('result')
