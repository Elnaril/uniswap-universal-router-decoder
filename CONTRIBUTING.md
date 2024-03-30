# How to contribute

Firstly, thank you for investing your time in contributing to this project! :)  
In this guide, you'll get an overview of the contribution workflow, from asking questions to reporting an issue and submitting a pull request.

## Reporting a Bug or Asking a Question ?

Before reporting or asking anything, ensure it has not already been done or answered in:
 - [Q&A](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions/categories/q-a)
 - [Issues](https://github.com/Elnaril/uniswap-universal-router-decoder/issues) (opened and closed)
 - [Documentation](https://github.com/Elnaril/uniswap-universal-router-decoder?tab=readme-ov-file#uniswap-universal-router-decoder--encoder)
 - [Wiki](https://github.com/Elnaril/uniswap-universal-router-decoder/wiki)

Sometime issue titles are misleading: search by keywords and check the questions/reports and answers to be sure yours has not yet been addressed.

Before reporting a bug, ensure it's one.  
If in doubt, then ask first a question in [Q&A](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions/categories/q-a).
And if we found out it's actually a bug, and if it has not already been reported, then you may open a new issue. 

## Reporting a Security Vulnerability

In the case of a security vulnerability, do not open an issue (or a question) but read the [security policy](https://github.com/Elnaril/uniswap-universal-router-decoder?tab=security-ov-file)

## Reporting a bug/issue

Open an [Issue](https://github.com/Elnaril/uniswap-universal-router-decoder/issues):
- Describe the issue or bug: A clear and concise description of what the issue or bug is.
- Formatting: 
  - use the Markdown code formatter for code.
  - ensure the code is correctly formatted (especially if you paste it).
  - If relevant, consider formatting any output for better readability.
- Expected behavior: A clear and concise description of what you expected to happen.
- Version: Check you're having the issue with the latest version of the lib.
- How to reproduce: Steps to reproduce the behavior.
- Screenshots: If applicable, add screenshots to help explain your problem.
- Additional context: Add any other context about the problem here.

## Asking for a new feature
If you think a new feature would be a nice addition to this library, let's discuss it first in the [Ideas](https://github.com/Elnaril/uniswap-universal-router-decoder/discussions/categories/ideas) section of the discussions.
On confirmation, you may create an issue for someone else to implement it, or submit directly a PR.
In both cases, ensure you're referencing the discussion.

When describing the feature please provide at least the following:
- clear and concise description of the feature you'd like to see in this lib.
- use case description with example + any context
- description of any alternative you use at the moment

## Submitting a PR

### The PR is a cosmetic patch (whitespace, format code, comments...)
Cosmetic changes that do not add anything substantial to the stability, functionality, or testability of this library will generally not be accepted (See [Rational](https://github.com/rails/rails/pull/13771#issuecomment-32746700)).

### The PR fixes a bug or add a new feature
You have gone through the previous steps (discussion and/or issue) and are ready to submit a PR that makes a substantial change?
Great!  
But does your change comply with the following:
- [PEP 8](https://peps.python.org/pep-0008/#function-and-variable-names) naming convention
- Formatting is consistent with the existing code
- all unit tests and linting are successful
- coverage is still at 100%
- all integration tests are successful
- depending on the changes, you may have to update the integration tests or update them
- If there is a change in the API that the SDK exposes (like a new public method or change in a public method signature):
  - it must be documented in the corresponding docstring.
  - it must be documented in the README.md if it's a new feature.
- ensure constants are defined in `_constants.py`
- ensure your change does not expose as "public" methods or attributes that should stay "private".

And lastly, please:
 - squash your commits so that 1 PR = 1 commit.
 - ensure your commit messages are clear and explanatory.
 - add a link to the corresponding discussion or issue in your PR.

-----
Thank you! :)
