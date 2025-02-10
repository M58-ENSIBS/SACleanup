import csv
import requests
import subprocess
import time
from datetime import datetime
import os 


slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

class SlackNotifier:
    def __init__(self, webhook_url: str):
        """
        Initialize the SlackNotifier with a webhook URL.
        """
        self.webhook_url = webhook_url

    def send_message(self, blocks: list) -> None:
        """
        Send a rich message to Slack using Block Kit.
        """
        payload = {"blocks": blocks}
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 200:
                print("Slack notification sent successfully.")
            else:
                print(f"Failed to send Slack notification. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending Slack notification: {e}")


def run_scripts():
    """
    Run the scripts in order and return the total time taken.
    """
    scripts = ["list_insights.py", "scrap.py", "logs.py", "isActive.py"]
    start_time = time.time()

    for script in scripts:
        os.system(f"echo 'Running {script}'")
        os.system("ls -al && wc -l *")
        try:
            subprocess.run(["python3", script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")
        except FileNotFoundError:
            print(f"Script not found: {script}")

    end_time = time.time()
    total_time = end_time - start_time
    return total_time

def create_slack_blocks(today_date: str, total_time: float, unused_count: int) -> list:
    """
    Create a fancy Slack message using Block Kit.
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 Service Account Analysis Report",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{today_date}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Total Time Taken:*\n{total_time:.2f} seconds"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Number of Unused Service Accounts:*\n{unused_count}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "✅ Analysis completed successfully."
                }
            ]
        }
    ]

def main():
    try:
        subprocess.run(["rm", "insights_results.txt", "insights_with_metrics.csv", "insights_with_dates.csv", "output_with_status.csv"], 
            check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        pass
    csv_file = "output_with_status.csv"

    notifier = SlackNotifier(slack_webhook_url)

    total_time = run_scripts()
    print(f"Total time taken: {total_time:.2f} seconds")

    try:
        with open(csv_file, "r", newline="") as file:
            unused_count = sum(1 for _ in csv.reader(file)) - 1  # Enlever l'en-tête si présent
    except FileNotFoundError:
        unused_count = 0
    
    print(f"Number of unused service accounts: {unused_count}")

    today_date = datetime.now().strftime("%Y-%m-%d")
    blocks = create_slack_blocks(today_date, total_time, unused_count)

    notifier.send_message(blocks)

if __name__ == "__main__":
    main()