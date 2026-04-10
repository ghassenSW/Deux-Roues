import os
import time
import json
import PIL.Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the API key from the local environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = API_KEY)

# 2. Define the System Instruction (The "Brain" of the project)
from prompt import VERIFICATION_PROMPT

def verify_documents(image_paths, expected_values=None, additional_text=None):
    # Load images using PIL
    images = [PIL.Image.open(path) for path in image_paths]
    
    # We pass the system instruction in the config
    config = types.GenerateContentConfig(
        system_instruction=VERIFICATION_PROMPT,
        temperature=0,
        response_mime_type="application/json",
    )
    
    # Provide the simple request alongside the images
    # Output formatting rules are now securely stored inside the prompt.py (VERIFICATION_PROMPT)
    prompt_str = "Please verify these documents according to the system instructions."
    
    if additional_text:
        prompt_str += f"\n\nAdditional Instructions or Context:\n{additional_text}"
        
    if expected_values:
        prompt_str = f"Expected Values to verify against:\n{json.dumps(expected_values, ensure_ascii=False, indent=2)}\n\n" + prompt_str
        
    contents = [prompt_str] + images
    
    # Generate content using Gemini 3 Flash Preview with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate" in error_msg or "quota" in error_msg or "503" in error_msg or "unavailable" in error_msg or "demand" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    print(f"⚠️ API issue or High Demand (Code 429/503). Waiting {wait_time} seconds before retrying (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    raise e
            else:
                raise e

# --- Example Usage ---
if __name__ == "__main__":
    # Directory containing your image files
    test_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test1")
    if not os.path.exists(test_folder):
        print(f"Test folder not found: {test_folder}")
        print("Please create 'data/test1' and place test images there.")
    else:
        my_docs = [
            os.path.join(test_folder, f) 
            for f in os.listdir(test_folder) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
        ]
        
        # Example of expected values you can pass for testing
        example_expected_values = {
            "Nom Prénom": "Foulen Ben Foulen",
            "CIN Number": "12345678",
            "Numéro de Châssis": "12345ABC",
            "Cylindrée": "49 cm³"
        }
        
        print("Gemini is analyzing documents...")
        result_text = verify_documents(my_docs, expected_values=example_expected_values)
    
    try:
        # Parse the JSON string
        result_json = json.loads(result_text)
        
        # Save it to a JSON file in the same directory as this script
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_json, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Verification complete! Results successfully saved to: {output_file}")
        
    except json.JSONDecodeError:
        print("❌ Failed to parse the result as JSON. Raw model output was:")
        print(result_text)