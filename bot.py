# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report

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


class ModBot(discord.Client):
    def __init__(self, key):
        intents = discord.Intents.default()
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None   
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports_in_progress = {} # Map from user IDs to the state of their report
        self.reports_by_user = {} # Map from user ID of who created the report to a list of their reports
        self.reports_about_user = {} # Map from user ID of who report is about to a list of reports against them
        self.perspective_key = key

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
        for r in responses:
            await message.channel.send(r)

        # If the report is cancelled, remove it from our reports_in_progress map
        if self.reports_in_progress[author_id].report_cancelled():
            self.reports_in_progress.pop(author_id)

        if self.reports_in_progress[author_id].report_complete():
            completed_report = self.reports_in_progress.pop(author_id)

            # Add completed report to other maps
            user_being_reported = completed_report.get_user_being_reported()
            user_making_report = author_id

            if user_making_report not in self.reports_by_user:
                self.reports_by_user[user_making_report] = []
            self.reports_by_user[user_making_report].append(completed_report)

            if user_being_reported not in self.reports_about_user:
                self.reports_about_user[user_being_reported] = []
            self.reports_about_user[user_being_reported].append(completed_report)


    async def send_to_mod(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return 
        
        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')

        scores = self.eval_text(message)
        await mod_channel.send(self.code_format(json.dumps(scores, indent=2)))

    def eval_text(self, message):
        '''
        Given a message, forwards the message to Perspective and returns a dictionary of scores.
        '''
        PERSPECTIVE_URL = 'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze'

        url = PERSPECTIVE_URL + '?key=' + self.perspective_key
        data_dict = {
            'comment': {'text': message.content},
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
            
        
client = ModBot(perspective_key)
client.run(discord_token)