import json_repair
from services.openai_service import client
from langchain_text_splitters import RecursiveCharacterTextSplitter

prompt = """
You are an OCR and image understanding system. Process the image and return a JSON object.
Follow this structure exactly:

{
  "ocr_text": "<full extracted text>",
  "description": "<image description>",
  "summary": "<semantic summary for RAG>",
  "tags": ["tag1", "tag2", ...]
}

Rules:
- Return ONLY valid JSON.
- Do not include explanations outside JSON.
- OCR text must contain line breaks exactly as in the image.
- If something is unreadable, write "[unreadable]".
- Description = short objective description.
- Summary = coherent paragraph merging OCR + visual context.
- Tags = 5–12 short searchable keywords.
"""

ocr_model = "gpt-4o-mini"


def image_recognition(images: list[str]) -> list[str]:
    image_request = [{"type": "input_image", "image_url": image} for image in images]
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                ]
                + image_request,
            }
        ],
    )
    data = json_repair.loads(response.output_text)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(data["ocr_text"]) + [data["description"], data["summary"]]
