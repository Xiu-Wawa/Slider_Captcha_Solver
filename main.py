from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import base64
import tempfile
import time
import requests
import re

from matplotlib import pyplot as plt
import cv2

# CONFIGURATION
URL = "https://gt4.geetest.com/demov4/slide-popup-en.html"

# LOCATORS
# CAPTCHA_IFRAME_LOCATOR = '//iframe[@title="DataDome CAPTCHA"]'
SLIDER_BUTTON_LOCATOR = "//div[starts-with(@class, 'geetest_btn_')]/div"
CAPTCHA_BG_LOCATOR = "//div[starts-with(@class, 'geetest_bg_') and contains(@style, 'background-image: url')]"
CAPTCHA_PIECE_LOCATOR = "//div[starts-with(@class, 'geetest_slice_bg_') and contains(@style, 'background-image: url')]"

# FUNCTIONS
def configure_browser():
    """
    Configures the Chrome WebDriver with options for fake user-agents and headless browsing.
    Returns:
        WebDriver: Configured WebDriver instance.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def save_base64_image(base64_data):
    """
    Saves a base64-encoded image to a temporary file.
    Args:
        base64_data (str): Base64-encoded image data.
    Returns:
        str: Path to the saved temporary image file.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    with open(temp_file.name, "wb") as file:
        file.write(base64.b64decode(base64_data))
    return temp_file.name

def drag_slider(action, slider_button, x_offset):
    """
    Simulates dragging the slider button to the required offset.
    Args:
        action (ActionChains): Selenium ActionChains instance.
        slider_button (WebElement): Slider button element.
        x_offset (int): X-coordinate offset for the slider.
    """
    action.click_and_hold(slider_button).move_by_offset(x_offset, 0).release().perform()
    print(f"Slider dragged to offset {x_offset}.")

def save_debug_screenshot(base64_data, filename):
    """
    Saves a base64-encoded screenshot to a file for debugging purposes.
    Args:
        base64_data (str): Base64-encoded screenshot data.
        filename (str): Filename for saving the image.
    """
    with open(filename, "wb") as file:
        file.write(base64.b64decode(base64_data))
    print(f"Saved screenshot to {filename}.")

def opencv():
    # Read the background and template images
    img = cv2.imread('example/demo_bg.png', cv2.IMREAD_GRAYSCALE)  # Background image in grayscale
    template = cv2.imread('example/demo_piece.png', cv2.IMREAD_GRAYSCALE)  # Template in grayscale
    img2 = img.copy()  # Copy of the background image for later use
    
    # Get dimensions of the template
    w = template.shape[1]
    h = template.shape[0]
    
    # Normalize intensity values for consistency (optional)
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    template = cv2.normalize(template, None, 0, 255, cv2.NORM_MINMAX)
    
    # Apply edge detection for improved accuracy
    img_edges = cv2.Canny(img, 50, 150)  # Adjust thresholds for optimal edge detection
    template_edges = cv2.Canny(template, 50, 150)
    
    # Methods for template matching
    methods = ['cv2.TM_CCOEFF']  # Use only one method for this demonstration
    
    for meth in methods:
        img_to_match = img_edges.copy()  # Use the edge-detected image for matching
        method = eval(meth)  # Convert method name string to actual cv2 method
        
        # Apply template matching
        res = cv2.matchTemplate(img_to_match, template_edges, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        # Determine the top-left corner of the match
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc
        
        # Calculate the bottom-right corner
        bottom_right = (top_left[0] + w, top_left[1] + h)
        
        # Draw a rectangle around the matched region on the original image
        cv2.rectangle(img2, top_left, bottom_right, (0, 0, 255), 2)
        
        # Print the result
        print("top_left =", top_left)
        
        # Plot the matching results and detected region
        plt.figure(figsize=(10, 5))
        plt.subplot(121), plt.imshow(res, cmap='gray')
        plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
        plt.subplot(122), plt.imshow(img2, cmap='gray')
        plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
        plt.suptitle(meth)
        plt.show()
        
        break  # Stop after the first method for demonstration
    
    return top_left

def save_image_from_url(image_url, filename='downloaded_image.png'):
    """
    Downloads and saves the image from the provided URL.

    Args:
        image_url (str): The URL of the image to download.
        filename (str): The filename to save the image as (default is 'downloaded_image.png').  

    Returns:
        bool: True if the image was successfully downloaded and saved, False otherwise.
    """
    image_url = re.search(r'url\(["\']?(https?://[^"\']+)["\']?\)', image_url)
    if not image_url:
        print("Image URL not found in the provided style.")
        return False
    image_url = image_url.group(1)  # Extract the actual URL
    try:
        # Send an HTTP request to fetch the image
        image_response = requests.get(image_url)

        # Check if the request was successful (status code 200)
        if image_response.status_code == 200:
            # Open the file in write-binary mode and save the image content
            with open(filename, 'wb') as file:
                file.write(image_response.content)
            print(f"Image successfully downloaded and saved as {filename}.")
            return True
        else:
            print(f"Failed to download the image. Status code: {image_response.status_code}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


# MAIN SCRIPT
if __name__ == "__main__":
    browser = configure_browser()
    try:
        browser.get(URL)
        action = ActionChains(browser)
        time.sleep(1)

        browser.find_element(By.XPATH, '//div[@aria-label="Click to verify"]').click()
        time.sleep(2)

        # Wait until the CAPTCHA background and piece images are available
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, CAPTCHA_BG_LOCATOR)))
        img_captcha_bg = browser.find_element(By.XPATH, CAPTCHA_BG_LOCATOR).get_attribute('style')
        img_captcha_piece = browser.find_element(By.XPATH, CAPTCHA_PIECE_LOCATOR).get_attribute('style')

        # Save the CAPTCHA images
        save_image_from_url(img_captcha_bg, 'example/demo_bg.png')
        save_image_from_url(img_captcha_piece, 'example/demo_piece.png')

        x_offset = opencv()  # Perform template matching to find the x offset
        x_offset = x_offset[0]  # Extract the x offset

        # Drag the slider to the required position
        slider_button = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, SLIDER_BUTTON_LOCATOR)))
        drag_slider(action, slider_button, x_offset)

        # Wait to ensure the captcha process is completed
        time.sleep(5)
        print("Captcha completed successfully.")
    finally:
        browser.quit()
