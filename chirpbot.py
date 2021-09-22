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
    if int(f.read()) > int(progress_id):
        f = open("chirpbot_progress.txt", "w")
        f.write(progress_id)
        f.close()
    f = open("chirpbot_progress.txt", "r")
    return max(int(f.read()), int(progress_id))

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = write_progress(max(tweet.id, new_since_id))
        if tweet.in_reply_to_status_id is not None:
            continue
        #if any(keyword in tweet.text.lower() for keyword in keywords):
        logger.info(f"Answering to {tweet.user.name}")

        if not tweet.user.following:
            tweet.user.follow()
        twitterrequester = tweet.user.screen_name
        returneddata = partypredict(twitterrequester)
        predictions = returneddata["data"]
        cdu = int(predictions["Christlich Demokratische Union Deutschlands"]) * 100
        afd = int(predictions["Alternative für Deutschland"]) * 100
        spd = int(predictions["Sozialdemokratische Partei Deutschlands"]) * 100
        fdp = int(predictions["Freie Demokratische Partei"]) * 100
        dielinke = int(predictions["Die Linke"]) * 100
        diegruenen = int(predictions["Bündnis 90/Die Grünen"]) * 100
        piraten = int(predictions["Piratenpartei Deutschland"]) * 100
        prettyresults = "CDU: " + str(cdu[0:3]) + "SPD: " + str(spd[0:3]) + "FDP: " + str(fdp[0:3]) + "Die Linke: " + str(dielinke[0:3]) + "Die Grünen: " + str(diegruenen[0:3]) + "Piratenpartei: " + str(piraten[0:3]) + "AFD: " + str(afd[0:3])
        print(prettyresults)
        tweetstatus = "@" + str(twitterrequester) + " deine Übereinstimmung mit den folgenden Parteien (%): " + str(prettyresults)
        api.update_status(
                status=tweetstatus,
                in_reply_to_status_id=tweet.id,
            )
    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(15)

if __name__ == "__main__":
    main()