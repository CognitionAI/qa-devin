from typing import TypedDict


class QATest(TypedDict):
    test_name: str
    user_prompt: str


QA_PREAMBLE = f"""\
Your job is to do QA testing on the {{url}} website.
Please follow the instructions below and make sure every line which starts with "CHECK" is working as expected.
If it is not then you should abort and send message to the user saying what went wrong. No need to send a message if it is working as expected.
After you are done, send a message with all the CHECKs you did and what the results were. Your structured output should be a json object with 'success' (boolean) and 'message' (string). The message should include whether each CHECK you ran passed or failed (and a reason if it failed).
"""

DEVIN_QA_LOGIN_INSTRUCTIONS = """\
Instructions:

Go to {url} and let the page load. Then the devin page should open up.
On the bottom left there will be a login button. Login using google and use the email and password from your secrets.
If it asks you to enter a 2-step-verification code, use the authenticator code from your secrets.

CHECK: That you got logged in.
"""


def create_qa_test(test_name: str, user_prompt: str) -> QATest:
    user_prompt = QA_PREAMBLE + "\n\n" + user_prompt
    return {
        "test_name": test_name,
        "user_prompt": user_prompt,
    }


QA_TESTS: list[QATest] = [
    create_qa_test(
        test_name="check-public-devin-session",
        user_prompt="""Instructions:
Open the link: https://app.devin.ai/sessions/26747fec98444a6f8c298948eeee8a38
CHECK: That the page loaded
CHECK: No auth was asked to open the session
CHECK: Is the first message in the conversation from Silas?
CHECK: Is the first message about building a grafana dashboard?
""",
    ),
    create_qa_test(
        test_name="devin-secrets-add",
        user_prompt=f"""{DEVIN_QA_LOGIN_INSTRUCTIONS}

Then move your mouse to the bottom left corner of the page which will open the sidebar.
Then click on the Library.
Then click on the Secrets page

First we will create a new secret using the "Create Secret" button.
Create a plain text secret with the key "TEST_NAME_1234" and the value "TEST_VALUE" and replace the 123 with a random number which you will generate.
CHECK: The secret was created and it is visible in the list.

Now delete the secret you just created.
CHECK: The secret was deleted. That it is no longer visible in the list.

Now we will try to bulk upload secrets. Create a test file with 3 secrets in it:
```
FILE_TEST_1="hi=abcd"
export secret2=postgresql://user:pass@localhost:5432/db
# export FILE_TEST_3="hey=123"
```
Delete secrets FILE_TEST_1 and secret2 if they already exist in the UI.
Then upload the file using "import secrets" button. Mark it as sensitive.
If it shows an error about there being duplicate secrets thats fine, you can ignore that and just continue because these secrets already exist.
CHECK: ensure that 2 secrets were shown and that the third one was not shown (since it starts with a #)

Add the secrets.
CHECK: ensure that the 2 new secrets are now in the list.
Click on the FILE_TEST_1 secret.
CHECK: ensure that the secret value is not visible as it has been marked as sensitive.

Now delete the 2 new secrets.
CHECK: ensure that the 2 new secrets are deleted.
""",
    ),
    create_qa_test(
        test_name="check-devin-weather",
        user_prompt=f"""{DEVIN_QA_LOGIN_INSTRUCTIONS}
Then start a new session with the prompt "Whats the weather right now?"
You need to press ctrl+enter to start a session.
CHECK: Your new session should have started successfully and it should have taken you to the session page.

Then wait for 90 seconds.

CHECK: Devin should have sent you a message asking what your location is?

If devin does that, then send a message saying you are based in San Francisco

Then wait for 90 seconds

CHECK: Devin should have sent a new message with the current weather in san francisco""",
    ),
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
```
gh pr comment -R usacognition-snapshot/devin-webapp-e732ee6155d2d543dbb285bfd60af2ec826db738 766 -b "Reduce the verbosity of the documentation you just added"
```
Wait 60 seconds and then call <view_browser>    to see the state of the browser again (dont use navigate_browser)
CHECK: Devin should no longer be in the sleeping state
CHECK: There should be text saying "Received feedback from GitHub comments" or something along those lines explaining that Devin received feedback from GitHub comments
""",
    ),
    create_qa_test(
        test_name="slack-devin-session",
        user_prompt="""Instructions:

Open https://qadevin.slack.com/sign_in_with_password and login using the email and password from your .env file.
If it asks you to enter a 2-step-verification code, use the authenticator code from your .env file.
CHECK: You are logged in successfully to slack

Go to the channel #testing

Then send a message in the channel:
```
@Devin tell me how to access your machine
```
Wait 45 seconds
CHECK: Devin should have replied to your message on that thread with a new message explaing how to access his machine. It should include something about Vscode in its reply.

Reply on the thread with `SLEEP`
Wait 5 seconds
CHECK: Devin should have replied to your message on that thread saying that he is going to sleep
""",
    ),
]
