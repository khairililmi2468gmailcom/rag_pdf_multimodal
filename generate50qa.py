import fitz  # PyMuPDF
import json
import random
from tqdm import tqdm
from PIL import Image
import base64
from io import BytesIO
import subprocess
import re

# === Extract text and image from PDF ===
def extract_pdf_content(pdf_path):
    doc = fitz.open(pdf_path)
    text_chunks = []
    image_data = []

    for page in doc:
        text = page.get_text().strip()
        if text:
            text_chunks.append(text)

        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_data.append(image_bytes)

    return text_chunks, image_data

# === Try parse as JSON ===
def extract_json_block(text):
    try:
        match = re.search(r"(\[\s*{.*?}\s*\]|{.*?})", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        return None
    return None

# === Fallback: Extract QAs from markdown-style output ===
def extract_markdown_qa(text):
    qa_pairs = []
    q_matches = re.findall(r"(?:Q\d*[:：]|Question\s*\d*[:：])\s*(.*)", text)
    a_matches = re.findall(r"(?:A\d*[:：]|Answer\s*\d*[:：])\s*(.*)", text)
    for q, a in zip(q_matches, a_matches):
        qa_pairs.append({
            "question": q.strip(),
            "answer": a.strip()
        })
    return qa_pairs if qa_pairs else None

# === Convert image to base64 ===
def image_to_base64(image_bytes):
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# === QA Generation ===
def generate_qa(text_chunks, image_data, total_q=50):
    text_prompt_template = """
You are an expert AI trained on medical education material.
Based on the following content, generate 3 relevant question-answer pairs.

Context:
{context}
    
Output format (JSON):
[
  {{
    "question": "...",
    "answer": "..."
  }},
  ...
]
"""

    image_prompt_template = """
You are an expert AI trained on medical images and illustrations.
Given the image below, generate 1 medical question and its correct answer.

Output format (JSON):
{{
  "question": "...",
  "answer": "..."
}}
"""

    qa_list = []

    # === TEXT QA ===
    print("Generating text-based questions using LLaMA3...")
    text_chunks_pool = random.sample(text_chunks, len(text_chunks))
    i = 0
    while len(qa_list) < total_q // 2 and i < len(text_chunks_pool):
        chunk = text_chunks_pool[i]
        i += 1
        prompt = text_prompt_template.format(context=chunk)
        result = subprocess.run(
            ["ollama", "run", "llama3:latest"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = result.stdout.decode("utf-8")
        parsed = extract_json_block(output)
        if parsed:
            qa_list.extend(parsed if isinstance(parsed, list) else [parsed])
        else:
            # Coba parse markdown
            fallback_qa = extract_markdown_qa(output)
            if fallback_qa:
                qa_list.extend(fallback_qa)
            else:
                print("⚠️ Failed to parse LLaMA3 output:\n", output[:500])

    # === IMAGE QA ===
    print("Generating image-based questions using LLaVA...")
    image_pool = random.sample(image_data, len(image_data))
    j = 0
    while len(qa_list) < total_q and j < len(image_pool):
        img_bytes = image_pool[j]
        j += 1
        b64_image = image_to_base64(img_bytes)
        prompt = image_prompt_template
        result = subprocess.run(
            ["ollama", "run", "llava:7b"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = result.stdout.decode("utf-8")
        parsed = extract_json_block(output)
        if parsed:
            qa_list.extend(parsed if isinstance(parsed, list) else [parsed])
        else:
            fallback_qa = extract_markdown_qa(output)
            if fallback_qa:
                qa_list.extend(fallback_qa)
            else:
                print("⚠️ Failed to parse LLaVA output:\n", output[:500])

    # === Final Top Up ===
    if len(qa_list) < total_q:
        print("🔁 Topping up with more LLaMA3 questions...")
        remaining_chunks = text_chunks_pool[i:]
        for chunk in remaining_chunks:
            if len(qa_list) >= total_q:
                break
            prompt = text_prompt_template.format(context=chunk)
            result = subprocess.run(
                ["ollama", "run", "llama3:latest"],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output = result.stdout.decode("utf-8")
            parsed = extract_json_block(output)
            if parsed:
                qa_list.extend(parsed if isinstance(parsed, list) else [parsed])
            else:
                fallback_qa = extract_markdown_qa(output)
                if fallback_qa:
                    qa_list.extend(fallback_qa)

    qa_list = qa_list[:total_q]

    with open("generated_qa.json", "w") as f:
        json.dump(qa_list, f, indent=2)

    print(f"✅ Done. Saved {len(qa_list)} questions to generated_qa.json")

# === Run ===
if __name__ == "__main__":
    extract_path = "/home/alim/alim_workspace/deepseek/rag_pdf/content/2021-3-12-Handout-Med-Student.pdf"
    text_chunks, image_data = extract_pdf_content(extract_path)
    generate_qa(text_chunks, image_data, total_q=50)
