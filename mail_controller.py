import smtplib
import os
from email.message import EmailMessage
import threading


class MailController:
    def __init__(self):
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.server.starttls()
        self.server.login("shoppystoreofficial@gmail.com", os.environ['mail_pass'])

    def send_message(self, message, subject, dest):
        thread = threading.Thread(target=self.__send_message, args=(message, subject, dest))
        thread.start()

    def __send_message(self, message, subject, dest):
        msg = EmailMessage()

        msg['Subject'] = subject
        msg['From'] = "shoppystoreofficial@gmail.com"
        msg['To'] = dest
        msg.set_content(message)

        self.server.send_message(msg)

    def __del__(self):
        self.server.quit()
