import subprocess
import threading
from typing import List, Optional
import json
import os 

class GCloudRecommender:
    def __init__(self, project_id: str) -> None:
        self.project_id = project_id

    def enable_api_if_needed(self) -> None:
        """Enable the recommender API if not already enabled."""
        command = [
            "gcloud", "services", "enable", "recommender.googleapis.com",
            "--project", self.project_id,
            "--quiet"
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError:
            pass

    def get_iam_insights(self) -> str:
        """Fetch IAM insights for the project and include the project ID in the JSON output."""
        
        self.enable_api_if_needed()

        
        command = [
            "gcloud", "recommender", "insights", "list",
            "--insight-type=google.iam.serviceAccount.Insight",
            "--project", self.project_id,
            "--location", "global",
            "--quiet",
            "--format=json"
        ]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            insights_data = json.loads(result.stdout.strip())  
            
            insights_data_with_project = {
                "project_id": self.project_id,
                "insights": insights_data
            }
            return json.dumps(insights_data_with_project, indent=2)  
        except subprocess.CalledProcessError as e:
            return json.dumps({"project_id": self.project_id, "error": str(e.stderr)})
        except json.JSONDecodeError as e:
            return json.dumps({"project_id": self.project_id, "error": "Failed to parse JSON output"})

class ProjectManagerWithRecommender:
    def __init__(self) -> None:
        self.lock = threading.Lock()  
    
    def save_insights(self, project_id: str, insights: str) -> None:
        """Save the IAM insights to a file."""
        with self.lock:
            with open("insights_results.txt", "a") as file:
                try:
                    file.write(insights + "\n")
                    file.write("\n")
                except Exception as e:
                    pass
    
    def fetch_and_save_insights(self, project_id: str) -> None:
        """Fetch IAM insights and save them."""
        recommender = GCloudRecommender(project_id)
        insights = recommender.get_iam_insights()
        self.save_insights(project_id, insights)
    
    def run(self) -> None:
        """Run the project manager with recommender logic."""

        try:
            with open("projects.txt", "r") as file:
                projects = [line.strip() for line in file.readlines() if line.strip()]
                
                if not projects:
                    print("No projects found in the projects.txt file.")
                    return
                
                threads: List[threading.Thread] = []
                for project_id in projects:
                    thread = threading.Thread(target=self.fetch_and_save_insights, args=(project_id,))
                    threads.append(thread)
                    thread.start()
                
                
                for thread in threads:
                    thread.join()

                print("All insights have been fetched and saved.")
        except FileNotFoundError:
            print("Error: projects.txt file not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    manager_with_recommender = ProjectManagerWithRecommender()
    manager_with_recommender.run()