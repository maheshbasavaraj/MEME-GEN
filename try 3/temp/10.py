"""
Minimal PDF Q&A with Google Gemini

A lightweight script that answers questions about PDF content using Google's Gemini API.
"""

import PyPDF2
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def process_pdf(pdf_path, chunk_size=1000):
    """Extract text from PDF and split into chunks."""
    # Extract text
    text = ""
    with open(pdf_path, 'rb') as file:
        for page in PyPDF2.PdfReader(file).pages:
            text += page.extract_text()
            
    # Split into chunks with simple approach (no overlap for simplicity)
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

def query_pdf(question, chunks, api_key, max_chunks=2):
    """Find relevant chunks and get answer from Gemini."""
    # Create TF-IDF vectorizer and get similarities
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(chunks + [question])
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    
    # Get most relevant chunks
    top_indices = similarities.argsort()[-max_chunks:][::-1]
    context = "\n\n".join(chunks[i] for i in top_indices)
    
    # Query Gemini API
    prompt = f"Question: {question}\n\nContext from document:\n{context}\n\nAnswer:"
    
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent",
        headers={"Content-Type": "application/json"},
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    
    # Extract and return answer
    response_json = response.json()
    
    # Check for error in response
    if "error" in response_json:
        return f"API Error: {response_json['error']['message']}"
    
    try:
        # Try to extract the answer from the response
        return response_json["candidates"][0]["content"]["parts"][0]["text"]
    except KeyError:
        # If the expected keys aren't found, return the full response for debugging
        return f"Unexpected API response format. Raw response: {response_json}"

def main():
    # Get inputs
    pdf_path = input("PDF path: ")
    api_key = input("Gemini API key: ")
    
    # Process PDF
    print("Processing PDF...")
    chunks = process_pdf(pdf_path)
    print(f"Ready! PDF split into {len(chunks)} chunks.")
    
    # Q&A loop
    while True:
        question = input("\nQuestion (or 'exit'): ").strip()
        if question.lower() == "exit":
            break
        if question:
            print("\nThinking...")
            print("\nAnswer:", query_pdf(question, chunks, api_key))

if __name__ == "__main__":
    main()