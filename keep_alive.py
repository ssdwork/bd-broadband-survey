from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime

def wake_up():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # ব্রাউজারটি আড়ালে চলবে
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    #  স্ট্রিমলিট অ্যাপের লিংক
    current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    app_url = f"https://bd-broadband-survey-bcc.streamlit.app/?t={current_time}" 
    
    print(f"Visiting {app_url}...")
    driver.get(app_url)
    
    # ১০ সেকেন্ড অপেক্ষা  যাতে পেজটি পুরোপুরি লোড হয়
    time.sleep(10) 
    
    print("App is awake!")
    driver.quit()

if __name__ == "__main__":
    wake_up()
