import argparse
import asyncio
import os
import sys
import time
from typing import TypedDict

from dotenv import load_dotenv
from slack_sdk import WebClient
from tests import QA_TESTS

from devin_api_client import DevinAPIClient, DevinAPISessionStatusResponse

# Load environment variables from .env file
load_dotenv()

# Default Slack channel for test results
SLACK_TEST_RESULTS_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "test-results")

DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
if not DEVIN_API_KEY:
    raise ValueError("DEVIN_API_KEY environment variable is required")

devin_api_client = DevinAPIClient(DEVIN_API_KEY)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
slack_client = WebClient(token=SLACK_BOT_TOKEN)


class QATestResult(TypedDict):
    test_name: str
    session_id: str
    session_url: str
    status_enum: str
    success: bool
    message: str


MAX_TIME_PER_TEST = 30 * 60  # 30 minutes


async def poll_session_and_eval(
    test_name: str, session_id: str, session_url: str
) -> QATestResult:
    status = None
    start_time = time.time()
    while True:
        status: DevinAPISessionStatusResponse | None = (
            await devin_api_client.get_session_status(session_id)
        )
        if (
            status
            and status["status_enum"] is not None
            and status["status_enum"].lower() in ["blocked", "stopped"]
        ):
            break

        if time.time() - start_time > MAX_TIME_PER_TEST:
            break
        await asyncio.sleep(20)

    if not status or not status["structured_output"]:
        return {
            "test_name": test_name,
            "session_id": session_id,
            "session_url": session_url,
            "status_enum": (
                status["status_enum"] or "unknown" if status else "never_started"
            ),
            "success": False,
            "message": "No structured IO",
        }

    success: bool = status["structured_output"].get("success", False)
    message: str = status["structured_output"].get("message", "")
    x: QATestResult = {
        "test_name": test_name,
        "session_id": session_id,
        "session_url": session_url,
        "status_enum": status["status_enum"] or "unknown",
        "success": success,
        "message": message,
    }
    print(f"Test finished: {x}")
    return x


async def send_final_results_to_slack(results: list[QATestResult]):
    # Post session links to slack
    slack_summary = "*QA Test Results*\n"
    slack_summary += f"*Command*: `python3 {' '.join(sys.argv)}`\n"
    slack_summary += "-" * 100 + "\n"

    # Add results to summary
    for result in results:
        emoji = "✅" if result["success"] else "❌"
        slack_summary += f"{emoji} *<{result['session_url']}|{result['test_name']}>*\n"

    thread_ts = None
    if SLACK_BOT_TOKEN:
        main_message = slack_client.chat_postMessage(
            channel=SLACK_TEST_RESULTS_CHANNEL_ID,
            text=slack_summary,
        )
        print(main_message)

        # Post detailed results in thread
        thread_ts = main_message["ts"]

    for result in results:
        thread_message = (
            f"Detailed results for <{result['session_url']}|{result['test_name']}>:\n"
        )
        thread_message += f"Status: {result['status_enum']}\n"
        if result["message"]:
            thread_message += f"Message: {result['message']}\n"

        if SLACK_BOT_TOKEN and thread_ts:
            slack_client.chat_postMessage(
                channel=SLACK_TEST_RESULTS_CHANNEL_ID,
                thread_ts=thread_ts,
                text=thread_message,
            )
        print(thread_message)


async def run_tests_and_send_to_slack(
    url: str,
    test_names: list[str] | None,
):
    eval_tasks = []
    session_links: list[tuple[str, str, str]] = []
    for test in QA_TESTS:
        if test_names and test["test_name"] not in test_names:
            continue
        prompt = test["user_prompt"].format(url=url)
        session_response = await devin_api_client.start_session(prompt)
        assert session_response["session_id"] is not None
        session_id = session_response["session_id"]
        session_url = session_response["url"]

        eval_tasks.append(
            asyncio.create_task(
                poll_session_and_eval(test["test_name"], session_id, session_url)
            )
        )
        session_links.append((session_id, session_url, test["test_name"]))
        await asyncio.sleep(0.1)
    print("Done starting sessions")

    # Send initial message with session links
    links_message = "*Started QA Test Sessions*\n"
    links_message += f"*Command*: `python3 {' '.join(sys.argv)}`\n"
    links_message += "-" * 100 + "\n"
    for _, session_url, test_name in session_links:
        links_message += f"• <{session_url}|{test_name}>\n"

    print(links_message)

    if SLACK_BOT_TOKEN:
        slack_client.chat_postMessage(
            channel=SLACK_TEST_RESULTS_CHANNEL_ID, text=links_message
        )

    # Use return_exceptions=True to prevent exceptions from stopping other tasks
    results = await asyncio.gather(*eval_tasks, return_exceptions=True)

    # Filter out exceptions and convert them to error results
    processed_results: list[QATestResult] = []
    for result, (session_id, session_url, test_name) in zip(results, session_links):
        if isinstance(result, Exception):
            processed_results.append(
                {
                    "test_name": test_name,
                    "session_id": session_id,
                    "session_url": session_url,
                    "status_enum": "error",
                    "success": False,
                    "message": f"Test failed with exception: {str(result)}",
                }
            )
        elif isinstance(result, dict):
            processed_results.append(QATestResult(**result))
        else:
            raise ValueError(f"Unknown result type: {type(result)}")

    await send_final_results_to_slack(processed_results)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tests", type=str, help="Comma separated test names to run", default=None
    )
    parser.add_argument(
        "--url", type=str, help="Base URL for Devin", default="app.devin.ai"
    )
    args = parser.parse_args()

    test_names = args.tests.split(",") if args.tests else None
    await run_tests_and_send_to_slack(url=args.url, test_names=test_names)


if __name__ == "__main__":
    asyncio.run(main())
