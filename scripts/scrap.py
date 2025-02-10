import json
import csv
from datetime import datetime

class InsightsParser:
    def __init__(self, input_file: str, output_file: str) -> None:
        """
        Initialize the InsightsParser with input and output file paths.
        """
        self.input_file = input_file
        self.output_file = output_file

    def parse_insights(self) -> list:
        """
        Parse the insights file and return a list of rows for the CSV.
        """
        csv_data = []
        try:
            with open(self.input_file, "r") as file:
                data = file.read().strip()
                json_objects = data.split("\n\n")
                
                for json_str in json_objects:
                    if not json_str.strip():
                        continue  # Skip empty lines
                    
                    try:
                        insights_data = json.loads(json_str)
                        project_id = insights_data.get("project_id", "UNKNOWN_PROJECT")
                        insights = insights_data.get("insights", [])
                        
                        for insight in insights:
                            if "content" in insight and "email" in insight["content"]:
                                service_account_email = insight["content"]["email"]
                                description = insight.get("description", "")
                                
                                alert = "Yes" if "was inactive." in description else "No"
                                
                                last_authenticated_time = insight["content"].get("lastAuthenticatedTime")
                                service_account_id = insight["content"].get("serviceAccountId")
                                
                                if last_authenticated_time:
                                    formatted_date = datetime.strptime(
                                        last_authenticated_time, "%Y-%m-%dT%H:%M:%SZ"
                                    ).strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                    formatted_date = "N/A"
                                
                                csv_data.append([project_id, service_account_email, service_account_id, alert, formatted_date])
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        continue
        except FileNotFoundError:
            print(f"Error: File '{self.input_file}' not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        return csv_data

    def save_to_csv(self, csv_data: list) -> None:
        """
        Save the parsed data to a CSV file.
        """
        try:
            with open(self.output_file, mode="w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Project ID", "Service Account Email", "Service Account ID", "Alert (Inactive)", "Last Authenticated Time"])
                writer.writerows(csv_data)
            print(f"Results saved to {self.output_file}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def run(self) -> None:
        """
        Run the parser and save the results to a CSV file.
        """
        csv_data = self.parse_insights()
        if csv_data:
            self.save_to_csv(csv_data)

if __name__ == "__main__":
    input_file = "insights_results.txt"
    output_file = "insights_with_dates.csv"
    
    parser = InsightsParser(input_file, output_file)
    parser.run()