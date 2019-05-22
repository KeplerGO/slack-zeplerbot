"""A helpful robot for KeplerGO's Slack channel.

Inspired by the following tutorial:
https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
"""
import os
import time
import re
from slackclient import SlackClient

import datetime
import random
import requests
import json
import emoji


# Instantiate Slack client as a global
slack_client = SlackClient(os.environ.get('ZEPLER_TOKEN'))
# Bot's user ID in Slack: value is assigned after the bot connects
botid = None
# Last restaurant request
last_restaurant_request = None

# Constants
BOTNAME = 'zepler'
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def post_message(channel, text, attachments=None):
    """Posts a message on a Slack channel."""
    print(f"#{channel}: {text}")
    return slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        attachments=attachments
    )


def parse_bot_commands(slack_events):
    """Given an event, returns (message, channel) if someone sends a message
    to our bot. Returns (None, None) otherwise.

    Parses a list of events coming from the Slack RTM API to find bot commands.
    If a bot command is found, this function returns a tuple of command and channel.
    If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == botid:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    """Executes bot commands."""
    if command.lower().startswith("give"):
        give(command, channel)
    elif command.lower().startswith("where"):
        where(command, channel)
    else:
        post_message(channel=channel, text="No.")


def give(command, channel):
    """Give something to someone."""
    attachments = None
    splt = command.replace(" a ", " ").split(" ")
    recipient = splt[1]
    reward = emoji.emojize(f":{splt[2]}:", use_aliases=True)
    if recipient.startswith("<@") and (emoji.emoji_count(reward) > 0):
        text = f"{recipient} you deserved a {reward}"
        if splt[2] == "dog":
            text = ""
            attachments = [{"title": f"dog for {recipient}", "image_url": random_dog_url()}]
    else:
        text = "No."
    post_message(channel=channel, text=text, attachments=attachments)


def random_dog_url():
    """Returns the random URL of an image of a good dog."""
    api_url = "https://dog.ceo/api/breeds/image/random"
    response = requests.get(api_url)
    if response.status_code == 200:
        js = json.loads(response.content.decode('utf-8'))
        return js['message']
    else:
        # Failsafe Labrador
        return "https://dcewboipbvgi2.cloudfront.net/cdn/farfuture/F3Jhqj1h8Lw_ZY8KFN4psInhN8vPekhOtFUYDskKWJs/mtime:1496942436/sites/default/files/styles/article_hero_image/public/Puppy_Dog_Labrador_Jerry.jpg"


def where(command, channel):
    """Give something to someone."""
    global last_restaurant_request
    seconds = 999
    if last_restaurant_request is not None:
        delta = datetime.datetime.now() - last_restaurant_request
        seconds = delta.seconds
    # Don't allow a restaurant to be recommended again within 45 seconds.
    if seconds < 45:
        text = "I'VE ALREADY BEEN ASKED. 😠"
    else:
        restaurant = random_restaurant()
        text = f"You will go to {restaurant}."
    post_message(channel=channel, text=text)
    last_restaurant_request = datetime.datetime.now()


def random_restaurant():
    """Returns the name of a random restaurant near Ames."""
    headers = {"Authorization": "Bearer " + os.environ.get('YELP_TOKEN')}
    restaurants = []
    lat, lon = 37.4121902, -122.0585327
    for offset in [0, 50]:  # Yelp will only give us 50 rows at a time.  Let's get 100.
        api_url = f"https://api.yelp.com/v3/businesses/search?latitude={lat}&longitude={lon}&radius=5000&open_now=true&price=1,2&categories=restaurants&sort_by=rating&limit=50&offset={offset}"
        response = requests.get(api_url, headers=headers)
        js = json.loads(response.content.decode('utf-8'))
        restaurants.extend(js['businesses'])
    names = list(set(["{} ({:.1f}⭐)".format(r['name'], r['rating']) for r in restaurants]))
    names.extend(['Mega Bites 😏', 'Space Bar 🚀'])
    return random.choice(names)


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("{} connected and running!".format(BOTNAME))
        # Read bot's user ID by calling Web API method `auth.test`
        botid = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
