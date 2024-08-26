import datetime
import os


def get_time_of_day() -> str:
    datetime_now = datetime.datetime.now()
    if 5 <= datetime_now.hour < 12:
        return "morning"
    elif 12 <= datetime_now.hour < 18:
        return "afternoon"
    else:
        return "evening"


def get_greeting_message() -> str:
    # Get the username from the environment variable
    username = os.getlogin(
    )  # or os.environ.get('USER') for Unix/Linux or os.environ.get('USERNAME') for Windows
    greeting = f"Good {get_time_of_day()}, {username}!"
    return greeting
