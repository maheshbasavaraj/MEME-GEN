# Plan for Improving the Lecture Meme Generator

This plan outlines the steps to refactor the codebase, enhance its features, and implement a fully functional meme generation pipeline.

### Phase 1: Code Cleanup & Refactoring
1.  **Remove Redundant Files:** Delete `Mem.py`, `voice_transcriber.py`, and `keyword_module.py` to eliminate confusion and outdated code.
2.  **Introduce Structured Logging:** Replace all `print()` statements in `main.py` with the standard Python `logging` module. This will provide clearer, filterable output (e.g., INFO, ERROR).
3.  **Clean Up `main.py`:** Remove unused imports and dependencies that are no longer needed after the file deletions.
4.  **Test:** Run the application to confirm that it still operates as before, transcribing and creating a placeholder meme, but with improved logging.

### Phase 2: Integrate Web Search into Meme Prompts
1.  **Connect the Logic:** Modify the `meme_generation_job` in `main.py` to correctly use the `formulate_meme_prompt` function, passing the summary and web search results to it.
2.  **Test:** Run the app and check the logs to ensure the generated meme prompt now incorporates context from the web search.

### Phase 3: Enhance Meme Text Formatting
1.  **Improve `add_text_to_image`:**
    *   Switch to a classic meme font (like Impact or Arial) and add a black outline for readability.
    *   Implement basic text wrapping to prevent text from overflowing.
    *   Position the text more appropriately (e.g., at the bottom of the image).
2.  **Test:** Inspect the newly generated placeholder meme to verify the text is clearer, better formatted, and well-positioned.

### Phase 4: Implement Real Meme Image Generation
1.  **Integrate a Meme API:** I will use the Imgflip API, which is perfect for this task. I will add code to:
    *   Fetch popular meme templates from the API.
    *   Use the generated prompt to add text to a chosen template.
    *   Download the final meme image.
2.  **Update Configuration:** You will need to add your Imgflip credentials to the `.env` file for the API integration to work.
3.  **Test:** Run the final version of the application. It should now generate a brand new, relevant meme from a popular template and save it to the `memes` folder.
