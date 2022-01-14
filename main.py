import base64
import httpx
import logging
import os
import random
import re
import requests
import secrets
import string
import threading
from managers.captchaManager import captchaManager
from managers.configStreamer import getValue
from managers.emailManager import emailManager
from managers.headerManager import headerManager
from managers.loggingFormatter import formatter
from requests.api import head
from websocket import create_connection

proxies = [line.rstrip("\n") for line in open("data/proxies.txt")]
names = [line.rstrip("\n") for line in open("data/names.txt")]

def getProxy():
    if len(proxies) == 0:
        return None
    proxy = random.choice(proxies)
    if len(proxy.split(":")) == 4:
        splitted = proxy.split(":")
        proxy = f"{splitted[2]}:{splitted[3]}@{splitted[0]}:{splitted[1]}"
    return "http://" + proxy

def generateToken():
    try:
        logging.getLogger("token_generator").info("Generating token...")
        if getValue("username") == "realistic":
            name = httpx.get("https://story-shack-cdn-v2.glitch.me/generators/username-generator?", proxies=getProxy()).json().get("data").get("name")
        elif "txt" in getValue("username"):
            name = random.choice(names)
        else:
            name = getValue("username").replace("<<rnd_str>>", secrets.token_urlsafe(4))
        email = emailManager.generateEmail()
        password = "".join(random.choice(string.ascii_letters) for _ in range(12))
        logging.getLogger("token_generator").info(f"Using username: {name}, email: {email}, password: {password}")
        client = httpx.Client(headers=headerManager.getClientHeaders(), timeout=30, proxies=getProxy())
        client.get("https://discord.com/")
        client.headers["locale"] = "en"
        client.headers["X-Fingerprint"] = client.get("https://discord.com/api/v9/experiments").json().get("fingerprint")
        payload = {"consent": True, "fingerprint": client.headers["X-Fingerprint"], "username": name, "captcha_key": None}
        req = client.post("https://discord.com/api/v9/auth/register", json=payload)
        if "retry_after" in req.text:
            logging.getLogger("token_generator").warning("Proxy is ratelimited, retrying...")
            return
        payload["captcha_key"] = captchaManager.getCaptcha()
        req = client.post("https://discord.com/api/v9/auth/register", json=payload)
        token = req.json().get("token")
        if token == None:
            logging.getLogger("token_generator").error("Failed to generate token. ")
            return None
        del client.headers["Origin"]
        client.headers["Authorization"] = token
        client.headers["Referer"] = "https://discord.com/channels/@me"
        tokenStatus = client.get("https://discord.com/api/v9/users/@me/library")
        if tokenStatus.status_code != 200:
            logging.getLogger("token_generator").error("Token locked!")
            with open("data/locked.txt", "a+") as f:
                f.write(f"{email}:{password}:{client.headers['Authorization']}\n")
                f.close()
            return None
        logging.getLogger("token_generator").info(f"Successfully generated token, changing email... ({token})")
        req = client.patch("https://discord.com/api/v9/users/@me", headers=headerManager.getEmailChangeHeaders(client.headers["Authorization"], client.headers["X-Fingerprint"]), json={"email": email, "password": password})
        if req.status_code == 403:
            logging.getLogger("token_generator").error("Token locked!")
            with open("data/locked.txt", "a+") as f:
                f.write(f"{email}:{password}:{client.headers['Authorization']}\n")
                f.close()
            return None
        logging.getLogger("token_generator").info("Successfully changed email!")
        verificationLink = emailManager.receiveEmail(email)
        link = verificationLink
        emailToken = requests.get(link).url.split("=")[1]
        logging.getLogger("token_generator").info(f"Got email token! {emailToken[:30]}...")
        emailData = client.post("https://discord.com/api/v9/auth/verify", json={"token": emailToken, "captcha_key": None}, headers=headerManager.verifyEmailHeaders())
        if emailData.status_code == 400:
            emailData = client.post("https://discord.com/api/v9/auth/verify", json={"token": emailToken, "captcha_key": captchaManager.getCaptcha()}, headers=headerManager.verifyEmailHeaders())
        client.headers["Authorization"] = emailData.json().get("token")
        logging.getLogger("token_generator").info("Email verified!")
        ws = create_connection("wss://gateway.discord.gg/?encoding=json&v=9&compress=zlib-stream")
        ws.send('{"op":2,"d":{"token":"' + client.headers['Authorization'] + '","capabilities":125,"properties":{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-GB","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36","browser_version":"91.0.4472.124","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":89709,"client_event_source":null},"presence":{"status":"online","since":0,"activities":[],"afk":false},"compress":false,"client_state":{"guild_hashes":{},"highest_last_message_id":"0","read_state_version":0,"user_guild_settings_version":-1}}}')
        ws.close()
        logging.getLogger("token_generator").info("Connected to WebSocket!")
        if getValue("avatar"):
            pic = str(base64.b64encode(client.get("https://picsum.photos/128/128", follow_redirects=True).content), "UTF-8")
            client.patch("https://discord.com/api/v9/users/@me", data='{"avatar":"data:image/png;base64,' + pic + '"}')
            logging.getLogger("token_generator").info("Changed avatar!")
        logging.getLogger("token_generator").info(f"Generated token! {client.headers['Authorization']}")
        with open("data/tokens.txt", "a+") as f:
            f.write(f"{email}:{password}:{client.headers['Authorization']}\n")
            f.close()
        return client.headers["Authorization"]
    except Exception as e:
        logging.getLogger("token_generator").error(e)
        pass

def generatorThread():
    while True:
        generateToken()

if __name__ == "__main__":
    os.system("color")
    log_level = logging.INFO
    logger = logging.getLogger("token_generator")
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter())
    logger.addHandler(ch)
    emailManager.initalize()
    logging.getLogger("token_generator").info(f"Preparing {getValue('threads')} thread(s)...")
    for i in range(getValue("threads")):
        threading.Thread(target=generatorThread).start()
