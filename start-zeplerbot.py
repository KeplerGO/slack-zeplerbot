"""A helpful robot for KeplerGO's Slack channel.

Inspired by the following tutorial:
https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
"""
import os
import time
import re
from slackclient import SlackClient

import emoji


# Instantiate Slack client
slack_client = SlackClient(os.environ.get('ZEPLER_TOKEN'))
# Bot's user ID in Slack: value is assigned after the bot connects
botid = None

# Constants
BOTNAME = 'zepler'
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


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
    """Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *help*."

    # Finds and executes the given command, filling in response
    response = "No."
    # This is where you start to implement more commands!
    if command.lower().startswith("help"):
        response = "No."

    if command.lower().startswith("give"):
        response = give(command)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def give(command):
    splt = command.split(" ")
    recipient = splt[1]
    reward = emoji.emojize(f":{splt[2]}:", use_aliases=True)
    if recipient.startswith("<@") and (emoji.emoji_count(reward) > 0):
        return f"{recipient} you deserved a {reward}"
    else:
        return "No."


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
