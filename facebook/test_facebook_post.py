import os
import sys
import requests
from dotenv import load_dotenv
load_dotenv()
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
def post_to_facebook(message: str, scheduled_time: int | None = None):
    """
    Posts a message to the Facebook Page.
    If scheduled_time is given (as a Unix timestamp), the post is scheduled
    for the future instead of publishing immediately.
    """
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }
    if scheduled_time:
        payload["published"] = "false"
        payload["scheduled_publish_time"] = scheduled_time
    response = requests.post(url, data=payload)
    result = response.json()
    if response.status_code == 200 and "id" in result:
        print("✅ Post successful!")
        print("Post ID:", result["id"])
    else:
        print("❌ Post failed.")
        print("Error:", result)
        sys.exit(1)  # ye line GitHub Actions ko batati hai ke run FAIL hua hai
    return result
if __name__ == "__main__":
    # Test 1: Multi-line post with hashtags (like Content Engine output)
    test_message = (
        "Life's fleeting, what's your timeout?\n\n"
        "Jake Knapp, the inventor of the Time Box method, reminds us that "
        "our time is limited. How we choose to spend it defines who we become.\n\n"
        "What's your strategy for making time count?\n\n"
        "#TimeManagement #ProductivityHacks #MindfulnessMatters #LifeDesign #Focus"
    )
    print("Sending formatted test post...")
    post_to_facebook(test_message)
