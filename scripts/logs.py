import csv
import threading
import time
from datetime import datetime, timedelta
from google.cloud import monitoring_v3

class ServiceAccountMetricsProcessor:
    def __init__(self, input_csv: str, output_csv: str) -> None:
        """
        Initialize the processor with input and output file paths.
        """
        self.input_csv = input_csv
        self.output_csv = output_csv
        self.processed_accounts = 0
        self.progress_lock = threading.Lock()
        self.csv_lock = threading.Lock()

    def get_service_account_metrics(self, project_id: str, service_account_unique_id: str) -> list:
        """
        Query Cloud Monitoring for metrics related to a service account.
        Returns a list of metrics and their data points.
        """
        client = monitoring_v3.MetricServiceClient()

        now = datetime.utcnow()
        interval = monitoring_v3.TimeInterval(
            end_time={"seconds": int(now.timestamp())},
            start_time={"seconds": int((now - timedelta(days=90)).timestamp())}
        )

        metric_type = "iam.googleapis.com/service_account/authn_events_count"
        filter_str = (
            f'metric.type = "{metric_type}" AND '
            f'resource.labels.unique_id = "{service_account_unique_id}"'
        )

        request = monitoring_v3.ListTimeSeriesRequest(
            name=f"projects/{project_id}",
            filter=filter_str,
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )

        response = client.list_time_series(request=request)
        metrics = []
        for time_series in response:
            points = [
                (point.interval.end_time, point.value)
                for point in time_series.points
            ]
            metrics.append((time_series.metric.type, points))
        return metrics

    def process_service_account(self, row: list, total_accounts: int) -> None:
        """
        Process a single service account and update the CSV file with the results.
        """
        project_id = row[0]
        service_account_unique_id = row[2]  # Assuming the unique ID is in the 3rd column

        try:
            metrics = self.get_service_account_metrics(project_id, service_account_unique_id)
            output = "Yes" if metrics else "No"
        except Exception as e:
            output = f"Error: {str(e)}"

        row.append(output)

        with self.csv_lock:
            with open(self.output_csv, mode="a", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(row)

        with self.progress_lock:
            self.processed_accounts += 1
            percentage = (self.processed_accounts / total_accounts) * 100

    def run(self) -> None:
        """
        Main function to process the CSV file and update it with metrics.
        """
        with open(self.input_csv, mode="r") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)

        header = rows[0] + ["Metrics"]
        with open(self.output_csv, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(header)

        total_accounts = len(rows) - 1  # Exclude header row

        threads = []
        for row in rows[1:]:
            thread = threading.Thread(
                target=self.process_service_account,
                args=(row, total_accounts)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    input_csv = "insights_with_dates.csv"
    output_csv = "insights_with_metrics.csv"
    processor = ServiceAccountMetricsProcessor(input_csv, output_csv)
    processor.run()