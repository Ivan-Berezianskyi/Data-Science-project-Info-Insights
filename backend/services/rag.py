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
    def __init__(self, embedding_provider: str = "gemini"):
        """
        Ініціалізує RAG сервіс з підтримкою Gemini або Hugging Face.
        
        Args:
            embedding_provider: "gemini" або "huggingface"
        """
        self.client = QdrantClient(":memory:")
        self.embedding_provider = embedding_provider.lower()
        
        if self.embedding_provider == "gemini":
            self.google_api_key = os.environ.get("GEMINI_API_KEY", "")
            if not self.google_api_key:
                raise ValueError("GEMINI_API_KEY не встановлено в змінних оточення.")
            self.vector_size = 768
            self.gemini_batch_limit = 100
            self.gemini_embed_model = "gemini-embedding-001"
        elif self.embedding_provider == "huggingface":
            self.hf_token = os.environ.get("HF_TOKEN", "")
            if not self.hf_token:
                raise ValueError("HF_TOKEN не встановлено в змінних оточення.")
            # Using granite-embedding-107m-multilingual which produces 768-dimensional embeddings
            self.vector_size = 768
            self.hf_batch_limit = 50  # Hugging Face may have different rate limits
            self.hf_embed_model = "ibm-granite/granite-embedding-278m-multilingual"
            self.hf_api_url = f"https://router.huggingface.co/hf-inference/models/{self.hf_embed_model}/pipeline/feature-extraction"
        else:
            raise ValueError(f"Невідомий провайдер ембедингів: {embedding_provider}. Використовуйте 'gemini' або 'huggingface'.")


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

        all_points_to_upsert = []
        
        if self.embedding_provider == "gemini":
            all_points_to_upsert = self._insert_data_gemini(chunks)
        elif self.embedding_provider == "huggingface":
            all_points_to_upsert = self._insert_data_huggingface(chunks)

        if all_points_to_upsert:
            self.client.upsert(
                collection_name=notebook_id,
                points=all_points_to_upsert,
                wait=True
            )
            #print(f"Успішно завантажено {len(all_points_to_upsert)} точок в '{notebook_id}'.")
        
        return True

    def _insert_data_gemini(self, chunks: list[str]) -> list:
        """Вставляє дані використовуючи Gemini embeddings."""
        all_points_to_upsert = []
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_embed_model}:batchEmbedContents"
        headers = {
            "x-goog-api-key": self.google_api_key,
            "Content-Type": "application/json"
        }

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
        
        return all_points_to_upsert

    def _insert_data_huggingface(self, chunks: list[str]) -> list:
        """Вставляє дані використовуючи Hugging Face embeddings."""
        all_points_to_upsert = []
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }

        for chunk_batch in batch_generator(chunks, self.hf_batch_limit):
            try:
                # Hugging Face feature extraction API expects a list of texts
                payload = {"inputs": chunk_batch}
                response = requests.post(self.hf_api_url, headers=headers, json=payload)
                response.raise_for_status()
                embeddings = response.json()
                
                # Hugging Face returns embeddings as a list of lists
                if isinstance(embeddings, list) and len(embeddings) == len(chunk_batch):
                    for chunk_text, embedding in zip(chunk_batch, embeddings):
                        # Ensure embedding is a list of floats
                        if isinstance(embedding, list):
                            all_points_to_upsert.append(
                                models.PointStruct(
                                    id=str(uuid.uuid4()),
                                    vector=embedding,
                                    payload={"text": chunk_text}
                                )
                            )
                else:
                    # Handle different response formats
                    print(f"Неочікуваний формат відповіді від Hugging Face: {type(embeddings)}")
                    continue

            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP помилка при отриманні ембедингів від Hugging Face: {http_err}")
                print(f"Відповідь: {response.text}")
                continue
            except Exception as err:
                print(f"Інша помилка при роботі з Hugging Face: {err}")
                continue
        
        return all_points_to_upsert

    
    def _get_embedding(self, text: str) -> list[float]:
        """
        Допоміжна функція для отримання одного вектора для запиту.
        Підтримує як Gemini, так і Hugging Face.
        """
        if self.embedding_provider == "gemini":
            return self._get_gemini_embedding(text)
        elif self.embedding_provider == "huggingface":
            return self._get_huggingface_embedding(text)
        else:
            return []

    def _get_gemini_embedding(self, text: str) -> list[float]:
        """
        Отримує ембединг використовуючи Gemini API.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_embed_model}:embedContent"
        headers = {
            "x-goog-api-key": self.google_api_key,
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
            print(f"HTTP помилка при отриманні ембедингу запиту від Gemini: {http_err}")
            print(f"Відповідь: {response.text}")
            return []
        except Exception as err:
            print(f"Інша помилка при роботі з Gemini: {err}")
            return []

    def _get_huggingface_embedding(self, text: str) -> list[float]:
        """
        Отримує ембединг використовуючи Hugging Face API.
        """
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        payload = {"inputs": text}

        try:
            response = requests.post(self.hf_api_url, headers=headers, json=payload)
            response.raise_for_status()
            embedding = response.json()
            
            # Hugging Face returns a list of embeddings (even for single input)
            if isinstance(embedding, list) and len(embedding) > 0:
                return embedding[0] if isinstance(embedding[0], list) else embedding
            elif isinstance(embedding, list):
                return embedding
            else:
                print(f"Неочікуваний формат відповіді від Hugging Face: {type(embedding)}")
                return []
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP помилка при отриманні ембедингу запиту від Hugging Face: {http_err}")
            print(f"Відповідь: {response.text}")
            return []
        except Exception as err:
            print(f"Інша помилка при роботі з Hugging Face: {err}")
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

# Initialize RAG service with provider from environment variable (default: gemini)
_embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "huggingface").lower()
rag_service = RAGService(embedding_provider=_embedding_provider)