*** Settings ***
Documentation    BDD tests for AI agents powered by GitHub Copilot SDK.
...              Demonstrates Gherkin-style (Given/When/Then) testing of
...              AI-generated code, bug detection, and structured output
...              using Robot Framework with a Python Copilot SDK keyword library.
...
...              Run:  robot samples/copilot_bdd.robot
...              Requires: pip install robotframework github-copilot-sdk

Library          samples/robot_copilot_library.CopilotLibrary

Suite Setup      Start Copilot Session    gpt-5-mini
Suite Teardown   Stop Copilot Session


*** Test Cases ***

AI Should Generate Valid Python Code
    [Documentation]    Verify that AI-generated code parses as valid Python
    ...                and defines the requested function.
    [Tags]    code-generation    bdd
    Given I have a Copilot session
    When I ask Copilot to generate code    a recursive function named 'fibonacci' that returns the nth Fibonacci number
    Then the code should be valid Python
    And the code should define the function    fibonacci

AI Code Review Should Detect Division-By-Zero Bug
    [Documentation]    Verify that AI code review catches an obvious bug
    ...                in the provided source code.
    [Tags]    code-review    bdd
    Given I have a Copilot session
    When I ask Copilot to review buggy code
    Then the review should mention the bug    zero    empty    division

AI Should Generate Valid Structured JSON
    [Documentation]    Verify that AI can produce valid JSON matching
    ...                an expected schema with specific keys.
    [Tags]    structured-output    bdd
    Given I have a Copilot session
    When I ask Copilot to generate JSON    a user profile with name (string), age (integer), email (string)
    Then the output should be valid JSON
    And the JSON should contain keys    name    age    email

AI Should Explain Technical Concepts Accurately
    [Documentation]    Verify that AI provides topically relevant explanations
    ...                by checking for expected keywords.
    [Tags]    explanation    bdd
    Given I have a Copilot session
    When I ask Copilot to explain    What is a Python decorator? Answer in 2-3 sentences.
    Then the response should mention    decorator
    And the response should mention    function


*** Keywords ***

# ── Given ──

I have a Copilot session
    [Documentation]    Pre-condition — session is already open via Suite Setup.
    Log    Copilot session is active

# ── When ──

I ask Copilot to generate code
    [Arguments]    ${description}
    ${code}=    Ask Copilot To Generate Code    ${description}
    Log    Generated code:\n${code}

I ask Copilot to review buggy code
    ${buggy}=    Set Variable
    ...    def calculate_average(numbers):\n    total = sum(numbers)\n    return total / len(numbers)\n
    ${review}=    Ask Copilot To Review Code    ${buggy}
    Log    Review:\n${review}

I ask Copilot to generate JSON
    [Arguments]    ${description}
    ${json}=    Ask Copilot To Generate JSON    ${description}
    Log    JSON:\n${json}

I ask Copilot to explain
    [Arguments]    ${question}
    ${answer}=    Ask Copilot    ${question}
    Log    Answer:\n${answer}

# ── Then ──

The code should be valid Python
    Code Should Be Valid Python

The code should define the function
    [Arguments]    ${name}
    Code Should Define Function    ${name}

The review should mention the bug
    [Arguments]    @{keywords}
    Response Should Mention Bug    @{keywords}

The output should be valid JSON
    JSON Should Be Valid

The JSON should contain keys
    [Arguments]    @{keys}
    JSON Should Have Keys    @{keys}

The response should mention
    [Arguments]    ${text}
    Response Should Contain    ${text}
