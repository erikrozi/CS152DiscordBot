# modFlow.py
from report import Report, ReportType

user_false_reports = {}
manager_review_queue = []


def new_report_filed(completed_report, user_being_reported, user_making_report, reports_by_user, reports_about_user):
    # Check if abuse or not.
    is_abuse = True # TODO: figure out if abuse or not

    # TODO: make all print statements into return messages.
    if not is_abuse:
        # Add to false reporting map.
        if user_making_report not in user_false_reports:
            user_false_reports[user_making_report] = []
        user_false_reports[user_making_report].append(completed_report)

        # Check if user has > 30 false reports.
        if len(user_false_reports[user_making_report]) > 30:
            print("Your account has been banned due to too many false reports.")
        else:
            print("We did not find this post to be abusive. Please email us if you think we made a mistake.")
        return

    # Determine what type of abuse.
    report_type = completed_report.get_report_type()
    if report_type == ReportType.HARASSMENT_BULLYING:
        general_harassment_report(completed_report)
    elif report_type == ReportType.SPAM:
        spam_report(reports_about_user[user_being_reported])
    elif report_type == ReportType.HATE_SPEECH:
        general_harassment_report(completed_report)
    elif report_type == ReportType.THREATENING_DANGEROUS:
        threatening_dangerous_report(completed_report)
    elif report_type == ReportType.SEXUAL:
        sexual_report(completed_report, reports_about_user[user_being_reported])
    else: # Other
        general_harassment_report(completed_report)


def spam_report(reports_about_user_list):
    # Check counts of spam already against user.
    spam_count = 0
    for report in reports_about_user_list:
        if report.report_type is ReportType.SPAM:
            spam_count += 1

    if spam_count > 30:
        print("Your account has been banned due to too many spam messages.")
    else:
        # TODO: figure out how to remove message.
        print("Your post has marked as spam and has been removed. Please email us if you think we made a mistake.")


def sexual_report(report, reports_about_user_list):
    # TODO: check if post is CSAM
    is_CSAM = False

    if is_CSAM:
        manager_review_queue.append(report)
        # TODO: remove post.
        print("Your account has been banned due to child sexual material.")
    else:
        check_if_have_3_strikes(reports_about_user_list)


def check_if_have_3_strikes(reports):
    offensive_count = 0
    for report in reports:
        if report.report_type != ReportType.SPAM:
            offensive_count += 1

    if offensive_count > 3:
        print("Your account has been banned due to too many abusive posts.")
    else:
        print("Your post has marked as offensive and has been removed. Please email us if you think we made a mistake.")


def threatening_dangerous_report(report):
    print("Sexual")


def general_harassment_report(report):
    print("General harassment")

