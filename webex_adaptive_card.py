from flask import Flask, request
import requests
import json
import configparser
from api_interaction import *

# read variables from config
credential = configparser.ConfigParser()
credential.read('cred.test')


# Import credential

bearer_bot = credential['Webex']['WEBEX_TEAMS_TOKEN']
botEmail = credential['Webex']['WEBEX_BOT_EMAIL']

# WebhookUrl
webhookUrl = credential['Webex']['WEBEX_WEBHOOK_URL']

Meraki_API_KEY = credential['Webex']['Meraki_API_KEY']

headers_bot = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer_bot
}

app = Flask(__name__)

#### Functions

def createWebhook(bearer, webhookUrl):
    hook = True
    botWebhooks = send_webex_get("https://webexapis.com/v1/webhooks")["items"]
    for webhook in botWebhooks:
        if webhook["targetUrl"] == webhookUrl:
            hook = False
    if hook:
        dataWebhook = {
        "name": "Messages collab bot Webhook",
        "resource": "messages",
        "event": "created",
        "targetUrl": webhookUrl
        }
        dataWebhookCard = {
            "name": "Card Report collab bot Webhook",
            "targetUrl": webhookUrl,
            "resource": "attachmentActions",
            "event": "created"
        }
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhook)
        send_webex_post("https://webexapis.com/v1/webhooks/", dataWebhookCard)
    print("Webhook status: done")

def deleteWebHooks(bearer, webhookUrl):
    webhookURL = "https://webexapis.com/v1/webhooks/"
    botWebhooks = send_webex_get(webhookURL)["items"]
    for webhook in botWebhooks:
        send_webex_delete(webhookURL + webhook["id"])

def send_webex_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers_bot)
    else:
        request = requests.get(url, headers=headers_bot, params=payload)
    if js == True:
        if request.status_code == 200:
            try:
                r = request.json()
            except json.decoder.JSONDecodeError:
                print("Error JSONDecodeError")
                return("Error JSONDecodeError")
            return r
        else:
            print (request)
            return ("Error " + str(request.status_code))
    return request

def send_webex_delete(url, payload=None):
    if payload == None:
        request = requests.delete(url, headers=headers_bot)
    else:
        request = requests.delete(url, headers=headers_bot, params=payload)

def send_webex_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers_bot).json()
    return request

def postNotificationToPerson(reportText, personEmail):
    body = {
        "toPersonEmail": personEmail,
        "markdown": reportText,
        "text": "This text would be displayed by Webex Teams clients that do not support markdown."
        }
    send_webex_post('https://webexapis.com/v1/messages', body)

def postCard(personEmail):
    # open and read data from file as part of body for request
    with open("adaptiveCard.json", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    print("POST CARD TO ", personEmail)

def postCardDNAC(personEmail):
    # open and read data from file as part of body for request
    with open("adaptiveCardDNAC.json", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    print("POST CARD TO ", personEmail)

def postCardMeraki(personEmail):
    # open and read data from file as part of body for request
    with open("adaptiveCardMeraki.json", "r", encoding="utf-8") as f:
        data = f.read().replace('USER_EMAIL', personEmail)
    # Add encoding, if you use non-Latin characters
    data = data.encode("utf-8")
    request = requests.post('https://webexapis.com/v1/messages', data=data, headers=headers_bot).json()
    print("POST CARD TO ", personEmail)

@app.route('/', methods=['GET', 'POST'])
def webex_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        print("Webhook:")
        print(webhook)
        if webhook['resource'] == 'messages' and webhook['data']['personEmail'] != botEmail:
            result = send_webex_get('https://webexapis.com/v1/messages/{0}'.format(webhook['data']['id']))
            print("result messages", result)
            in_message = result.get('text', '').lower()
            print("in_message", in_message)
            if in_message.startswith('/hi'):
                personEmail = webhook['data']['personEmail']
                postNotificationToPerson('Hi', personEmail)
            elif in_message.startswith('/dnac'):
                postCardDNAC(webhook['data']['personEmail'])
            elif in_message.startswith('/post'):
                postCardMeraki(webhook['data']['personEmail'])
            else:
                postCard(webhook['data']['personEmail'])

        elif webhook['resource'] == 'attachmentActions':
            result = send_webex_get('https://webexapis.com/v1/attachment/actions/{}'.format(webhook['data']['id']))
            print("\n\n Result ", result)
            person = send_webex_get('https://webexapis.com/v1/people/{}'.format(result['personId']))
            personEmail = person["emails"][0]
            postNotificationToPerson("Bot received your answer", personEmail)
            if (result['inputs']['type'] == 'event_card'):
                responseText = "Your Email " + personEmail + "\n" + "Date in Adaptive Card: " + result['inputs']['date'] + "\n" + "Text in Adaptive Card: " + result['inputs']['input_text']
                postNotificationToPerson(responseText, personEmail)
            elif (result['inputs']['type'] == 'api_operation_card'):
                reportText = SimpleAPIoperation(dnac_url)
                postNotificationToPerson(reportText[1], personEmail)
                postNotificationToPerson(reportText[0], personEmail)
            elif (result['inputs']['type'] == 'api_operation_card_post'):
                reportText = merakiPostOperation(result['inputs']['admin_email'])
                postNotificationToPerson(reportText, personEmail)
            elif (result['inputs']['type'] == '3rd_party'):
                pass

        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"http://bit.ly/SparkBot-512x512\" alt=\"Webex Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\"></i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Please don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" \
                "<center><b>Generate meeting token <a href='/token'>/token</a></b></center>"
        return message


print("Start Bot")
deleteWebHooks(bearer_bot, webhookUrl)
createWebhook(bearer_bot, webhookUrl)