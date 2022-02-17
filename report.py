from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    REPORT_IDENTIFIED = auto()
    REPORT_CANCELLED = auto()
    START_OF_SPAM_BRANCH = auto()
    EXIT_ABUSE_BRANCH = auto()
    FINAL_PROMPT = auto()
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
    SPAM_OPTION_ONE_KEYWORD = "1a"
    SPAM_OPTION_TWO_KEYWORD = "1b"
    END_REPORT_KEYWORD = "No"
    SUBMIT_ANOTHER_REPORT_KEYWORD = "Yes"
    MUTE_KEYWORD = "Mute"
    BLOCK_KEYWORD = "Block"

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
            reply = "Please elaborate how this message is spam/fraud.\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1a: This message is from a fake/spam account.\n"
            reply += "1b: This account is repeatedly sending you unwanted messages.\n"
            self.report_type = ReportType.SPAM
            self.state = State.START_OF_SPAM_BRANCH
            return [reply]

        if self.state == State.START_OF_SPAM_BRANCH:
            if message.content == self.SPAM_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this account.\n\n"
                reply += "Would you like to block or mute this account?\n"
                reply += "1: Mute\n"
                reply += "2: Block\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.SPAM_OPTION_TWO_KEYWORD:
                reply = "We're sorry to hear that.\n"
                reply += "Would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]


        if message.content == self.HATE_SPEECH_KEYWORD:
            self.report_type = ReportType.HATE_SPEECH
            reply = "Who is the user targeting?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Me\n"
            reply += "2: Someone else\n"
            reply += "3: A group of people\n"
            return [reply]

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

        if self.state == State.EXIT_ABUSE_BRANCH:
            reply = "Are there other harmful messages from this user or similar harmful messages from other users that " \
                    "you'd also like to report?\n"
            reply += "Please respond with: 'Yes' or 'No'"
            self.state = State.FINAL_PROMPT
            return [reply]

        if self.state == State.FINAL_PROMPT:
            self.state = State.REPORT_COMPLETE
            if message.content == self.END_REPORT_KEYWORD:
                reply = "Thank you for taking the time to report this. We know that interacting with this content can" \
                        " be harmful. Here are some mental health resources for you: <NOTE PUT LINKS HERE>\n"
                return[reply]
            elif message.content == self.SUBMIT_ANOTHER_REPORT_KEYWORD:
                reply = "Please say 'report' to continue reporting the message(s).\n"
                return [reply]
        return []

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

    

