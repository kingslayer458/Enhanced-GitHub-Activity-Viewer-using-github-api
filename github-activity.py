#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
import os
import time

class GitHubActivityViewer:
    def __init__(self):
        self.events = []
        self.page = 0
        self.events_per_page = 5

    def clear_screen(self):
        """Clear the console screen on both Windows and Unix systems"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def fetch_github_activity(self, username):
        """Fetch GitHub activity for a given username"""
        url = f"https://api.github.com/users/{username}/events"
        headers = {
            'User-Agent': 'GitHub-Activity-CLI/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }

        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request) as response:
                self.events = json.loads(response.read().decode('utf-8'))
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"\nError: User '{username}' not found")
            else:
                print(f"\nError: Failed to fetch data (HTTP {e.code})")
            return False
        except urllib.error.URLError as e:
            print(f"\nError: Failed to connect to GitHub API ({e.reason})")
            return False
        except json.JSONDecodeError:
            print("\nError: Invalid response from GitHub API")
            return False

    def format_event(self, event):
        """Format a GitHub event into a readable string"""
        event_type = event['type']
        repo_name = event['repo']['name']
        created_at = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

        if event_type == 'PushEvent':
            commits = event.get('payload', {}).get('commits', [])
            return f"Pushed {len(commits)} commits to {repo_name}"
        elif event_type == 'CreateEvent':
            ref_type = event.get('payload', {}).get('ref_type', 'unknown')
            return f"Created {ref_type} in {repo_name}"
        elif event_type == 'IssuesEvent':
            action = event.get('payload', {}).get('action', 'unknown')
            issue_number = event.get('payload', {}).get('issue', {}).get('number', 'unknown')
            return f"{action.capitalize()} issue #{issue_number} in {repo_name}"
        elif event_type == 'WatchEvent':
            return f"Starred {repo_name}"
        elif event_type == 'ForkEvent':
            return f"Forked {repo_name}"
        
        return f"{event_type} in {repo_name}"

    def get_event_details(self, event):
        """Get detailed information about an event"""
        details = []
        event_type = event['type']
        repo_name = event['repo']['name']
        created_at = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

        details.append(f"Event Type: {event_type}")
        details.append(f"Repository: {repo_name}")
        details.append(f"Date: {date_str}")

        if event_type == 'PushEvent':
            commits = event.get('payload', {}).get('commits', [])
            details.append(f"Number of commits: {len(commits)}")
            details.append("\nCommit messages:")
            for commit in commits:
                details.append(f"- {commit.get('message', 'No message')}")

        elif event_type == 'IssuesEvent':
            issue = event.get('payload', {}).get('issue', {})
            action = event.get('payload', {}).get('action', 'unknown')
            details.append(f"Action: {action}")
            details.append(f"Issue number: #{issue.get('number')}")
            details.append(f"Title: {issue.get('title')}")

        return details

    def display_page(self):
        """Display current page of events"""
        start_idx = self.page * self.events_per_page
        end_idx = min(start_idx + self.events_per_page, len(self.events))

        self.clear_screen()
        print("\n=== GitHub Activity Viewer ===")
        print(f"Page {self.page + 1} of {(len(self.events) - 1) // self.events_per_page + 1}")
        print("=" * 30 + "\n")

        for i, event in enumerate(self.events[start_idx:end_idx], 1):
            print(f"{i}. {self.format_event(event)}")

        print("\nCommands:")
        print("n - Next page")
        print("p - Previous page")
        print("1-5 - View event details")
        print("q - Quit")
        print("\nEnter command: ", end='')

    def show_event_details(self, event_number):
        """Show detailed information about a specific event"""
        event_idx = self.page * self.events_per_page + event_number - 1
        if 0 <= event_idx < len(self.events):
            event = self.events[event_idx]
            details = self.get_event_details(event)
            
            self.clear_screen()
            print("\n=== Event Details ===")
            print("=" * 30 + "\n")
            
            for detail in details:
                print(detail)
            
            input("\nPress Enter to go back...")
        else:
            print("Invalid event number")
            time.sleep(1)

    def run(self):
        """Main application loop"""
        username = input("Enter GitHub username: ")
        if not self.fetch_github_activity(username):
            input("\nPress Enter to exit...")
            return

        while True:
            self.display_page()
            command = input().lower()

            if command == 'q':
                break
            elif command == 'n':
                if (self.page + 1) * self.events_per_page < len(self.events):
                    self.page += 1
            elif command == 'p':
                if self.page > 0:
                    self.page -= 1
            elif command.isdigit():
                event_num = int(command)
                if 1 <= event_num <= self.events_per_page:
                    self.show_event_details(event_num)
            else:
                print("Invalid command")
                time.sleep(1)

def main():
    viewer = GitHubActivityViewer()
    viewer.run()

if __name__ == "__main__":
    main()