import tweepy
import logging
import json
import time
import os
from predict import partypredict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def create_api():
    with open('twittercredentials.json') as data_file:
        data = json.load(data_file)

    consumer_key = data['consumerKey']
    consumer_secret = data['consumerSecret']
    access_token = data['accessTokenKey']
    access_token_secret = data['accessTokenSecret']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, 
        wait_on_rate_limit_notify=True)
    try:
        api.verify_credentials()
    except Exception as e:
        logger.error("Error creating API", exc_info=True)
        raise e
    logger.info("API created")
    return api

def write_progress(progress_id):
    f = open("chirpbot_progress.txt", "r")
    readid = int(f.read())
    if readid < progress_id:
        f = open("chirpbot_progress.txt", "w")
        f.write(str(progress_id))
        f.close()
        return progress_id
    return readid

def check_mentions(api, since_id):
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = write_progress(max(tweet.id, new_since_id))
        if tweet.in_reply_to_status_id is not None:
            continue
        logger.info(f"Answering to {tweet.user.name}")
        if not tweet.user.following:
            tweet.user.follow()
        twitterrequester = tweet.user.screen_name
        returneddata = partypredict(twitterrequester)
        tweetsreadtotal = returneddata["tweetsread"]
        predictions = returneddata["data"]
        cdu = predictions["Christlich Demokratische Union Deutschlands"] * 100
        afd = predictions["Alternative für Deutschland"] * 100
        spd = predictions["Sozialdemokratische Partei Deutschlands"] * 100
        fdp = predictions["Freie Demokratische Partei"] * 100
        dielinke = predictions["Die Linke"] * 100
        diegruenen = predictions["Bündnis 90/Die Grünen"] * 100
        piraten = predictions["Piratenpartei Deutschland"] * 100
        prettyresults = "\n⬛ CDU: " + str(round(cdu, 1)) + "%\n🟥 SPD: " + str(round(spd, 1)) + "%\n🟨 FDP: " + str(round(fdp, 1)) + "%\n🟥 Die Linke: " + str(round(dielinke, 1)) + "%\n🟩 Die Grünen: " + str(round(diegruenen, 1)) + "%\n🟧 Piratenpartei: " + str(round(piraten, 1)) + "%\n🟦 AfD: " + str(round(afd, 1)) + "%\n\nInsgesamt haben wir " + str(tweetsreadtotal) + " Tweets von dir analysiert."
        tweetstatus = "@" + str(twitterrequester) + " Deine Tweets stimmen so viel mit den den folgenden Parteien überein: " + str(prettyresults)
        with open('temp.txt', 'w') as t:
            t.write(tweetstatus)
            t.close()

        with open('temp.txt','r') as t:
            api.update_status(
                    status=t.read(),
                    in_reply_to_status_id=tweet.id,
                )
    return new_since_id

def main():
    api = create_api()
    since_id = write_progress(1)
    logger.info("Chirpbot started, last Tweet ID: " + str(since_id))
    while True:
        since_id = check_mentions(api, since_id)
        time.sleep(15)

if __name__ == "__main__":
    main()