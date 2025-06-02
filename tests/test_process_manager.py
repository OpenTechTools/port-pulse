import pytest
from src.process_manager import create_process, get_processes

def test_create_process():
    initial_count = len(get_processes())
    new_process = create_process()
    assert new_process is not None
    assert len(get_processes()) == initial_count + 1