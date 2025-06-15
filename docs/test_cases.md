# 📄 Manual Test Cases – Port-Pulse

This document contains manually executable test cases for validating the key functionalities of **Port-Pulse**. These test cases are meant to be run by a human tester and verified against expected outcomes.

---

## ✅ Test Case: TC_001 — Process Creation

| Field            | Description                                      |
|------------------|--------------------------------------------------|
| **ID**           | TC_001                                           |
| **Scenario**     | Process Creation                                 |
| **Preconditions**| System is running and Port-Pulse is installed.   |
| **Steps**        | 1. Start the Port-Pulse application  <br> 2. Create a new process via UI/CLI <br> 3. Observe the process list for monitoring |
| **Expected Result** | A new process appears with a unique port assigned and being monitored by Port-Pulse |

---

## ✅ Test Case: TC_002 — Inter-Process Communication

| Field            | Description                                        |
|------------------|----------------------------------------------------|
| **ID**           | TC_002                                             |
| **Scenario**     | Inter-Process Communication                        |
| **Preconditions**| Two processes must already be running with different ports |
| **Steps**        | 1. Send a message from Process A to Process B <br> 2. Ensure Process B receives it <br> 3. Check Port-Pulse logs |
| **Expected Result** | Process B successfully receives the message. Port-Pulse logs show details of communication between Process A and B |

---

## 🗂️ Notes

- These tests can be performed in both CLI and GUI versions of Port-Pulse (if available).
- Network or system firewalls should be disabled or configured to avoid interference with port communication during tests.
- Make sure to clean up processes post-testing to avoid port conflicts.
