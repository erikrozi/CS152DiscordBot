# modFlow.py
from report import Report, ReportType
from datetime import datetime

user_false_reports = {}
manager_review_queue = []


def new_report_filed(completed_report, user_being_reported, user_making_report, reports_by_user, reports_about_user):
    # Check if abuse or not.
    is_abuse = True # TODO: figure out if abuse or not

    if not is_abuse:
        # Add to false reporting map.
        if user_making_report not in user_false_reports:
            user_false_reports[user_making_report] = []
        user_false_reports[user_making_report].append(completed_report)

        # Check if user has > 30 false reports.
        if len(user_false_reports[user_making_report]) > 30:
            return "Your account has been banned due to too many false reports."
        else:
            return "We did not find this post to be abusive. Please email us if you think we made a mistake."

    # Determine what type of abuse.
    report_type = completed_report.get_report_type()
    if report_type == ReportType.HARASSMENT_BULLYING:
        return general_harassment_report("", user_being_reported, user_making_report, reports_by_user, reports_about_user)
    elif report_type == ReportType.SPAM:
        return spam_report(reports_about_user[user_being_reported])
    elif report_type == ReportType.HATE_SPEECH:
        response = hate_speech_report(completed_report)
        return general_harassment_report(response, user_being_reported, user_making_report, reports_by_user, reports_about_user)
    elif report_type == ReportType.THREATENING_DANGEROUS:
        return threatening_dangerous_report(completed_report)
    elif report_type == ReportType.SEXUAL:
        return sexual_report(completed_report, reports_about_user[user_being_reported])
    else: # Other
        return general_harassment_report("", user_being_reported, user_making_report, reports_by_user, reports_about_user)


def spam_report(reports_about_user_list):
    # Check counts of spam already against user.
    spam_count = 0
    for report in reports_about_user_list:
        if report.report_type is ReportType.SPAM:
            spam_count += 1

    if spam_count > 30:
        return "Your account has been banned due to too many spam messages."
    else:
        # TODO: figure out how to remove message.
        return "Your post has marked as spam and has been removed. Please email us if you think we made a mistake."


def sexual_report(report, reports_about_user_list):
    # TODO: check if post is CSAM
    is_CSAM = False

    if is_CSAM:
        manager_review_queue.append(report)
        # TODO: remove post.
        return "Your account has been banned due to child sexual material."
    else:
        check_if_have_3_strikes(reports_about_user_list)


def check_if_have_3_strikes(reports):
    offensive_count = 0
    for report in reports:
        if report.report_type != ReportType.SPAM:
            offensive_count += 1

    if offensive_count > 3:
        return "Your account has been banned due to too many abusive posts."
    else:
        return "Your post has marked as offensive and has been removed. Please email us if you think we made a mistake."


def threatening_dangerous_report(report):
    who_targeting = "self" # TODO: determine who is targeting

    if who_targeting == "self":
        return "Your post has been removed due to threatening behavior. Please see the below mental health resources " \
               "and call lines."
    elif who_targeting == "user":
        return "Your account has been banned for 24 hours due to threatening behavior. Please email us if you think " \
               "we made a mistake."
    else:
        is_terrorism = False # TODO: determine if terrorism
        if is_terrorism:
            manager_review_queue.append(report)
            return "Your account has been banned due to terrorism material."
        else:
            return "Your account has been banned for 24 hours due to threatening behavior. Please email us if you " \
                   "think we made a mistake."


def hate_speech_report(report):
    is_protected_group = False # TODO: determine if protected group
    if is_protected_group:
        # TODO: Remove post. Block user from messaging this user permanently.
        return "Some forms of hate speech can be legally prosecuted, including libel. Please see these resources " \
                   "to see how you could potentially hold your abusers accountable under the law. "
    return ""


def general_harassment_report(response, user_being_reported, user_making_report, reports_by_user, reports_about_user):
    # Find number of reports the user had made in last 24 hours, and number of different people they have reported.
    num_reports_by_user_in_last_24_hours = 0
    users_being_reported_last_24_hours = []
    for report in reports_by_user[user_making_report]:
        timestamp = report.message.created_at
        difference = datetime.utcnow() - timestamp
        if difference.days == 0:
            num_reports_by_user_in_last_24_hours += 1
            if report.message.author.id not in users_being_reported_last_24_hours:
                users_being_reported_last_24_hours.append(users_being_reported_last_24_hours)

    if num_reports_by_user_in_last_24_hours == 0:
        check_if_have_3_strikes(reports_about_user[user_being_reported])
    else:
        number_users_being_reported = len(users_being_reported_last_24_hours)
        if number_users_being_reported == 1:
            # TODO: block user from sending messages to this user for 24 hours. Make user re-verify identity.
            check_if_have_3_strikes(reports_about_user[user_being_reported])
        elif number_users_being_reported > 5:
            # TODO: Allow user to block non-friends from messaging them for 24 hours.
            return response + "We noticed you have reported many users for harmful content. Please click here if you " \
                              "would like to block non-friends from messaging you for the next 24 hours. Please " \
                              "contact us if you think this block should be extended for more than 24 hours."
        else:
            # TODO: Allow user to block non-friends from messaging them for 24 hours.
            return response + "We noticed you have reported many users for harmful content. Please click here if you " \
                              "would like to block non-friends from messaging you for the next 24 hours."

