import os
import requests
import json
import csv
import datetime

from os.path import join, dirname
from dotenv import load_dotenv

from slack_bolt import App

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

forecast_url = "https://weather.tsukumijima.net/api/forecast/city/130010"
train_url = "https://tetsudo.rti-giken.jp/free/delay.json"

bolt_app = App(
    token = os.environ.get("XOXB_TOKEN"),
    signing_secret = os.environ.get("SIGNING_SECRET")
)

@bolt_app.message("天気")
def message_forecast(message, say):
    r = requests.get(forecast_url)
    json = r.json()

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": json["title"]
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*更新時刻:*\n" + json["publicTimeFormatted"]
                },
                {
                    "type": "mrkdwn",
                    "text": "*計測地点:*\n" + json["publishingOffice"]
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*日時:*\n" + json["forecasts"][0]["date"]
                },
                {
                    "type": "mrkdwn",
                    "text": "*天気:*\n" + json["forecasts"][0]["telop"]
                },
                {
                    "type": "mrkdwn",
                    "text": "*風向:*\n" + json["forecasts"][0]["detail"]["wind"] + json["forecasts"][0]["detail"]["wave"]
                },
                {
                    "type": "mrkdwn",
                    "text": "*最高気温:*\n" + str(json["forecasts"][0]["temperature"]["max"]["celsius"])
                },
                {
                    "type": "mrkdwn",
                    "text": "*最低気温:*\n" + str(json["forecasts"][0]["temperature"]["min"]["celsius"])
                },
            ]
        }
    ]
    say(
        blocks=blocks,
        text=json["title"]
    )

@bolt_app.message("運行情報")
def message_train(message, say):
    r = requests.get(train_url)
    json = r.json()

    blocks = [
        {
            "type": "section",
            "text":
            {
                "type": "plain_text",
                "text": is_traindelayed(json, "中央線快速電車")
            },
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": is_traindelayed(json, "中央･総武各駅停車")
            },
        }
    ]
    say(
        blocks=blocks,
        text="運行情報"
    )


def is_traindelayed(list, name):
    for item in list:
        if name in item.values():
            return f"{name} が遅延しています．詳しくは JR 東日本のホームページをご覧ください．"
    return f"現在，{name} に遅延情報はありません．"

@bolt_app.shortcut("modal_checkin")
def modal_checkin(ack, body, client):
    ack()
    view = {
        "type": "modal",
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "title": {
            "type": "plain_text",
            "text": "Laboratory check-in",
            "emoji": True
        },
        "blocks": [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "研究室の入退室管理システムです．入退室を打刻する場合，以下にチェックしてください．"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "入室",
                            "emoji": True
                        },
                        "action_id": "checkin"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "退室",
                            "emoji": True
                        },
                        "action_id": "checkout"
                    }
                ]
            }
        ]
    }
    client.views_open(trigger_id = body['trigger_id'], view=view)

@bolt_app.action("checkin")
def modal_checkin_update(ack, body, client):
    ack()
    dt_now = datetime.datetime.now()
    date = dt_now.strftime("%Y/%m/%d %H:%M:%S")
    user = body['user']['username']

    data = ["checkin", user, date]
    with open("checkin.csv", "a") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(data)

    client.users_profile_set(
        token = os.environ.get("XOXP_TOKEN"),
        user = body['user']['id'],
        profile = {
            "status_text": "在室",
            "status_emoji": ":office:",
            "status_expiration": 0
        }
    )

    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Laboratory check-in",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "入室を記録しました．",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*入室*\n" + date
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*ユーザ名*\n" + user
                    },
                ]
            }
        ]
    }

    client.views_update(
        view_id = body['view']['id'],
        hash = body['view']['hash'],
        view = view
    )

@bolt_app.action("checkout")
def modal_checkout_update(ack, body, client):
    ack()
    dt_now = datetime.datetime.now()
    date = dt_now.strftime("%Y/%m/%d %H:%M:%S")
    user = body['user']['username']
    print(body['user'])

    data = ["checkout", user, date]
    with open("checkin.csv", "a") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(data)

    client.users_profile_set(
        token = os.environ.get("XOXP_TOKEN"),
        user = body['user']['id'],
        profile = {
            "status_text": "帰宅",
            "status_emoji": ":house:",
            "status_expiration": 0
        }
    )

    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Laboratory check-in",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "退室を記録しました．",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*退室*\n" + date
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*ユーザ名*\n" + user
                    },
                ]
            }
        ]
    }

    client.views_update(
        view_id = body['view']['id'],
        hash = body['view']['hash'],
        view = view
    )

# 本番環境用，flask で実行する．

from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler

app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == '__main__':
    app.run()
