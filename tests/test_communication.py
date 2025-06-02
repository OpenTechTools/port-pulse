import pytest
from src.process_manager import create_process
from src.communication import send_message, receive_message

def test_send_receive():
    process1 = create_process()
    process2 = create_process()
    message = "Test message"
    send_message(process1, process2, message)
    received = receive_message(process2)
    assert received == message