import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError

def summarize_with_gemini(text: str, external_prompt: str = None):
    """
    Simple reusable function:
    - Uses a single hardcoded API key
    - Uses a fixed Gemini model
    - Uses print() for status
    """

    # ✅ Hardcoded model and API key
    API_KEY = "YOUR_API_KEY_HERE"
    MODEL_NAME = "models/gemini-2.5-flash"

    print(f"MODEL_NAME: {MODEL_NAME}")
    print("Using a single hardcoded API key.")

    # ✅ Configure Gemini
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    # ✅ Prepare prompt
    final_prompt = external_prompt + "\n\n" + text if external_prompt else text

    try:
        print("⏳ Generating summary...")
        response = model.generate_content(final_prompt)

        if response and response.text:
            print("✅ Summary generated successfully.")
            return response.text
        else:
            print("⚠️ No response received.")
            return None

    except GoogleAPICallError as e:
        print(f"❌ API Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")

    return None

if __name__ == "__main__":
    summary = summarize_with_gemini(
    text="Machine learning enables systems to learn from data...",
    external_prompt="Simplify and explain given topic with real life examples."
)

print(summary)