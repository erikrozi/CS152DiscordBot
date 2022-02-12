# modFlow.py
from report import Report

user_false_reports = {}

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


