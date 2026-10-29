import nltk
import string
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np # For handling TF-IDF matrix results
import voice_transcriber as voice_transcriber_module

# --- NLTK resource download (same as before) ---
def download_nltk_resources():
    resources = [('corpora/stopwords', 'stopwords'), ('tokenizers/punkt', 'punkt')]
    for resource_path, resource_name in resources:
        try:
            nltk.data.find(resource_path)
        except nltk.downloader.DownloadError:
            nltk.download(resource_name)
download_nltk_resources()
# ---

# Global or class variable to store our "corpus" of lecture segments
# This would grow over time as the lecture progresses.
# For a single run, it might start empty or with some pre-loaded general texts.
lecture_corpus = []
MAX_CORPUS_SIZE = 100 # Limit the size to prevent it from growing indefinitely

def preprocess_text_for_tfidf(text):
    """
    Cleans and tokenizes text, returning a string of processed words.
    TF-IDF vectorizer often prefers to receive a string of space-separated tokens.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    try:
        words = nltk.word_tokenize(text)
    except Exception: # Fallback if NLTK tokenizer fails
        words = text.split()

    table = str.maketrans('', '', string.punctuation)
    stripped_words = [w.translate(table) for w in words]
    alphabetic_words = [word for word in stripped_words if word.isalpha() and len(word) > 1]

    stop_words_set = set(nltk.corpus.stopwords.words('english'))
    custom_stop_words = {"lecture", "okay", "right", "going", "like", "um", "uh", "actually", "basically", "gonna", "yeah"}
    stop_words_set.update(custom_stop_words)
    filtered_words = [word for word in alphabetic_words if word not in stop_words_set]

    return " ".join(filtered_words) # Return a single string of processed words

def extract_keywords_tfidf(current_text_segment, num_keywords=5):
    global lecture_corpus # Use the global corpus

    if not current_text_segment:
        return []

    processed_current_segment = preprocess_text_for_tfidf(current_text_segment)
    if not processed_current_segment: # If preprocessing results in empty string
        return []

    # Add the current processed segment to our growing corpus for future IDF calculations
    # For the *current* run, if the corpus is small, IDF might not be super meaningful yet.
    # But it will improve over time.
    temp_corpus = list(lecture_corpus) # Use a copy
    temp_corpus.append(processed_current_segment)

    # Initialize TF-IDF Vectorizer
    # - max_df: ignore terms that appear in more than X% of documents (too common)
    # - min_df: ignore terms that appear in less than Y documents (too rare, or absolute count)
    # - ngram_range: (1, 1) for single words, (1, 2) for unigrams and bigrams
    vectorizer = TfidfVectorizer(max_df=0.85, min_df=1, ngram_range=(1,1), stop_words=None) # We did stopwords manually

    try:
        # Fit the vectorizer on the current corpus (including the new segment)
        # and transform the current segment.
        # If temp_corpus has only 1 document, IDF will be constant, TF will dominate.
        # For better IDF, corpus should have multiple diverse (but related) documents.
        tfidf_matrix = vectorizer.fit_transform(temp_corpus)
    except ValueError as e:
        # This can happen if the vocabulary is empty after preprocessing (e.g., all stop words)
        print(f"TF-IDF Error: {e}. This might happen with very short or generic text.")
        # Fallback to simple frequency for this segment if TF-IDF fails
        from collections import Counter
        words = processed_current_segment.split()
        if not words: return []
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(num_keywords)]


    # The last row of the tfidf_matrix corresponds to our current_text_segment
    current_segment_tfidf_scores = tfidf_matrix[-1]

    # Get feature names (the words/tokens)
    feature_names = vectorizer.get_feature_names_out()

    # Create a list of (score, word)
    scored_keywords = []
    # current_segment_tfidf_scores is a sparse matrix row. Convert to dense array.
    # .A attribute converts a sparse matrix to a dense NumPy array.
    # [0] accesses the first (and only) row of this dense array.
    scores_array = current_segment_tfidf_scores.toarray()[0]

    for col_idx, score in enumerate(scores_array):
        if score > 0: # Only consider words present in the current document with a TF-IDF score
            scored_keywords.append((score, feature_names[col_idx]))

    # Sort by score in descending order
    scored_keywords.sort(key=lambda x: x[0], reverse=True)

    # Extract top N keywords
    top_keywords = [word for score, word in scored_keywords[:num_keywords]]

    # Update the main corpus (optional: manage its size)
    # This should happen outside this function, after a successful meme generation perhaps,
    # or on a timer, so that the corpus used for THIS segment's IDF isn't immediately
    # biased by itself if it's the first document.
    # For now, let's just show how to add it for the *next* iteration.
    # A better approach is to add `processed_current_segment` to `lecture_corpus`
    # *after* this function call, in the main loop.

    return top_keywords

def update_lecture_corpus(processed_segment):
    """Adds the processed segment to the global corpus and manages its size."""
    global lecture_corpus
    if processed_segment:
        lecture_corpus.append(processed_segment)
        if len(lecture_corpus) > MAX_CORPUS_SIZE:
            # Keep only the most recent segments (FIFO)
            lecture_corpus = lecture_corpus[-MAX_CORPUS_SIZE:]


# --- Example Usage ---
'''
#if __name__ == "__main__":
def keyword_extractor():
    sample_lecture_text_1 = """
    Alright class, today we're going to dive deep into Python programming,
    specifically focusing on data structures. Python offers several built-in
    data structures like lists, tuples, dictionaries, and sets. Understanding
    these Python data structures is crucial for efficient coding. We'll also
    touch upon algorithms that work with these structures. Python is great.
    """
    sample_lecture_text_2 = """
    Okay, so the next topic is quantum entanglement. It's a very, um, counter-intuitive
    concept in quantum mechanics where two particles become linked. Measuring a property
    of one particle instantaneously influences the property of the other, regardless of
    the distance separating them. Einstein famously called this 'spooky action at a
    distance'. This entanglement is key to quantum computing and quantum communication.
    """
    sample_lecture_text_3 = "Let's discuss Python again, Python features are amazing." # A short, somewhat repetitive text
    voice_transcriber() # Simulate running multiple times to build corpus
    # Simulate running multiple times to build corpus
    print("--- TF-IDF Keyword Extraction Test ---")

    # Run 1
    keywords1 = extract_keywords_tfidf(sample_lecture_text_1, num_keywords=3)
    print(f"\nText 1: '{sample_lecture_text_1[:50]}...'")
    print(f"Keywords (TF-IDF): {keywords1}")
    update_lecture_corpus(preprocess_text_for_tfidf(sample_lecture_text_1))
    print(f"Corpus size: {len(lecture_corpus)}")

    # Run 2
    keywords2 = extract_keywords_tfidf(sample_lecture_text_2, num_keywords=4)
    print(f"\nText 2: '{sample_lecture_text_2[:50]}...'")
    print(f"Keywords (TF-IDF): {keywords2}")
    update_lecture_corpus(preprocess_text_for_tfidf(sample_lecture_text_2))
    print(f"Corpus size: {len(lecture_corpus)}")

    # Run 3 (Now 'python' might have a lower IDF if it appeared in text 1)
    keywords3 = extract_keywords_tfidf(sample_lecture_text_3, num_keywords=3)
    print(f"\nText 3: '{sample_lecture_text_3[:50]}...'")
    print(f"Keywords (TF-IDF): {keywords3}")
    update_lecture_corpus(preprocess_text_for_tfidf(sample_lecture_text_3))
    print(f"Corpus size: {len(lecture_corpus)}")

    # Example of how TF-IDF might change results:
    # If "python" was in text 1, its IDF in run 3 (when text 1 is in corpus)
    # will be lower than a word like "amazing" if "amazing" hasn't appeared before.
    # So "amazing" might get a higher TF-IDF score than "python" in text 3,
    # even if "python" is more frequent in text 3 alone.'''
