# Contributing to PortPulse

We welcome contributions to [Port Pulse](https://github.com/OpenTechTools/port-pulse)! Please follow these guidelines to ensure a smooth contribution process.

## Prerequisites

Before you start contributing, make sure you have the following installed:

* **Git:** You'll need Git for version control. Download it from [git-scm.com](https://git-scm.com/downloads).
* **Python:** Python 3.8+
* **pip:** pip


## Getting Started

1.  **Fork the repository:** Click the "Fork" button on the top right of the repository page.
2.  **Clone your fork:**

    ```bash
    git clone https://github.com/your-username/port-pulse.git

    cd port-pulse
    ```

3.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate  # On Windows
    ```

4.  **Install dependencies:**

    * **Using pip:**

        ```bash
        pip install -r requirements.txt
        ```

5.  **Create a branch for your changes:**

    ```bash
    git checkout -b feature/your-feature-name
    ```

## Making Changes

1.  **Make your changes:** Implement your feature or fix the bug.
2.  **Follow code style:** Adhere to the project's coding style and conventions.
3.  **Write tests:** If you're adding new functionality, write tests to ensure it works correctly.
4.  **Run tests:**

    ```bash
    pytest
    ```


## Commit Message Guidelines

* **Use the present tense:** "Add feature" not "Added feature."
* **Use the imperative mood:** "Move cursor to..." not "Moves cursor to..."
* **Limit the first line to 72 characters or less.**
* **Reference issues and pull requests liberally after the first line.**
* **Provide a detailed description of the change in the body of the commit message.**
* **Example:**

    ```
    feat: Add new feature for user authentication

    This commit adds a new feature that allows users to authenticate
    using their email and password.

    Closes #123
    ```

## Pull Request Guidelines

1.  **Push your changes to your fork:**

    ```bash
    git push origin feature/your-feature-name
    ```

2.  **Create a pull request:** Go to the original repository on GitHub and click "New Pull Request."
3.  **Provide a clear and descriptive title and description:** Explain the changes you've made and why.
4.  **Reference relevant issues:** If your pull request addresses an issue, mention it in the description (e.g., "Closes #123").

## Developer Certificate of Origin (DCO)

We require that all contributors sign off on their commits to certify that they have the right to submit the code.

To sign off on a commit, use the `-s` or `--signoff` option when committing:

```bash
git commit -s -m "Your commit message" -m "Message Description"
```
**Note : Message Description & DCO signoff is strictly required.** 