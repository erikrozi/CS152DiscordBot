from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    AWAITING_ABUSE_TYPE = auto()
    REPORT_CANCELLED = auto()
    REPORT_COMPLETE = auto()

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
    SPAM_FRAUD_KEYWORD = "spam/fraud"
    HATE_SPEECH_KEYWORD = "hate speech"
    HARASSMENT_BULLYING_KEYWORD = "harassment/bullying"
    THREATENING_DANGEROUS_KEYWORD = "threatening/dangerous behavior"
    SEXUAL_KEYWORD = "sexual offensive content"
    OTHER_KEYWORD = "other"

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
            self.message = message
            self.report_type = ReportType.OTHER  # This is just temporary for testing.
            self.state = State.MESSAGE_IDENTIFIED # TODO: this is just temporary for testing. This should instead be REPORT_IDENTIFIED, and later is set to REPORT_COMPLETED.
            reply = "Help us understand the problem with this message."
            return[reply]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            reply = "Which of the following categories best describes this message:\n"
            reply += "'spam/fraud'\n'hate speech'\n'harassment/bullying'\n'threatening/dangerous behavior'\n"
            reply += "'sexual offensive content'\n'other'\n"
            self.state = State.AWAITING_ABUSE_TYPE
            # TODO: first step should be asking user what type of harassment it is
            # TODO: Based on their answer, then update self.report_type
            return [reply]

        if self.state == State.AWAITING_ABUSE_TYPE:
            # TODO: get the user's input and work with that
            # testing 1 abuse type
            if message.content == self.SPAM_FRAUD_KEYWORD:
                reply = "TODO: This would be the start of the spam/fraud branch"
            self.state = State.REPORT_COMPLETE # Note: Placeholder for now, the final report won't finish here
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


    

