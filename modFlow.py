# modFlow.py
from report import Report, ReportType, State
from datetime import datetime
from enum import Enum, auto

user_false_reports = {}
manager_review_queue = []


SEVERE_TOXICITY = "SEVERE_TOXICITY"
IDENTITY_ATTACK = "IDENTITY_ATTACK"
TOXICITY = "TOXICITY"
FLIRTATION = "FLIRTATION"
THREAT = "THREAT"
PROFANITY = "PROFANITY"

AUTOMATED = "AUTOMATED"

def new_report_filed(completed_report, user_being_reported, user_being_reported_name, user_making_report,
                     user_making_report_name, reports_by_user, reports_about_user, bad_things_list):
    # Check if abuse or not.
    is_abuse = False
    if len(bad_things_list) > 0:
        is_abuse = True

    if not is_abuse:
        # Add to false reporting map.
        if user_making_report not in user_false_reports:
            user_false_reports[user_making_report] = []
        user_false_reports[user_making_report].append(completed_report)

        # Check if user has > 30 false reports.
        if len(user_false_reports[user_making_report]) > 30:
            return False, user_making_report_name + ": Your account has been banned due to too many false reports."
        else:
            return False, user_making_report_name + ": We did not find this post to be abusive. " \
                                                    "Please email us if you think we made a mistake."

    # Determine what type of abuse.
    report_type = completed_report.get_report_type()
    if report_type == ReportType.HARASSMENT_BULLYING:
        return general_harassment_report(user_being_reported, user_making_report, reports_by_user, reports_about_user,
                                         user_making_report_name, user_being_reported_name)
    elif report_type == ReportType.SPAM:
        return spam_report(reports_about_user[user_being_reported], user_being_reported_name)
    elif report_type == ReportType.HATE_SPEECH:
        take_post_down, response = general_harassment_report(user_being_reported, user_making_report,
                                                             reports_by_user, reports_about_user,
                                                             user_making_report_name, user_being_reported_name)
        response += " " + user_making_report_name + ": Some forms of hate speech can be legally prosecuted, including libel. " \
                                              "Please see these resources to see how you could potentially hold your " \
                                              "abusers accountable under the law. https://www.ala.org/advocacy/intfreedom/hate"
        return True, response
    elif report_type == ReportType.THREATENING_DANGEROUS:
        return threatening_dangerous_report(completed_report, bad_things_list, user_being_reported, reports_about_user,
                                            user_making_report_name, user_being_reported_name)
    elif report_type == ReportType.SEXUAL:
        return sexual_report(completed_report, reports_about_user[user_being_reported], user_being_reported_name)
    else: # Other
        return general_harassment_report(user_being_reported, user_making_report, reports_by_user, reports_about_user,
                                         user_making_report_name, user_being_reported_name)


def spam_report(reports_about_user_list, user_being_reported_name):
    # Check counts of spam already against user.
    spam_count = 0
    for report in reports_about_user_list:
        if report.report_type is ReportType.SPAM:
            spam_count += 1

    if spam_count > 30:
        return True, user_being_reported_name + ": Your account has been banned due to too many spam messages."
    else:
        return True, user_being_reported_name + ": Your post has marked as spam and has been removed. " \
                                                "Please email us if you think we made a mistake."


def sexual_report(report, reports_about_user_list, user_being_reported_name):
    manager_review_queue.append(report) # To check if CSAM.
    return True, check_if_have_3_strikes(reports_about_user_list, user_being_reported_name)


def check_if_have_3_strikes(reports, user_being_reported_name):
    offensive_count = 0
    for report in reports:
        if report.report_type != ReportType.SPAM:
            offensive_count += 1

    if offensive_count > 3:
        return user_being_reported_name + ": Your account has been banned due to too many abusive posts."
    else:
        return user_being_reported_name + ": Your post has marked as offensive and has been removed. " \
                                          "Please email us if you think we made a mistake."


def threatening_dangerous_report(report, bad_things_list, user_being_reported, reports_about_user, user_making_report_name, user_being_reported_name):
    if "THREAT" in bad_things_list:
        manager_review_queue.append(report) # For chance of terrorism.

    return True, check_if_have_3_strikes(reports_about_user[user_being_reported], user_being_reported_name)


def general_harassment_report(user_being_reported, user_making_report, reports_by_user, reports_about_user,
                              user_making_report_name, user_being_reported_name):
    # Find number of reports the user had made in last 24 hours, and number of different people they have reported.
    num_reports_by_user_in_last_24_hours = 0
    users_being_reported_last_24_hours = []
    if user_making_report != AUTOMATED:
        for report in reports_by_user[user_making_report]:
            timestamp = report.message.created_at
            difference = datetime.utcnow() - timestamp
            if difference.days == 0:
                num_reports_by_user_in_last_24_hours += 1
                if report.message.author.id not in users_being_reported_last_24_hours:
                    users_being_reported_last_24_hours.append(users_being_reported_last_24_hours)

    if num_reports_by_user_in_last_24_hours == 0:
        return True, check_if_have_3_strikes(reports_about_user[user_being_reported], user_being_reported_name)
    else:
        number_users_being_reported = len(users_being_reported_last_24_hours)
        if number_users_being_reported == 1:
            return True, check_if_have_3_strikes(reports_about_user[user_being_reported], user_being_reported_name)
        elif number_users_being_reported > 5:
            return True, user_making_report_name + ": We noticed you have reported many users for harmful content. Please click here if you " \
                              "would like to block non-friends from messaging you for the next 24 hours. Please " \
                              "contact us if you think this block should be extended for more than 24 hours."
        else:
            return True, user_making_report_name + "We noticed you have reported many users for harmful content. Please click here if you " \
                              "would like to block non-friends from messaging you for the next 24 hours."

def automatic_report(bad_things, message, self, reports_about_user, user_making_report_name, user_being_reported_name):
    new_report = Report(self)
    new_report.message = message
    new_report.state = State.AUTOMATED_REPORT
    user_being_reported = message.author.id
    if user_being_reported not in reports_about_user:
        self.reports_about_user[user_being_reported] = []
    self.reports_about_user[user_being_reported].append(new_report)

    for bad_thing in bad_things:
        if bad_thing == SEVERE_TOXICITY:
            new_report.report_type = ReportType.HARASSMENT_BULLYING
            return threatening_dangerous_report(new_report, bad_things, user_being_reported, reports_about_user,
                                                user_making_report_name, user_being_reported_name)
        elif bad_thing == TOXICITY:
            new_report.report_type = ReportType.HATE_SPEECH
            return general_harassment_report(user_being_reported, AUTOMATED, [],
                                             reports_about_user, user_making_report_name, user_being_reported_name)
        elif bad_thing == THREAT:
            new_report.report_type = ReportType.THREATENING_DANGEROUS
            return threatening_dangerous_report(new_report, bad_things, user_being_reported, reports_about_user,
                                                user_making_report_name, user_being_reported_name)
        elif bad_thing == FLIRTATION:
            new_report.report_type = ReportType.SEXUAL
            return sexual_report(new_report, reports_about_user[user_being_reported], user_being_reported_name)
        elif bad_thing == PROFANITY:
            new_report.report_type = ReportType.HARASSMENT_BULLYING
            return general_harassment_report(user_being_reported, AUTOMATED, [],
                                             reports_about_user, user_making_report_name, user_being_reported_name)
        elif bad_thing == IDENTITY_ATTACK:
            new_report.report_type = ReportType.OTHER
            return general_harassment_report(user_being_reported, AUTOMATED, [],
                                             reports_about_user, user_making_report_name, user_being_reported_name)
    return False, ""

