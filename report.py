from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    REPORT_IDENTIFIED = auto()
    REPORT_CANCELLED = auto()

    START_OF_SPAM_BRANCH = auto()
    ABUSE_SPECIFIC_REPORT = auto()
    REPORT_COMPLETE = auto()
    AUTOMATED_REPORT = auto()

# The types of reports that a user can submit.
class ReportType(Enum):
    HARASSMENT_BULLYING = auto()
    SPAM = auto()
    HATE_SPEECH = auto()
    OTHER = auto()
    THREATENING_DANGEROUS = auto()
    SEXUAL = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    SPAM_FRAUD_KEYWORD = "1"
    HATE_SPEECH_KEYWORD = "2"
    HARASSMENT_BULLYING_KEYWORD = "3"
    THREATENING_DANGEROUS_KEYWORD = "4"
    SEXUAL_KEYWORD = "5"
    OTHER_KEYWORD = "6"


    SPAM_OPTION_ONE_KEYWORD = "1"
    SPAM_OPTION_TWO_KEYWORD = "2"



    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.report_type = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_CANCELLED
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            reply = "Help us understand the problem with this message."
            reply += "Which of the following categories best describes this message:\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Spam/fraud\n2: Hate speech\n3: Harassment/bullying\n4: Threatening/dangerous behavior\n"
            reply += "5: Sexual offensive content\n6: Other\n"
            self.message = message
            self.report_type = ReportType.OTHER  # This is just temporary for testing.
            self.state = State.REPORT_IDENTIFIED # TODO: this is just temporary for testing. This should instead be REPORT_IDENTIFIED, and later is set to REPORT_COMPLETED.
            return [reply]

        if message.content == self.SPAM_FRAUD_KEYWORD:
            self.report_type = ReportType.SPAM
            self.state = State.START_OF_SPAM_BRANCH
            self.spam_branch()

            # reply = "Please elaborate how this message is spam/fraud.\n\n"
            # reply += "Reply with the number corresponding to the correct reason.\n\n"
            # reply += "1: This message is from a fake/spam account.\n"
            # reply += "2: This account is repeatedly sending you unwanted messages."
            # return [reply]

        # if message.content == self.SPAM_OPTION_ONE_KEYWORD:
        #     reply = "Thank you for reporting this. Our moderation team with investigate this account.\n"
        #     return [reply]

        if message.content == self.HATE_SPEECH_KEYWORD:
            self.report_type = ReportType.HATE_SPEECH
            reply = "Who is the user targeting?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Me\n"
            reply += "2: Someone else\n"
            reply += "3: A group of people\n"
            print(reply)

        if message.content == self.HARASSMENT_BULLYING_KEYWORD:
            self.report_type = ReportType.HARASSMENT_BULLYING
            reply = "Who is the user targeting?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Me\n"
            reply += "2: Someone else\n"
            reply += "3: A group of people\n"
            return [reply]

        if message.content == self.THREATENING_DANGEROUS_KEYWORD:
            self.report_type = ReportType.THREATENING_DANGEROUS
            reply = "Who is the being threatened or in danger?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: The user is threatening me\n"
            reply += "2: The user is threatening or appears to be at risk of harming themselves\n"
            reply += "3: The user is threatening to or appears to be at risk of harming others\n"
            return [reply]

        if message.content == self.SEXUAL_KEYWORD:
            self.report_type = ReportType.SEXUAL
            reply = "Is this child sexual abuse material?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Yes"
            reply += "2: No"
            return [reply]

        if message.content == self.OTHER_KEYWORD:
            self.report_type = ReportType.OTHER
            reply = "TODO: This would take you to the final option about other harmful messages you'd like to report"
            # if yes, call handle_message
            return [reply]

        # if self.report_type == ReportType.SPAM:
        #     reply = ""
        #     if message.content == self.SPAM_OPTION_ONE_KEYWORD:
        #         reply += "Thank you for reporting this. Our moderation team will investigate this account.\n\n"
        #         reply += "Would you like to block or mute this account?\n"
        #     elif message.content == self.SPAM_OPTION_TWO_KEYWORD:
        #         reply += "Would you like to block or mute this account?\n"
        #     self.state = State.REPORT_COMPLETE #NOTE: This is a placeholder! The final report won't finish here
        #     return [reply]

        return []

    def spam_branch(self, message):
        if self.state == State.START_OF_SPAM_BRANCH:
            # 2 Prompt Spam (2PSpam)
            reply = "Please elaborate how this message is spam/fraud.\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: This message is from a fake/spam account.\n"
            reply += "2: This account is repeatedly sending you unwanted messages."
            return [reply]

        # 2 Response Spam (2RS)
        if message.content == self.SPAM_OPTION_ONE_KEYWORD:
            reply = "Thank you for reporting this. Our moderation team will investigate this account.\n"
            return [reply]
        elif message.content == self.SPAM_OPTION_TWO_KEYWORD:
            reply = "We're sorry to hear that.\n"
            return [reply]

        reply = "Would you like to block or mute this account?\n"
        reply += "1: Mute\n"
        reply += "2: Block\n"
        return [reply]


    def get_user_being_reported(self):
        return self.message.author.id

    def report_cancelled(self):
        return self.state == State.REPORT_CANCELLED

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE

    def get_report_type(self):
        return self.report_type

    def get_message(self):
        return self.message

    

