#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Example to show scheduling messages to and cancelling messages from a Service Bus Queue.
"""

import os
import datetime
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.identity import DefaultAzureCredential

FULLY_QUALIFIED_NAMESPACE = os.environ["SERVICEBUS_FULLY_QUALIFIED_NAMESPACE"]
TOPIC_NAME = os.environ["SERVICEBUS_TOPIC_NAME"]


def schedule_single_message(sender):
    message = ServiceBusMessage("Message to be scheduled")
    scheduled_time_utc = datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
    sequence_number = sender.schedule_messages(message, scheduled_time_utc)
    return sequence_number


def schedule_multiple_messages(sender):
    messages_to_schedule = []
    for _ in range(10):
        messages_to_schedule.append(ServiceBusMessage("Message to be scheduled"))

    scheduled_time_utc = datetime.datetime.utcnow() + datetime.timedelta(seconds=30)
    sequence_numbers = sender.schedule_messages(messages_to_schedule, scheduled_time_utc)
    return sequence_numbers


def main():
    credential = DefaultAzureCredential()
    servicebus_client = ServiceBusClient(FULLY_QUALIFIED_NAMESPACE, credential, logging_enable=True)
    with servicebus_client:
        sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
        with sender:
            sequence_number = schedule_single_message(sender)
            print("Single message is scheduled and sequence number is {}".format(sequence_number))
            sequence_numbers = schedule_multiple_messages(sender)
            print("Multiple messages are scheduled and sequence numbers are {}".format(sequence_numbers))

            sender.cancel_scheduled_messages(sequence_number)
            sender.cancel_scheduled_messages(sequence_numbers)
            print("All scheduled messages are cancelled.")


if __name__ == "__main__":
    main()
