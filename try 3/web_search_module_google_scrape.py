# --- web_search_module_google_scrape.py ---
from googlesearch import search
import time
import random

# --- Configuration ---
# Headers to make requests look more like a browser
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def perform_web_search_google_scrape(keywords, num_results=3, lang="en", pause_time=2.0):
    """
    Performs a web search using the googlesearch-python library.

    Args:
        keywords (list): A list of keyword strings.
        num_results (int): The desired number of search results.
        lang (str): Language for the search.
        pause_time (float): Time to pause between requests to avoid blocking.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              information about a search result (e.g., title, link).
              Returns an empty list if an error occurs or no results are found.
    """
    if not keywords:
        print("No keywords provided for web search. Skipping.")
        return []

    query = " ".join(keywords)
    # Consider adding "meme" or "funny" to the query for better meme context
    # query_for_meme = f"{' '.join(keywords)} meme"
    print(f"Performing Google scrape search for: '{query}'")

    processed_results = []
    try:
        # The library handles user agents internally but being explicit can sometimes help.
        # However, googlesearch library itself tries to rotate user agents.
        # The `num_results` parameter in search() is how many results to fetch in total.
        # The `stop` parameter is how many results to yield.
        # The `pause` parameter adds a delay.
        count = 0
        for result_url in search(query, num_results=num_results, lang=lang):
            # The 'googlesearch' library primarily returns URLs.
            # Getting titles and snippets would require fetching each URL and parsing its content,
            # which adds complexity and more requests (increasing block risk).
            # For simplicity, we'll just return the URL and a placeholder title.
            processed_results.append({
                "title": f"Search Result for '{query}'", # Placeholder title
                "link": result_url,
                "snippet": "Snippet not available via this simple scraping method.", # Placeholder
                "source": "google_scrape"
            })
            count += 1
            if count >= num_results:
                break
        
        if not processed_results:
            print(f"No results found for '{query}' using googlesearch-python.")

    except Exception as e:
        print(f"Error during Google scrape search with googlesearch-python: {e}")
        print("This could be due to network issues or Google blocking the request (e.g., CAPTCHA).")
        return []

    return processed_results

# --- Example Usage (for standalone testing of this module) ---
if __name__ == "__main__":
    print("--- Google Scrape Web Search Module Test (using googlesearch-python) ---")

    sample_keywords_1 = ["python programming", "data structures"]
    results_1 = perform_web_search_google_scrape(sample_keywords_1, num_results=2)
    print(f"\nSearch results for: {sample_keywords_1}")
    if results_1:
        for i, res in enumerate(results_1):
            print(f"  Result {i+1}:")
            print(f"    Title: {res.get('title')}")
            print(f"    Link: {res.get('link')}")
    else:
        print("  No results found or error occurred.")

    # Add a delay before the next search to be respectful
    time.sleep(5)

    sample_keywords_2 = ["funny cat programmer meme"]
    results_2 = perform_web_search_google_scrape(sample_keywords_2, num_results=1)
    print(f"\nSearch results for: {sample_keywords_2}")
    if results_2:
        for i, res in enumerate(results_2):
            print(f"  Result {i+1}: Link: {res.get('link')}")
    else:
        print("  No results found or error occurred.")