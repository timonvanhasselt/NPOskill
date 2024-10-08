from ovos_utils import classproperty
from ovos_workshop.skills import OVOSSkill
from ovos_utils.log import LOG
from ovos_workshop.intents import IntentBuilder
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time

DEFAULT_SETTINGS = {
    "log_level": "WARNING"
}

class NPOStreamSkill(OVOSSkill):
    channels = ["NPO1", "NPO2", "NPO3", "NPO1 Extra", "NPO2 Extra", "NPO Politiek en Nieuws"]
    current_channel_index = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = None
        self.thread = None
        self.is_headless = False  # Stores the headless status

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(
            internet_before_load=False,
            network_before_load=False,
            gui_before_load=False,
            requires_internet=True,
            requires_network=False,
            requires_gui=False,
            no_internet_fallback=True,
            no_network_fallback=True,
            no_gui_fallback=True,
        )
    
    def initialize(self):
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        
        # Define play intents (non-headless)
        self.register_intent(IntentBuilder("PlayNPO1Intent").require("Play").require("NPO1"), self.handle_play_npo1)
        self.register_intent(IntentBuilder("PlayNPO2Intent").require("Play").require("NPO2"), self.handle_play_npo2)
        self.register_intent(IntentBuilder("PlayNPO3Intent").require("Play").require("NPO3"), self.handle_play_npo3)
        self.register_intent(IntentBuilder("PlayNPO1ExtraIntent").require("Play").require("NPO1 Extra"), self.handle_play_npo1_extra)
        self.register_intent(IntentBuilder("PlayNPO2ExtraIntent").require("Play").require("NPO2 Extra"), self.handle_play_npo2_extra)
        self.register_intent(IntentBuilder("PlayNPOPolitiekIntent").require("Play").require("Politiek"), self.handle_play_npo_politiek)
        
        # Define listen intents (headless)
        self.register_intent(IntentBuilder("ListenNPO1Intent").require("Listen").require("NPO1"), self.handle_listen_npo1)
        self.register_intent(IntentBuilder("ListenNPO2Intent").require("Listen").require("NPO2"), self.handle_listen_npo2)
        self.register_intent(IntentBuilder("ListenNPO3Intent").require("Listen").require("NPO3"), self.handle_listen_npo3)
        self.register_intent(IntentBuilder("ListenNPO1ExtraIntent").require("Listen").require("NPO1 Extra"), self.handle_listen_npo1_extra)
        self.register_intent(IntentBuilder("ListenNPO2ExtraIntent").require("Listen").require("NPO2 Extra"), self.handle_listen_npo2_extra)
        self.register_intent(IntentBuilder("ListenNPOPolitiekIntent").require("Listen").require("Politiek"), self.handle_listen_npo_politiek)
        
        # Define previous and next channel intents (for both headless and non-headless)
        self.register_intent(IntentBuilder("NextChannelIntent").require("Next"), self.handle_next_channel)
        self.register_intent(IntentBuilder("PreviousChannelIntent").require("Previous"), self.handle_previous_channel)

    def start_stream(self, channel, headless):
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/google-chrome"
        chrome_options.add_argument("--enable-features=UseOzonePlatform")
        chrome_options.add_argument("--ozone-platform=wayland")
        chrome_options.add_argument("--force-dark-mode")
        chrome_options.add_argument("--enable-features=WebUIDarkMode")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-fullscreen")
        chrome_options.add_argument("--disable-infobars")
        
        if headless:
            chrome_options.add_argument("--headless")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            url = f"https://npo.nl/start/live?channel={channel.replace(' ', '+')}"
            self.driver.get(url)
            play_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "bmpui-id-181"))
            )
            play_button.click()
            fullscreen_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "bmpui-id-173"))
            )
            fullscreen_button.click()
            while True:
                time.sleep(1)
        except Exception as e:
            self.log.info("Error during stream start: " + str(e))

    def stop(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.log.info("The stream has been stopped.")

    def start_new_stream(self, channel, headless):
        self.is_headless = headless  # Store the desired headless status
        if self.driver:
            self.stop()
        self.speak_dialog("start_channel", {"channel": channel})
        self.thread = threading.Thread(target=self.start_stream, args=(channel, headless))
        self.thread.start()

    # Play (non-headless) handlers
    def handle_play_npo1(self, message):
        self.current_channel_index = self.channels.index("NPO1")
        self.start_new_stream("NPO1", headless=False)

    def handle_play_npo2(self, message):
        self.current_channel_index = self.channels.index("NPO2")
        self.start_new_stream("NPO2", headless=False)

    def handle_play_npo3(self, message):
        self.current_channel_index = self.channels.index("NPO3")
        self.start_new_stream("NPO3", headless=False)

    def handle_play_npo1_extra(self, message):
        self.current_channel_index = self.channels.index("NPO1 Extra")
        self.start_new_stream("NPO1 Extra", headless=False)

    def handle_play_npo2_extra(self, message):
        self.current_channel_index = self.channels.index("NPO2 Extra")
        self.start_new_stream("NPO2 Extra", headless=False)

    def handle_play_npo_politiek(self, message):
        self.current_channel_index = self.channels.index("NPO Politiek en Nieuws")
        self.start_new_stream("NPO Politiek en Nieuws", headless=False)

    # Listen (headless) handlers
    def handle_listen_npo1(self, message):
        self.current_channel_index = self.channels.index("NPO1")
        self.start_new_stream("NPO1", headless=True)

    def handle_listen_npo2(self, message):
        self.current_channel_index = self.channels.index("NPO2")
        self.start_new_stream("NPO2", headless=True)

    def handle_listen_npo3(self, message):
        self.current_channel_index = self.channels.index("NPO3")
        self.start_new_stream("NPO3", headless=True)

    def handle_listen_npo1_extra(self, message):
        self.current_channel_index = self.channels.index("NPO1 Extra")
        self.start_new_stream("NPO1 Extra", headless=True)

    def handle_listen_npo2_extra(self, message):
        self.current_channel_index = self.channels.index("NPO2 Extra")
        self.start_new_stream("NPO2 Extra", headless=True)

    def handle_listen_npo_politiek(self, message):
        self.current_channel_index = self.channels.index("NPO Politiek en Nieuws")
        self.start_new_stream("NPO Politiek en Nieuws", headless=True)

    # Next and Previous handlers (both modes)
    def handle_next_channel(self, message):
        self.current_channel_index = (self.current_channel_index + 1) % len(self.channels)
        next_channel = self.channels[self.current_channel_index]
        self.start_new_stream(next_channel, headless=self.is_headless)  # Use stored headless status

    def handle_previous_channel(self, message):
        self.current_channel_index = (self.current_channel_index - 1) % len(self.channels)
        previous_channel = self.channels[self.current_channel_index]
        self.start_new_stream(previous_channel, headless=self.is_headless)  # Use stored headless status
