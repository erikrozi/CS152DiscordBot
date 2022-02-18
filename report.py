from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    REPORT_IDENTIFIED = auto()
    REPORT_CANCELLED = auto()
    START_OF_SPAM_BRANCH = auto()
    START_OF_HATE_SPEECH_BRANCH = auto()
    START_OF_HARASSMENT_BULLYING_BRANCH = auto()
    START_OF_THREATENING_DANGEROUS_BRANCH = auto()
    START_OF_SEXUAL_BRANCH = auto()
    START_OF_OTHER_BRANCH = auto()
    EXIT_ABUSE_BRANCH = auto()
    FINAL_PROMPT = auto()
    ABUSE_SPECIFIC_REPORT = auto()
    REPORT_COMPLETE = auto()
    AUTOMATED_REPORT = auto()

# The types of reports that a user can submit.
class ReportType(Enum):
    SPAM = auto()
    HATE_SPEECH = auto()
    HARASSMENT_BULLYING = auto()
    THREATENING_DANGEROUS = auto()
    SEXUAL = auto()
    OTHER = auto()

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
    HATE_SPEECH_OPTION_ONE_KEYWORD = "2a"
    HATE_SPEECH_OPTION_TWO_KEYWORD = "2b"
    HATE_SPEECH_OPTION_THREE_KEYWORD = "2c"
    HARASSMENT_BULLYING_OPTION_ONE_KEYWORD = "3a"
    HARASSMENT_BULLYING_OPTION_TWO_KEYWORD = "3b"
    HARASSMENT_BULLYING_OPTION_THREE_KEYWORD = "3c"
    THREATENING_DANGEROUS_OPTION_ONE_KEYWORD = "4a"
    THREATENING_DANGEROUS_OPTION_TWO_KEYWORD = "4b"
    THREATENING_DANGEROUS_OPTION_THREE_KEYWORD = "4c"
    SEXUAL_OPTION_ONE_KEYWORD = "5a"
    SEXUAL_OPTION_TWO_KEYWORD = "5b"

    END_REPORT_KEYWORD = "no"
    SUBMIT_ANOTHER_REPORT_KEYWORD = "yes"
    MUTE_KEYWORD = "Mute"
    BLOCK_KEYWORD = "Block"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.report_type = None
        self.abuseTypeKeyWords = [self.SPAM_FRAUD_KEYWORD, self.HATE_SPEECH_KEYWORD, self.HARASSMENT_BULLYING_KEYWORD,
                                  self.THREATENING_DANGEROUS_KEYWORD, self.SEXUAL_KEYWORD, self.OTHER_KEYWORD]
    
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
            reply = "Thank you for starting the reporting process. "
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
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner "
                        "add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to "
                        "cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to "
                        "cancel."]

            reply = "Help us understand the problem with this message. "
            reply += "Which of the following categories best describes this message:\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1: Spam/fraud\n2: Hate speech\n3: Harassment/bullying\n4: Threatening/dangerous behavior\n"
            reply += "5: Sexual offensive content\n6: Other\n"
            self.state = State.REPORT_IDENTIFIED
            self.message = message
            return [reply]

        # If an incorrect keyword was put in, reprompt the user with the correct keywords
        if message.content not in self.abuseTypeKeyWords and self.state == State.REPORT_IDENTIFIED:
            reply = "Reply with the number corresponding to the correct reason. \n\n"
            reply += "Which of the following categories best describes this message?\n\n"
            reply += "1: Spam/fraud\n2: Hate speech\n3: Harassment/bullying\n4: Threatening/dangerous behavior\n"
            reply += "5: Sexual offensive content\n6: Other\n"
            return [reply]

        if message.content == self.SPAM_FRAUD_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.SPAM
            self.state = State.START_OF_SPAM_BRANCH
            reply = "Please elaborate how this message is spam/fraud.\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "1a: This message is from a fake/spam account.\n"
            reply += "1b: This account is repeatedly sending you unwanted messages.\n"
            return [reply]

        if self.state == State.START_OF_SPAM_BRANCH:
            if message.content == self.SPAM_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this account.\n\n"
                reply = "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.SPAM_OPTION_TWO_KEYWORD:
                reply = "We're sorry to hear that.\n"
                reply = "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            else:
                # If an incorrect keyword was put in, reprompt the user with the correct keywords
                reply = "Please reply with the number corresponding to the correct reason.\n\n"
                reply += "1a: This message is from a fake/spam account.\n"
                reply += "1b: This account is repeatedly sending you unwanted messages.\n"
                return [reply]

        if message.content == self.HATE_SPEECH_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.HATE_SPEECH
            self.state = State.START_OF_HATE_SPEECH_BRANCH
            reply = "Who is the user targeting?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "2a: Me\n"
            reply += "2b: Someone else\n"
            reply += "2c: A group of people\n"
            return [reply]

        if self.state == State.START_OF_HATE_SPEECH_BRANCH:
            if message.content == self.HATE_SPEECH_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.HATE_SPEECH_OPTION_TWO_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.HATE_SPEECH_OPTION_THREE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            else:
                # If an incorrect keyword was put in, reprompt the user with the correct keywords
                reply = "Please reply with the number corresponding to the correct reason.\n\n"
                reply += "2a: Me\n"
                reply += "2b: Someone else\n"
                reply += "2c: A group of people\n"
                return [reply]

        if message.content == self.HARASSMENT_BULLYING_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.HARASSMENT_BULLYING
            self.state = State.START_OF_HARASSMENT_BULLYING_BRANCH
            reply = "Who is the user targeting?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "3a: Me\n"
            reply += "3b: Someone else\n"
            reply += "3c: A group of people\n"
            return [reply]

        if self.state == State.START_OF_HARASSMENT_BULLYING_BRANCH:
            if message.content == self.HARASSMENT_BULLYING_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.HARASSMENT_BULLYING_OPTION_TWO_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.HARASSMENT_BULLYING_OPTION_THREE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this further.\n\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            else:
                # If an incorrect keyword was put in, reprompt the user with the correct keywords
                reply = "Please reply with the number corresponding to the correct reason.\n\n"
                reply += "3a: Me\n"
                reply += "3b: Someone else\n"
                reply += "3c: A group of people\n"
                return [reply]

        if message.content == self.THREATENING_DANGEROUS_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.THREATENING_DANGEROUS
            self.state = State.START_OF_THREATENING_DANGEROUS_BRANCH
            reply = "Who is the being threatened or in danger?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "4a: The user is threatening me\n"
            reply += "4b: The user is threatening or appears to be at risk of harming themselves\n"
            reply += "4c: The user is threatening to or appears to be at risk of harming others\n"
            return [reply]

        if self.state == State.START_OF_THREATENING_DANGEROUS_BRANCH:
            if message.content == self.THREATENING_DANGEROUS_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this. If deemed " \
                        "appropriate, we will remove the post and may work with law enforcement to investigate this " \
                        "further.\n\n"
                reply = "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.THREATENING_DANGEROUS_OPTION_TWO_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this. If deemed " \
                        "appropriate, we will remove the post and will provide mental health support and resources " \
                        "to the user.\n\n"
                reply = "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.THREATENING_DANGEROUS_OPTION_THREE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this and remove the post" \
                        "and work with law enforcement to determine the consequence for this account if deemed " \
                        "appropriate.\n\n"
                reply = "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            else:
                # If an incorrect keyword was put in, reprompt the user with the correct keywords
                reply = "Please reply with the number corresponding to the correct reason.\n\n"
                reply += "4a: The user is threatening me\n"
                reply += "4b: The user is threatening or appears to be at risk of harming themselves\n"
                reply += "4c: The user is threatening to or appears to be at risk of harming others\n"
                return [reply]

        if message.content == self.SEXUAL_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.SEXUAL
            self.state = State.START_OF_SEXUAL_BRANCH
            reply = "Is this child sexual abuse material?\n\n"
            reply += "Reply with the number corresponding to the correct reason.\n\n"
            reply += "5a: Yes\n"
            reply += "5b: No\n"
            return [reply]

        if self.state == State.START_OF_SEXUAL_BRANCH:
            if message.content == self.SEXUAL_OPTION_ONE_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this and remove the post" \
                        "and work with law enforcement to determine the consequence for this account if deemed " \
                        "appropriate.\n\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            elif message.content == self.SEXUAL_OPTION_TWO_KEYWORD:
                reply = "Thank you for reporting this. Our moderation team will investigate this and remove the post" \
                        "and work with law enforcement to determine the consequence for this account if deemed " \
                        "appropriate.\n\n"
                reply += "To improve your experience, would you like to block or mute this account?\n"
                reply += "'Mute'\n"
                reply += "'Block'\n"
                reply += "'No thanks'\n"
                self.state = State.EXIT_ABUSE_BRANCH
                return [reply]
            else:
                # If an incorrect keyword was put in, reprompt the user with the correct keywords
                reply = "Please reply with the number corresponding to the correct reason.\n\n"
                reply += "5a: Yes\n"
                reply += "5b: No\n"
                return [reply]

        if message.content == self.OTHER_KEYWORD and self.state == State.REPORT_IDENTIFIED:
            self.report_type = ReportType.OTHER
            reply = "To improve your experience, would you like to block or mute this account?\n"
            reply += "'Mute'\n"
            reply += "'Block'\n"
            reply += "'No thanks'\n"
            self.state = State.EXIT_ABUSE_BRANCH
            return [reply]

        if self.state == State.EXIT_ABUSE_BRANCH:
            reply = "Are there other harmful messages from this user or similar harmful messages from other users " \
                    "that you'd also like to report?\n\n"
            reply += "Please respond with 'Yes' or 'No'\n"
            self.state = State.FINAL_PROMPT
            return [reply]

        if self.state == State.FINAL_PROMPT:
            userMessage = message.content
            if userMessage.lower() == self.END_REPORT_KEYWORD:
                self.state = State.REPORT_COMPLETE
                reply = "Thank you for taking the time to report this. We know that interacting with this content can" \
                        " be harmful. Here are some mental health resources for you: <NOTE PUT LINKS HERE>\n\n"
                return[reply]
            elif userMessage.lower() == self.SUBMIT_ANOTHER_REPORT_KEYWORD:
                self.state = State.REPORT_COMPLETE
                reply = "Please say 'report' to continue reporting the message(s).\n"
                return [reply]
            else:
                reply = "Are there other harmful messages from this user or similar harmful messages from other users " \
                        "that you'd also like to report?\n\n"
                reply += "Please respond with 'Yes' or 'No'\n"
                self.state = State.FINAL_PROMPT
                return [reply]
        return []

    def get_user_being_reported(self):
        return self.message.author.id

    def get_user_being_reported_name(self):
        return self.message.author.name

    def report_cancelled(self):
        return self.state == State.REPORT_CANCELLED

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE

    def get_report_type(self):
        return self.report_type

    def get_message(self):
        return self.message


