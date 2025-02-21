import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import os
import time
import argparse
from collections import Counter
import webbrowser
from typing import List, Dict, Optional
import colorama
from colorama import Fore, Back, Style

class GitHubActivityViewer:
    def __init__(self):
        self.events = []
        self.page = 0
        self.events_per_page = 5
        self.user_data = None
        self.filter_type = None
        self.date_filter = None
        colorama.init()  # Initialize colorama for cross-platform colored output
        
    def initialize_argparse(self) -> argparse.ArgumentParser:
        """Set up command line argument parsing"""
        parser = argparse.ArgumentParser(description='GitHub Activity Viewer CLI')
        parser.add_argument('-u', '--username', help='GitHub username to view')
        parser.add_argument('-d', '--days', type=int, help='Filter events from last N days')
        parser.add_argument('-t', '--type', help='Filter by event type (push, create, issue, etc)')
        parser.add_argument('-n', '--num-events', type=int, help='Number of events per page')
        return parser

    def fetch_user_details(self, username: str) -> bool:
        """Fetch detailed user information"""
        url = f"https://api.github.com/users/{username}"
        try:
            request = urllib.request.Request(url, headers=self.get_headers())
            with urllib.request.urlopen(request) as response:
                self.user_data = json.loads(response.read().decode('utf-8'))
                return True
        except Exception as e:
            print(f"\nError fetching user details: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with optional GitHub token"""
        headers = {
            'User-Agent': 'GitHub-Activity-CLI/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        # Add GitHub token if available
        token = os.getenv('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    def fetch_github_activity(self, username):
        """Fetch GitHub activity for a given username"""
        url = f"https://api.github.com/users/{username}/events"
        
        try:
            request = urllib.request.Request(url, headers=self.get_headers())
            with urllib.request.urlopen(request) as response:
                self.events = json.loads(response.read().decode('utf-8'))
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"\n{Fore.RED}Error: User '{username}' not found{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}Error: Failed to fetch data (HTTP {e.code}){Style.RESET_ALL}")
            return False
        except urllib.error.URLError as e:
            print(f"\n{Fore.RED}Error: Failed to connect to GitHub API ({e.reason}){Style.RESET_ALL}")
            return False
        except json.JSONDecodeError:
            print(f"\n{Fore.RED}Error: Invalid response from GitHub API{Style.RESET_ALL}")
            return False

    def display_user_info(self):
        """Display user profile information"""
        if self.user_data:
            print(f"\n{Fore.CYAN}=== User Profile ==={Style.RESET_ALL}")
            print(f"Name: {self.user_data.get('name', 'N/A')}")
            print(f"Bio: {self.user_data.get('bio', 'N/A')}")
            print(f"Location: {self.user_data.get('location', 'N/A')}")
            print(f"Followers: {self.user_data.get('followers', 0)}")
            print(f"Following: {self.user_data.get('following', 0)}")
            print(f"Public Repos: {self.user_data.get('public_repos', 0)}")
            print("=" * 30 + "\n")

    def filter_events(self) -> List[Dict]:
        """Filter events based on type and date"""
        filtered_events = self.events

        if self.filter_type:
            filtered_events = [
                event for event in filtered_events 
                if event['type'].lower().startswith(self.filter_type.lower())
            ]

        if self.date_filter:
            cutoff_date = datetime.now() - timedelta(days=self.date_filter)
            filtered_events = [
                event for event in filtered_events
                if datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') > cutoff_date
            ]

        return filtered_events

    def show_activity_stats(self):
        """Display activity statistics"""
        if not self.events:
            return

        print(f"\n{Fore.GREEN}=== Activity Statistics ==={Style.RESET_ALL}")
        
        # Event type distribution
        event_types = Counter(event['type'] for event in self.events)
        print("\nEvent Distribution:")
        for event_type, count in event_types.most_common():
            print(f"- {event_type}: {count}")

        # Most active repositories
        repos = Counter(event['repo']['name'] for event in self.events)
        print("\nMost Active Repositories:")
        for repo, count in repos.most_common(3):
            print(f"- {repo}: {count} events")

        # Activity timeline
        print("\nRecent Activity Timeline:")
        for event in self.events[:5]:
            date = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            print(f"- {date.strftime('%Y-%m-%d %H:%M')} - {self.format_event(event)}")

        print("=" * 30 + "\n")

    def open_in_browser(self, event: Dict):
        """Open the event's repository or issue in browser"""
        if event['type'] == 'IssuesEvent':
            url = event['payload']['issue']['html_url']
        else:
            url = f"https://github.com/{event['repo']['name']}"
        webbrowser.open(url)

    def format_event(self, event: Dict) -> str:
        """Enhanced event formatting with color"""
        event_type = event['type']
        repo_name = event['repo']['name']
        
        if event_type == 'PushEvent':
            commits = event.get('payload', {}).get('commits', [])
            return f"{Fore.GREEN}Pushed {len(commits)} commits to {repo_name}{Style.RESET_ALL}"
        elif event_type == 'CreateEvent':
            ref_type = event.get('payload', {}).get('ref_type', 'unknown')
            return f"{Fore.BLUE}Created {ref_type} in {repo_name}{Style.RESET_ALL}"
        elif event_type == 'IssuesEvent':
            action = event.get('payload', {}).get('action', 'unknown')
            issue_number = event.get('payload', {}).get('issue', {}).get('number', 'unknown')
            return f"{Fore.YELLOW}{action.capitalize()} issue #{issue_number} in {repo_name}{Style.RESET_ALL}"
        elif event_type == 'WatchEvent':
            return f"{Fore.MAGENTA}Starred {repo_name}{Style.RESET_ALL}"
        elif event_type == 'ForkEvent':
            return f"{Fore.CYAN}Forked {repo_name}{Style.RESET_ALL}"
        
        return f"{event_type} in {repo_name}"

    def get_event_details(self, event: Dict) -> List[str]:
        """Enhanced event details with additional information"""
        details = []
        event_type = event['type']
        repo_name = event['repo']['name']
        created_at = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

        details.append(f"Event Type: {event_type}")
        details.append(f"Repository: {repo_name}")
        details.append(f"Date: {date_str}")
        
        # Add repository URL
        details.append(f"\nRepository URL: https://github.com/{event['repo']['name']}")
        
        if event_type == 'PushEvent':
            # Add commit stats
            payload = event.get('payload', {})
            commits = payload.get('commits', [])
            details.append(f"\nNumber of commits: {len(commits)}")
            details.append(f"Branch: {payload.get('ref', 'unknown').split('/')[-1]}")
            details.append(f"Size: {payload.get('size', 0)} commits")
            details.append(f"Distinct commits: {payload.get('distinct_size', 0)}")
            details.append("\nCommit messages:")
            for commit in commits:
                details.append(f"- {commit.get('message', 'No message')}")

        elif event_type == 'IssuesEvent':
            # Add issue details
            issue = event.get('payload', {}).get('issue', {})
            action = event.get('payload', {}).get('action', 'unknown')
            details.append(f"Action: {action}")
            details.append(f"Issue number: #{issue.get('number')}")
            details.append(f"Title: {issue.get('title')}")
            details.append(f"\nIssue URL: {issue.get('html_url', 'N/A')}")
            details.append(f"Labels: {', '.join(label['name'] for label in issue.get('labels', []))}")
            details.append(f"State: {issue.get('state', 'unknown')}")
            
        return details

    def display_help(self):
        """Display enhanced help menu"""
        print(f"\n{Fore.CYAN}=== Available Commands ==={Style.RESET_ALL}")
        print("n - Next page")
        print("p - Previous page")
        print("1-5 - View event details")
        print("f - Set event type filter")
        print("d - Set date filter")
        print("s - Show statistics")
        print("o - Open current page in browser")
        print("r - Refresh data")
        print("h - Show this help")
        print("q - Quit")
        input("\nPress Enter to continue...")

    def display_page(self):
        """Display current page of events"""
        filtered_events = self.filter_events()
        start_idx = self.page * self.events_per_page
        end_idx = min(start_idx + self.events_per_page, len(filtered_events))

        self.clear_screen()
        print(f"\n{Fore.CYAN}=== GitHub Activity Viewer ==={Style.RESET_ALL}")
        print(f"Page {self.page + 1} of {(len(filtered_events) - 1) // self.events_per_page + 1}")
        print("=" * 30 + "\n")

        if self.filter_type:
            print(f"Filter: {self.filter_type}")
        if self.date_filter:
            print(f"Showing last {self.date_filter} days")

        for i, event in enumerate(filtered_events[start_idx:end_idx], 1):
            print(f"{i}. {self.format_event(event)}")

        print(f"\n{Fore.CYAN}Commands:{Style.RESET_ALL}")
        print("n - Next page | p - Previous page | h - Help | q - Quit")
        print("1-5 - View event details | f - Filter | s - Stats")
        print("\nEnter command: ", end='')

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def handle_command(self, command: str):
        """Handle user commands"""
        if command == 'n':
            filtered_events = self.filter_events()
            if (self.page + 1) * self.events_per_page < len(filtered_events):
                self.page += 1
        elif command == 'p':
            if self.page > 0:
                self.page -= 1
        elif command.isdigit():
            event_num = int(command)
            if 1 <= event_num <= self.events_per_page:
                self.show_event_details(event_num)
        else:
            print(f"{Fore.RED}Invalid command{Style.RESET_ALL}")
            time.sleep(1)

    def show_event_details(self, event_number: int):
        """Show detailed information about a specific event"""
        filtered_events = self.filter_events()
        event_idx = self.page * self.events_per_page + event_number - 1
        
        if 0 <= event_idx < len(filtered_events):
            event = filtered_events[event_idx]
            details = self.get_event_details(event)
            
            self.clear_screen()
            print(f"\n{Fore.CYAN}=== Event Details ==={Style.RESET_ALL}")
            print("=" * 30 + "\n")
            
            for detail in details:
                print(detail)
            
            input("\nPress Enter to go back...")
        else:
            print(f"{Fore.RED}Invalid event number{Style.RESET_ALL}")
            time.sleep(1)

    def run(self):
        """Enhanced main application loop"""
        parser = self.initialize_argparse()
        args = parser.parse_args()

        username = args.username or input("Enter GitHub username: ")
        if args.num_events:
            self.events_per_page = args.num_events
        if args.type:
            self.filter_type = args.type
        if args.days:
            self.date_filter = args.days

        if not self.fetch_github_activity(username):
            input("\nPress Enter to exit...")
            return

        # Fetch user details synchronously
        self.fetch_user_details(username)

        while True:
            self.display_user_info()
            self.display_page()
            command = input().lower()

            if command == 'q':
                break
            elif command == 'h':
                self.display_help()
            elif command == 's':
                self.show_activity_stats()
                input("Press Enter to continue...")
            elif command == 'f':
                self.filter_type = input("Enter event type filter (or empty to clear): ").strip()
            elif command == 'd':
                days = input("Enter number of days to filter (or empty to clear): ").strip()
                self.date_filter = int(days) if days.isdigit() else None
            elif command == 'r':
                self.fetch_github_activity(username)
            elif command == 'o':
                # Open current page events in browser
                start_idx = self.page * self.events_per_page
                filtered_events = self.filter_events()
                end_idx = min(start_idx + self.events_per_page, len(filtered_events))
                for event in filtered_events[start_idx:end_idx]:
                    self.open_in_browser(event)
            else:
                self.handle_command(command)


def main():
    try:
        viewer = GitHubActivityViewer()
        viewer.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
