import os
import sys

from harvey.globals import Global
from harvey.messages import Message


class Utils:
    @staticmethod
    def kill(final_output, webhook):
        """A kill util to write everything to logs, send messages,
        tear down Docker stuff, and quit.
        """
        Logs.generate_logs(final_output, webhook)
        if os.getenv('SLACK'):
            Message.send_slack_message(final_output)
        sys.exit()
        return True

    @staticmethod
    def success(final_output, webhook):
        """Log output and send message on pipeline success."""
        Logs.generate_logs(final_output, webhook)
        if os.getenv('SLACK'):
            Message.send_slack_message(final_output)
        return True


class Logs:
    @staticmethod
    def generate_logs(final_output, webhook):
        """Generate log file with all output"""
        if not os.path.exists(os.path.join(Global.PROJECTS_LOG_PATH, Global.repo_full_name(webhook))):
            os.makedirs(os.path.join(Global.PROJECTS_LOG_PATH, Global.repo_full_name(webhook)))
        try:
            filename = os.path.join(
                Global.PROJECTS_LOG_PATH, Global.repo_full_name(webhook), Global.repo_commit_id(webhook) + '.log'
            )
            with open(filename, 'w') as log:
                log.write(final_output)
        except OSError as os_error:
            final_output = 'Error: Harvey could not save the log file.'
            print(os_error)
            Utils.kill(final_output, webhook)
