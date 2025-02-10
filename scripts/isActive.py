import csv
import subprocess
import threading
from queue import Queue

class ServiceAccountChecker:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.lock = threading.Lock()
        self.queue = Queue()
        self.results = []
        self.headers = []

    def get_service_account_status(self, project_id, email):
        try:
            cmd = [
                'gcloud', 'iam', 'service-accounts', 'describe', email,
                '--project', project_id,
                '--format', 'value(disabled)'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return "Disabled" if result.stdout.strip() == "True" else "Active"
            else:
                return f"Error: {result.stderr.strip()}"
                
        except Exception as e:
            return f"Exception: {str(e)}"

    def worker(self):
        while True:
            row = self.queue.get()
            if row is None:
                break
                
            project_id = row[0]
            email = row[1]
            
            if "appspot.gserviceaccount.com" in email:
                status = "System Managed"
            else:
                status = self.get_service_account_status(project_id, email)
                
            row.append(status)
            
            with self.lock:
                with open(self.output_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
                    
            self.queue.task_done()

    def process_csv(self):
        with open(self.input_file, 'r') as f:
            reader = csv.reader(f)
            self.headers = next(reader) + ['Current State']
            rows = list(reader)

        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

        num_workers = 2
        threads = []
        for _ in range(num_workers):
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)

        for row in rows:
            self.queue.put(row)

        self.queue.join()

        for _ in range(num_workers):
            self.queue.put(None)
        for t in threads:
            t.join()

if __name__ == '__main__':
    INPUT_CSV = 'insights_with_metrics.csv'
    OUTPUT_CSV = 'output_with_status.csv'
    
    checker = ServiceAccountChecker(INPUT_CSV, OUTPUT_CSV)
    checker.process_csv()
    print(f"Processing complete. Results saved to {OUTPUT_CSV}")