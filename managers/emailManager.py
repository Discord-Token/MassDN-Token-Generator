import httpx
import logging
import random
import string
from managers.configStreamer import getValue

class emailManager:
    BASE = "http://45.42.45.172:6969/api/getInbox?email="
    DOMAINS = []

    def initalize():
        logging.getLogger("token_generator").info("Initializing emailManager...")
        emailManager.DOMAINS = ["sexyoxi.com", "blackmanhidingfromaperson.com"]
        logging.getLogger("token_generator").info("Successfully initialized emailManager!")

    def generateEmail():
        if len(emailManager.DOMAINS) == 0: raise Exception("emailManager was not initialized!")
        rndStr = "".join(random.choice(string.ascii_lowercase) for i in range(12))
        return f"{rndStr}@{random.choice(emailManager.DOMAINS)}"

    def receiveEmail(email):
        try:
            tries = 0
            while True:
                if tries == 75:
                    logging.getLogger("token_generator").ERROR("emailManager could not receive email within 75 tries!")
                    return None
                data = httpx.get(emailManager.BASE + email).text
                if len(data) != 0:
                    data = "https://click.discord.com/ls/click?upn=" + data
                    break
                tries += 1
            return data
        except TimeoutError:
            return emailManager.receiveEmail(email)
