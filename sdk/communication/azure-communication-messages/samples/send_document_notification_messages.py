# coding: utf-8

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
FILE: send_document_notification_messages.py

DESCRIPTION:
    This sample demonstrates sending an Whatsapp message from business phone number to a single user. The NotificationMessageClient is 
    authenticated using a connection string.
USAGE:
    python send_document_notification_messages.py

    Set the environment variable with your own value before running the sample:
    1) COMMUNICATION_SAMPLES_CONNECTION_STRING - the connection string in your ACS resource
    2) RECIPIENT_PHONE_NUMBER - a phone number with Whatsapp capabilities. Use list for recipient phone number.
    3) WHATSAPP_CHANNEL_ID - Channel created in Azure portal for Advanced Messaging.
"""

import os
import sys

sys.path.append("..")


class SendWhatsAppMessageSample(object):

    connection_string: str = os.getenv("COMMUNICATION_SAMPLES_CONNECTION_STRING")  # type: ignore
    phone_number: str = os.getenv("RECIPIENT_PHONE_NUMBER")  # type: ignore
    channel_id: str = os.getenv("WHATSAPP_CHANNEL_ID")  # type: ignore

    def send_document_message(self):

        from azure.communication.messages import NotificationMessagesClient
        from azure.communication.messages.models import DocumentNotificationContent

        messaging_client = NotificationMessagesClient.from_connection_string(self.connection_string)

        text_options = DocumentNotificationContent(
            channel_registration_id=self.channel_id,
            to=[self.phone_number],
            caption="Hello World via Advanced Messaging SDK.This is document message",
            file_name="Product roadmap timeline.pptx",
            media_uri="https://sample-videos.com/ppt/Sample-PPT-File-500kb.ppt",
        )

        # calling send() with whatsapp message details
        message_responses = messaging_client.send(text_options)
        response = message_responses.receipts[0]
        print("Message with message id {} was successful sent to {}".format(response.message_id, response.to))


if __name__ == "__main__":
    sample = SendWhatsAppMessageSample()
    sample.send_document_message()
