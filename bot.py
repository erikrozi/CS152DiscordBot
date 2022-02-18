# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
import modFlow
from report import Report
import ocr
import urllib.request

import pymongo
from pymongo import MongoClient

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'token.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']
    perspective_key = tokens['perspective']
    mongo_url = tokens.get('mongodb')

class ModBot(discord.Client):
    def __init__(self, key, mongo_url=None):
        intents = discord.Intents.default()
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None   
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports_in_progress = {} # Map from user IDs to the state of their report
        self.reports_by_user = {} # Map from user ID of who created the report to a list of their reports
        self.reports_about_user = {} # Map from user ID of who report is about to a list of reports against them
        self.perspective_key = key

        self.cluster = MongoClient(mongo_url) if mongo_url is not None else None
        self.db = self.cluster['discordbot'] if mongo_url is not None else None
        self.message_db = self.db['messages'] if mongo_url is not None else None
        self.userdata_db = self.db['userdata'] if mongo_url is not None else None

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")
        
        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from us 
        if message.author.id == self.user.id:
            return
        
        await self.send_to_mod(message) # Forwards message to mod channel
        await self.check_if_in_reporting(message) # Check if currently in reporting flow

    async def check_if_in_reporting(self, message):
        if message.content == "yo":
            await message.delete()
            return

        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id # User who is creating the report
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports_in_progress and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports_in_progress:
            self.reports_in_progress[author_id] = Report(self)
        
        # Let the report class handle this message; forward all the messages it returns to us
        responses = await self.reports_in_progress[author_id].handle_message(message)


        # If the report is cancelled, remove it from our reports_in_progress map
        if self.reports_in_progress[author_id].report_cancelled():
            self.reports_in_progress.pop(author_id)

        if self.reports_in_progress[author_id].report_complete():
            completed_report = self.reports_in_progress.pop(author_id)

            # Add completed report to other maps
            user_being_reported = completed_report.get_user_being_reported()
            user_being_reported_name = completed_report.get_user_being_reported_name()
            user_making_report = author_id
            user_making_report_name = message.author.name

            if user_making_report not in self.reports_by_user:
                self.reports_by_user[user_making_report] = []
            self.reports_by_user[user_making_report].append(completed_report)

            if user_being_reported not in self.reports_about_user:
                self.reports_about_user[user_being_reported] = []
            self.reports_about_user[user_being_reported].append(completed_report)

            take_post_down, response = modFlow.new_report_filed(completed_report, user_being_reported,
                                    user_being_reported_name, user_making_report, user_making_report_name,
                                     self.reports_by_user, self.reports_about_user,
                                       self.check_scores(self.eval_text(completed_report.get_message().content)))
            responses += [response]
            if take_post_down:
                await completed_report.get_message().delete()

        for r in responses:
            await message.channel.send(r)


    async def send_to_mod(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return 
        
        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')

        responses = []
        message_text = message.content

        # OCR on each image, currently the text gets appended to message content.
        for idx, file in enumerate(message.attachments):
            if not self.valid_image_url(file.url):
                continue

            save_name = str(message.id) + '_' + str(idx) + '_' + file.filename
            save_name = os.path.join("tmp", save_name)
            await file.save(save_name)

            img_text = ocr.process_image(save_name)
            message_text += " " + img_text
            if os.path.exists(save_name):
                os.remove(save_name)

        scores = self.eval_text(message_text)
        bad_things = self.check_scores(scores)
        
        if self.message_db is not None:
            await self.update_message_db(message, scores)

        if len(bad_things) > 0:
            take_post_down, response = modFlow.automatic_report(bad_things, message, self, self.reports_about_user, "",
                                                                message.author.name)
            responses += [response]
            if take_post_down:
                await message.delete()

        await mod_channel.send(self.code_format(json.dumps(scores, indent=2)))
        for r in responses:
            await message.channel.send(r)

    def valid_image_url(self, url):
        image_extensions = ['png', 'jpg', 'jpeg']
        for image_extension in image_extensions:
            if url.endswith('.' + image_extension):
                return True
        return False

    async def update_message_db(self, message, scores):
        entry = {
            "_id": message.id,
            "author_id": message.author.id,
            "content": message.content,
            "created_at": message.created_at
        }
        entry.update(scores)
        self.message_db.insert_one(entry)
        return

    def eval_text(self, text):
        '''
        Given a message, forwards the message to Perspective and returns a dictionary of scores.
        '''
        PERSPECTIVE_URL = 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze'

        url = PERSPECTIVE_URL + '?key=' + self.perspective_key
        data_dict = {
            'comment': {'text': text},
            'languages': ['en'],
            'requestedAttributes': {
                                    'SEVERE_TOXICITY': {}, 'PROFANITY': {},
                                    'IDENTITY_ATTACK': {}, 'THREAT': {},
                                    'TOXICITY': {}, 'FLIRTATION': {}
                                },
            'doNotStore': True
        }
        response = requests.post(url, data=json.dumps(data_dict))
        response_dict = response.json()

        scores = {}
        for attr in response_dict["attributeScores"]:
            scores[attr] = response_dict["attributeScores"][attr]["summaryScore"]["value"]

        return scores
    
    def code_format(self, text):
        return "```" + text + "```"

    def check_scores(self, scores):
        bad_things = []
        for key in scores:
            if scores[key] > .85:
                bad_things.append(key)

        return bad_things
            
        
client = ModBot(perspective_key, mongo_url)
client.run(discord_token)
