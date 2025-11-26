import os
import uuid
from qdrant_client import QdrantClient, models
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.openai_service import client


def batch_generator(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


class RAGService:
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        """
        Ініціалізує RAG сервіс, що використовує OpenAI embeddings.

        Args:
            embedding_model: назва моделі ембедингів OpenAI.
        """
        self.client = QdrantClient(
            "https://d6547155-728d-481c-b616-df5e5a8cde21.eu-west-2-0.aws.cloud.qdrant.io",
            api_key=os.getenv("QDRANT_APIKEY"),
        )
        self.embedding_model = embedding_model
        self.vector_size = 1536
        self.batch_limit = 100

    def create_notebook(self, notebook_id: str):
        """
        Створює нову колекцію (блокнот) в Qdrant.
        """
        try:
            self.client.recreate_collection(
                collection_name=notebook_id,
                vectors_config=models.VectorParams(
                    size=self.vector_size, distance=models.Distance.COSINE
                ),
            )
            print(f"Колекцію '{notebook_id}' успішно створено.")
        except Exception as e:
            # Qdrant може кинути помилку, якщо колекція вже існує з іншими параметрами
            print(f"Помилка при створенні колекції: {e}")
            raise

    def insert_data(self, notebook_id: str, data: str, source: str | None = None):

        if not self.client.collection_exists(notebook_id):
            raise ValueError(f"Колекція {notebook_id} не існує. Спочатку створіть її.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(data)
        self.insert_split_data(notebook_id, chunks, source)

    
    def insert_split_data(self, notebook_id: str, chunks: list[str], source: str | None = None):
        if not chunks:
            return True

        all_points_to_upsert = self._insert_data_openai(chunks, source=source)

        if all_points_to_upsert:
            self.client.upsert(
                collection_name=notebook_id, points=all_points_to_upsert, wait=True
            )

        return True

    def _insert_data_openai(self, chunks: list[str], source: str | None = None) -> list:
        all_points_to_upsert = []

        for chunk_batch in batch_generator(chunks, self.batch_limit):
            try:
                response = client.embeddings.create(
                    model=self.embedding_model,
                    input=chunk_batch,
                )
                for chunk_text, item in zip(chunk_batch, response.data):
                    all_points_to_upsert.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=item.embedding,
                            payload={
                                "text": chunk_text,
                                "source": source,
                            },
                        )
                    )
            except Exception as err:
                print(f"Помилка при отриманні ембедингів від OpenAI: {err}")
                continue

        return all_points_to_upsert

    def _get_embedding(self, text: str) -> list[float]:
        """
        Допоміжна функція для отримання одного вектора для запиту.
        Використовує OpenAI embeddings.
        """
        try:
            response = client.embeddings.create(
                model=self.embedding_model,
                input=[text],
            )
            if response.data:
                return response.data[0].embedding
            return []
        except Exception as err:
            print(f"Помилка при отриманні ембедингу запиту від OpenAI: {err}")
            return []

    def search_data(self, notebook_id: str, query: str, limit: int = 5):
        if not self.client.collection_exists(notebook_id):
            raise ValueError(f"Колекція {notebook_id} не існує.")

        query_vector = self._get_embedding(query)

        if not query_vector:
            return []

        search_results = self.client.query_points(
            collection_name=notebook_id,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )

        results = []

        if hasattr(search_results, "points"):
            for point in search_results.points:
                payload = point[0].payload if isinstance(point, tuple) else point.payload
                results.append(
                    {
                        "text": payload.get("text", ""),
                        "source": payload.get("source"),
                    }
                )
        else:
            for item in search_results:
                payload = item[0].payload if isinstance(item, tuple) else item.payload
                results.append(
                    {
                        "text": payload.get("text", ""),
                        "source": payload.get("source"),
                    }
                )

        return results

    def delete_notebook(self, notebook_id: str):
        if self.client.collection_exists(notebook_id):
            self.client.delete_collection(notebook_id)
        else:
            raise ValueError(f"Колекція {notebook_id} не існує.")

    def scroll_notebook(self, notebook_id: str, limit: int = 20):
        records, _ = self.client.scroll(
            collection_name=notebook_id,
            limit=limit,
            with_vectors=False,
            with_payload=True,
        )
        texts = []
        for record in records:
            content = record.payload.get("text", "")
            if content:
                texts.append(content)
        return texts


rag_service = RAGService()
