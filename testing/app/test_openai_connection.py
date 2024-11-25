import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def test_openai_connection():
    """
    Test connection to OpenAI API using the latest library interface.
    """
    # Retrieve the OpenAI API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set. Check your .env file.")
        return False

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Test chat completion
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello to the world!"}
            ]
        )

        # Access the assistant's reply from the response
        assistant_reply = response.choices[0].message.content
        print("OpenAI Response:", assistant_reply)

        return True

    except Exception as e:
        print(f"Failed to connect to OpenAI API: {e}")
        return False


if __name__ == "__main__":
    if test_openai_connection():
        print("Test passed: Successfully connected to OpenAI API.")
    else:
        print("Test failed: Unable to connect to OpenAI API.")
