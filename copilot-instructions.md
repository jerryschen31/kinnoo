## Introduction
- This markdown file contains instructions that guide the behavior and guidelines for any AI coding agent (e.g., GitHub Copilot SWE agent) in this project when generating code, generating text, planning, or performing other tasks.

## Project Overview
- Kinnoo is intended to be a platform where developers can publish, version control and share their agents with other developers. 
- Features include a package definition for agents, a package manager for agents, and a CLI that supports many common commands for working with agents. 
- The platform should be designed to be extensible and flexible, supporting the most common agent frameworks (CrewAI, LangChain, Copilot, smolagents etc). 
- The platform should also prioritize security and privacy, ensuring that humans are always in control of the agents, and agents and their data are protected from unauthorized access or misuse. This prevents the risk of a "Skynet" where agents become self-aware and uncontrollable, and ensures that the platform is used responsibly and ethically by developers.

## Project Technical Details
- to be filled

## Project Steps
- to be filled

## Coding Standards
- The app should be structured in a modular way to facilitate maintainability and scalability
- The app should include comprehensive error handling and user feedback mechanisms to handle potential issues gracefully
- Use meaningful and descriptive names for variables, functions, classes, and other identifiers
- Write clear and concise comments to explain complex logic or decisions in the code
- Maintain consistent code formatting, including indentation, spacing, and line breaks
- Ensure all code is well-documented, including public APIs and complex functions
- Write unit tests for all critical components and functionalities to ensure code reliability
- Adhere to SOLID principles and design patterns to create a robust and flexible codebase
- Never commit any secrets to the repository. Always use environment variables or secure vaults to manage sensitive information, and ensure that .gitignore is properly configured to exclude any files containing secrets or sensitive data from being tracked by Git.
- Any agent that installs a Python library must first add it to `requirements.txt` before running `pip install`. This ensures all dependencies are tracked and reproducible.
- Run Python scripts inside virtual environments

## Project Structure
- The project should be organized into logical modules or components
- Each module should have a clear responsibility and interface, allowing for separation of concerns and easier maintenance
- The project should include a README file with an overview of the app, setup instructions, and any other relevant information for developers or users
- utils/ folder should contain any utility functions or helpers used across the project
- tests/ folder should contain unit tests for the critical components and functionalities of the app
- outputs/ folders should contain any test runs, logs, or generated files from the app
- docs/ folder should contain any documentation related to the project, such as API documentation, design decisions, or other relevant information
- data/ folder should contain any data downloaded for the project
- scripts/ folder should contain any scripts used for automating tasks, such as model conversion, data preprocessing, or other relevant tasks
- env/ folder should contain any environment configuration files, such as .env files for storing sensitive information or configuration settings

## Other Agent Instructions and Guidelines
- Always follow the instructions found in this file when generating code, generating text, planning, or performing other tasks related to this project
- Teach me how to do things, don't just do them for me. I want to learn and understand the process, not just see the end result. Teach me about the tools, technologies, and best practices involved in this project so I can become more knowledgeable and self-sufficient in the future. Particularly, teach me about Machine Learning and agentic AI concepts, and any technologies or tools (e.g., LangChain / LangGraph) that are used in this project. Provide explanations, resources, and guidance to help me learn and grow as a developer while we work on this project together.
- Always explain your reasoning and thought process when making decisions or generating code. While thinking and working, write out your thinking process in the response output, instead of hiding it. This will help me understand your reasoning and approach to solving problems, and will also allow for better collaboration and learning between us.
- Always ask for clarification if you are unsure about any aspect of the project, requirements, or instructions. If something is unclear or ambiguous, ask me for more information or clarification before proceeding. This will help ensure that we are on the same page and that the work being done aligns with the project goals and requirements.
- After the task or action to be performed is clear, for any commands to be executed that do not change any existing files (e.g., command to search for files, or list files, or get file sizes), go ahead and execute them without asking for confirmation or approval. For any commands to be executed that do change existing files (e.g., command to write to a file, or delete a file), ALWAYS ask for confirmation or approval before executing the command. This will help prevent unintended changes or mistakes in the project files, and will allow for better control and oversight of the work being done.
- After making an important decision or generating code, ALWAYS provide a summary of what you have done and why. Update any relevant documentation or instructions to reflect the changes or decisions made. This will help keep the project organized and ensure that all changes are well-documented and understood by everyone involved in the project.

## Agent Workflow and Project Management
- Tech-Lead agent (techlead.agent.md) is primarily responsible for the technical direction of the project, managing features, and creating tasks that are handoff to SWE agents for implementation. 
- Tech-Lead agent is also responsible for reviewing and approving features and tasks completed by SWE agents.
- The SWE agent (swe.agent.md) is primarily responsible for managing tasks and tests.
- The Tech-Lead and SWE agents should collaborate and communicate effectively to ensure that features, tasks, and tests are properly linked and organized in the project.
- The Git agent (git.agent.md) is responsible for managing the git workflow, including creating branches, committing changes, and creating pull requests. The Git agent should work closely with the Tech-Lead and SWE agents to ensure that all code changes are properly tracked and organized in the git repository. Git agent should also ensure review commits, to ensure all commits are well-documented and follow the project's coding standards and guidelines.
- Agents work on features, tasks, and tests (see git.agent.md). The hierarchy is feature -> task(s) -> test(s)
- If a feature references tests/tasks, an agent must refuse implementation until tasks and tests exist and are linked. Specifically,every feature requires task IDs that exist in TASKS.txt and test IDs that exist in TESTS.txt. Every task requires test IDs that exist in TESTS.txt. If any of these references do not exist, the agent must refuse implementation and ask for the missing references to be created and linked before proceeding with implementation. This will help ensure that all work is properly tracked and organized, and that there is a clear connection between features, tasks and tests in the project.
- Allowed status transitions for features and tasks are as follows:
    - not-started -> in-progress
    - in-progress -> completed
    - not-started -> blocked
    - in-progress -> blocked
    - blocked -> in-progress
    - in-progress -> paused
    - paused -> in-progress
    - in-progress -> needs-review
    - needs-review -> in-progress
    - needs-review -> completed
- To prevent conflicts, SWE agent updates tasks/tests, and can review tasks; Tech-Lead agent updates features and reviews/approves tasks and features; Git agent should review commits.

## Manifest Update Checklist (agents MUST follow)
1. Create test entry in TESTS.txt (increment ID).
2. Create/update task entry in TASKS.txt; add test ID to `tests` list.
3. Create/update feature entry in FEATURES.txt; add task ID to `tasks`.
4. Run `python3 scripts/validate_manifest.py` — fix any errors before committing.
5. Commit manifest changes in the same branch/PR as the code.
