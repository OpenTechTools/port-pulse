import multiprocessing
import os
from cli import cli

class Handler :
    """
    Handler class handles the request from the CLI and UI, to create the processes(parent and child).
    And to terminate process.
    """
    def __init__(self):
        self.test_p_process = 2
        self.test_c_process = 2
    def get_processes(self) :
        """
        This function will get the number of parent and child processes
        """
        # For now I have added the cli module, but this will fetch the number of processes in real-time.
        p_processes = cli.get_p_processes
        c_processes = cli.get_c_processes
        return self.test_p_process, self.test_c_process

class ProcessCreator :
    """
    ProcessCreator class is responsible for creating the parent and child processs.
    It creates multiple parent and child processes as per the requirement.
    """
    
    def __init__(self) :
        # Create object of the class Handler to get the processes
        self.instance_process = Handler()
        self.parent_processes = []
        self.child_process = []

    def main_process(self) :
        """
        This is the main process which is the file executioner itself.
        """
        return os.getpid()
    
    def child_handler(self,) :
        """
        Function to be executed by each child process.
        """

    def parent_handler(self, num_children) :
        """
        This is parent handler function that will handle parent processes
        Creates and waits indefinitely for the child processes
        """
        for i in range(num_children) :
            child_processes = multiprocessing.Process(target=child_handler)
            self.child_process.append(child_processes)
            child_processes.join()

        for p in child_processes :
            p.join()

    def create_parent_processes(self, parent_handler, num_processes) :
        """
        Create multiple parent processes.
        """
        
        for i in range(num_processes) :
            process = multiprocessing.Process(target=parent_handler, args=(i,self.instance_process.test_c_process))
            process.start()

class PortAssigner :
    """
    PortAssigner class is responsible for assigning the port to parent and child processes.
    This will call the "port_allocator".
    """


class ProcessTerminator :
    """
    ProcessTerminator is responsible for terminating the parent and child processes.
    Terminates the process based on when Port gets Destroyed.
    """
    