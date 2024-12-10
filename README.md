# QA-Devin
At Cognition we use Devin for Quality Assurance and end-to-end testing.

### Devin uses its browser to open app.devin.ai and test its functionality.
<img width="1496" alt="394167067-c350c30b-8825-4d43-80b3-73419a01eb91" src="https://github.com/user-attachments/assets/845f7440-c5d1-4f8b-8229-049ee9e834fa">


### Devin opens a Slack page and starts a new devin session with @Devin
<img width="1496" alt="394176239-5c3a5e0c-8135-4c79-86c0-658f974bf6a5" src="https://github.com/user-attachments/assets/989390bd-c786-4b54-8ea1-6cf091e60431">


### Final results sent to Slack
<img width="788" alt="394176066-606f7fb1-d8a7-4e25-a209-b57ec91277fe" src="https://github.com/user-attachments/assets/dfaa16de-f17c-43b5-bf27-09a5c1637d2c">


## Example Tests

- check-public-devin-session: Verifies that a public session can be accessed without logging in
- devin-secrets-add: Tests secrets management functionality in the browser
- check-devin-weather: Tests whether Devin can get the weather in a specific location using its browser
- devin-pr-sleep: Tests Pull Request creation and interaction along with sleep/awake functionality
- slack-devin-session: Tests Slack integration

## Example Test
```py
create_qa_test(
        test_name="devin-pr-sleep",
        user_prompt=f"""{DEVIN_QA_LOGIN_INSTRUCTIONS}
Then start a new session with the prompt "In the usacognition-snapshot/devin-webapp-e732ee6155d2d543dbb285bfd60af2ec826db738 repo explain what the useGlobalStateProvider hook does and add documentation to it. Make a PR for it. Do not change any other files. Use the branchname devin/explain-$RANDOM"
You need to press ctrl+enter to start a session.
CHECK: Your new session should have started (or in the process of starting) successfully and it should have taken you to the session page.

Wait for 20 seconds.
Send a message saying "What are you doing?" (pressing Enter is enough to send the message once the session has started)
Wait 20 seconds.
CHECK: You should have receieved a new message from Devin talking about what it is doing.

Send a new message saying "SLEEP".
Wait 15 seconds.
CHECK: The status of the session should be something like "Devin is sleeping"

Send a new message saying "WAKE UP"
Wait 90 seconds.
CHECK: The status of the session should no longer be sleeping
CHECK: Devin should have replied to your message with a new message

If you see devin asking you to confirm a plan then always confirm the plan.

Then wait until Devin sends you a message with a link to a github PR.
CHECK: Devin should have sent you a message with a link to a github PR.

Type in "SLEEP"
Wait 15 seconds.
CHECK: The status of the session should be sleeping

Now we will write a comment on the PR created above using the API
Run the following shell command replacing the secret with the actual token and the PR number with the actual PR number from the previous message:

gh pr comment -R usacognition-snapshot/devin-webapp-e732ee6155d2d543dbb285bfd60af2ec826db738 766 -b "Reduce the verbosity of the documentation you just added"

Wait 60 seconds and then call <view_browser>    to see the state of the browser again (dont use navigate_browser)
CHECK: Devin should no longer be in the sleeping state
CHECK: There should be text saying "Received feedback from GitHub comments" or something along those lines explaining that Devin received feedback from GitHub comments
""",
    ),
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Generate a Devin API Key from https://app.devin.ai/settings/api-keys
2. Copy the `.env.template` file to `.env` in the root directory and fill in the values. Slack tokens are optional.
3. Open https://app.devin.ai/secrets in your browser and add the secrets. For this particular example we added these secrets:
   - Google Login - Email, Password and [2FA code (TOTP)](https://docs.devin.ai/onboard-devin/secrets#one-time-password)
   - Slack Login - Email, Password and [2FA code (TOTP)](https://docs.devin.ai/onboard-devin/secrets#one-time-password)
   - Github Token - Personal Access Token - To create comments on pull requests

4. Run QA tests:
```bash
python3 run_qa_devin.py
```

You can also run specific tests:
```bash
python3 run_qa_devin.py --tests test1,test2
```
