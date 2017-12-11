import json
import os

from pyfcm import FCMNotification


class NestFCMManager:
    ADMIN_TOPIC = "admin"
    NONADMIN_TOPIC = "non-admin"

    def __init__(self):
        with open(os.path.join(os.environ["MYH_HOME"], "data", "fcm.json")) as fcm_file:
            fcm_dict = json.load(fcm_file)
            api_key = fcm_dict["api_key"]
        self.push_service = FCMNotification(api_key=api_key)

    def sendMessage(self, message_title, message_body, topic_name):
        self.push_service.notify_topic_subscribers(topic_name=topic_name, message_body=message_body,
                                                            message_title=message_title)

    def sendMessageAdmin(self, message_title, message_body):
        self.sendMessage(message_title, message_body, self.ADMIN_TOPIC)

    def sendMessageNonAdmin(self, message_title, message_body):
        self.sendMessage(message_title, message_body, self.NONADMIN_TOPIC)

if __name__ == "__main__":
    my_fcm = NestFCMManager()
    my_fcm.sendMessageNonAdmin("Test Title","Test Message")