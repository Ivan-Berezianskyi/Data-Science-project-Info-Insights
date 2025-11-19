import os
import uuid
from qdrant_client import QdrantClient, models
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter

def batch_generator(data, batch_size):
    """Розбиває список data на пакети розміром batch_size."""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

class RAGService:
    def __init__(self):
        self.client = QdrantClient(":memory:")
        self.api_key = ""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY не встановлено в змінних оточення.")
        
        self.vector_size = 768
        self.gemini_batch_limit = 100
        self.gemini_embed_model = "gemini-embedding-001"


    def create_notebook(self, notebook_id: str):
        """
        Створює нову колекцію (блокнот) в Qdrant.
        """
        try:
            self.client.recreate_collection(
                collection_name=notebook_id,
                vectors_config=models.VectorParams(
                    size=self.vector_size, 
                    distance=models.Distance.COSINE
                ),
            )
            print(f"Колекцію '{notebook_id}' успішно створено.")
        except Exception as e:
            # Qdrant може кинути помилку, якщо колекція вже існує з іншими параметрами
            print(f"Помилка при створенні колекції: {e}")
            raise


    def insert_data(self, notebook_id: str, data: str):

        if not self.client.collection_exists(notebook_id):
            raise ValueError(f"Колекція {notebook_id} не існує. Спочатку створіть її.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50, 
            length_function=len,
            is_separator_regex=False, 
        )
        chunks = text_splitter.split_text(data)
        #print(f"Текст розбито на {len(chunks)} чанків.")

        if not chunks:
            #print("Немає чанків для обробки.")
            return True

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_embed_model}:batchEmbedContents"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        all_points_to_upsert = [] 
        for chunk_batch in batch_generator(chunks, self.gemini_batch_limit):

            embedding_requests = []
            for chunk_text in chunk_batch:
                embedding_requests.append({
                    "model": f"models/{self.gemini_embed_model}",
                    "content": {"parts": [{"text": chunk_text}]},
                    "output_dimensionality": self.vector_size 
                })

            api_data = {"requests": embedding_requests}

            try:
                response = requests.post(url, headers=headers, json=api_data)
                response.raise_for_status()
                response_data = response.json()
                
                embeddings = response_data.get('embeddings', [])
                #print(f"Отримано {len(embeddings)} ембедингів для пакету.")

                for chunk_text, embedding in zip(chunk_batch, embeddings):
                    all_points_to_upsert.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=embedding["values"],
                            payload={"text": chunk_text}
                        )
                    )

            except requests.exceptions.HTTPError as http_err:
                #print(f"HTTP помилка при отриманні ембедингів: {http_err}")
                #print(f"Відповідь: {response.text}")
                continue # Пропускаємо цей пакет
            except Exception as err:
                #print(f"Інша помилка: {err}")
                continue

        if all_points_to_upsert:
            self.client.upsert(
                collection_name=notebook_id,
                points=all_points_to_upsert,
                wait=True
            )
            #print(f"Успішно завантажено {len(all_points_to_upsert)} точок в '{notebook_id}'.")
        
        return True

    
    def _get_embedding(self, text: str) -> list[float]:
        """
        Допоміжна функція для отримання одного вектора для запиту.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_embed_model}:embedContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "model": f"models/{self.gemini_embed_model}",
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": self.vector_size
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            embedding = response.json().get('embedding', {})
            return embedding.get('values', [])
        except requests.exceptions.HTTPError as http_err:
            #print(f"HTTP помилка при отриманні ембедингу запиту: {http_err}")
            #print(f"Відповідь: {response.text}")
            return []
        except Exception as err:
            #print(f"Інша помилка: {err}")
            return []


    def search_data(self, notebook_id: str, query: str, limit: int = 5):
        if not self.client.collection_exists(notebook_id):
            raise ValueError(f"Колекція {notebook_id} не існує.")

        query_vector = self._get_embedding(query)

        if not query_vector:
            #print("Не вдалося отримати вектор для запиту.")
            return []

        search_results = self.client.query_points(
            collection_name=notebook_id,
            query=query_vector,
            limit=limit,
            with_payload=True
        )
        
        # Спочатку подивимося на структуру результатів
        #print(f"Тип результату: {type(search_results)}")
        #print(f"Результат: {search_results}")
        
        # Спробуємо різні варіанти обробки
        results = []
        
        if hasattr(search_results, 'points'):
            # Якщо є атрибут points
            for point in search_results.points:
                if isinstance(point, tuple):
                    # Якщо це кортеж (зазвичай: (scored_point, score))
                    results.append({
                        "text": point[0].payload.get("text", "")
                    })
                else:
                    # Якщо це об'єкт
                    results.append({
                        "text": point.payload.get("text", ""),
                    })
        else:
            # Якщо search_results - це безпосередньо список
            for item in search_results:
                if isinstance(item, tuple):
                    results.append({
                        "text": item[0].payload.get("text", ""),
                    })
                else:
                    results.append({
                        "text": item.payload.get("text", ""),
                    })
        
        return results


    def delete_notebook(self, notebook_id: str):
        if self.client.collection_exists(notebook_id):
            self.client.delete_collection(notebook_id)
            #print(f"Колекцію '{notebook_id}' видалено.")
        else:
            raise ValueError(f"Колекція {notebook_id} не існує.")

rag_service = RAGService()