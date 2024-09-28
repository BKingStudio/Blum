import requests
import json
import time
import os
import random
from colorama import Fore, Style, init
import signal
import sys
from datetime import datetime
from urllib.parse import parse_qs

# Initialize Colorama
init(autoreset=True)

# Helper function to get headers for requests
def get_headers(token):
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ])
    }

# Function to parse username from query ID
def parse_username_from_query(query):
    try:
        parsed_query = parse_qs(query)
        user_info = parsed_query.get('user', [None])[0]
        if user_info:
            user_info = json.loads(user_info)
            return user_info.get('username', 'Unknown')
    except Exception as e:
        print(f"{Fore.RED}Error parsing username from query: {e}{Style.RESET_ALL}")
    return 'Unknown'

# Function to get tasks from the API
def get_task(token, proxies=None):
    url = "https://earn-domain.blum.codes/api/v1/tasks"
    try:
        response = requests.get(
            url=url, headers=get_headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()
        return data
    except Exception as e:
        print(f"{Fore.RED}Error fetching tasks: {e}{Style.RESET_ALL}")
        return []

# Function to start a task
def start_task(token, task_id, proxies=None):
    url = f"https://earn-domain.blum.codes/api/v1/tasks/{task_id}/start"
    try:
        response = requests.post(
            url=url,
            headers=get_headers(token=token),
            json={},
            proxies=proxies,
            timeout=20,
        )
        countdown_timer(random.randint(1, 2))
        return response.json()
    except Exception as e:
        return None

# Function to claim a task
def claim_task(token, task_id, proxies=None):
    url = f"https://earn-domain.blum.codes/api/v1/tasks/{task_id}/claim"
    try:
        response = requests.post(
            url=url,
            headers=get_headers(token=token),
            json={},
            proxies=proxies,
            timeout=20,
        )
        countdown_timer(random.randint(1, 2))
        return response.json().get("status")
    except Exception as e:
        return None

# Function to validate a task with a keyword
def validate_task(token, task_id, keyword, proxies=None):
    url = f"https://earn-domain.blum.codes/api/v1/tasks/{task_id}/validate"
    try:
        response = requests.post(
            url=url,
            headers=get_headers(token=token),
            json={"keyword": keyword},
            proxies=proxies,
            timeout=20,
        )
        countdown_timer(random.randint(1, 2))
        return response.json().get("status") == "READY_FOR_CLAIM"
    except Exception as e:
        return False

# Function to get a keyword from a file based on a task name
def get_value_from_title(filename, target_title):
    try:
        with open(filename, "r") as file:
            for line in file:
                if ":" in line:
                    title, value = line.split(":", 1)
                    if title.strip() == target_title:
                        return value.strip()
    except FileNotFoundError:
        print(f"{Fore.RED}Keyword file '{filename}' not found.{Style.RESET_ALL}")
    return None

# Function to handle a specific task
def do_task(token, task_id, task_name, task_status, keyword_file, proxies=None):
    if task_status == "FINISHED":
        print(f"{Fore.RED}{task_name}: Completed Already!{Style.RESET_ALL}")
    elif task_status == "READY_FOR_CLAIM":
        claim_status = claim_task(token=token, task_id=task_id, proxies=proxies)
        if claim_status == "FINISHED":
            print(f"{Fore.GREEN}{task_name}: Claim Success{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{task_name}: Claim Fail{Style.RESET_ALL}")
    elif task_status == "NOT_STARTED":
        start = start_task(token=token, task_id=task_id, proxies=proxies)
        if start and start.get("status") == "STARTED":
            print(f"{Fore.GREEN}{task_name}: Start Success{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{task_name}: Start Fail{Style.RESET_ALL}")
    elif task_status == "STARTED":
        print(f"{Fore.RED}{task_name}: Started but not ready to claim{Style.RESET_ALL}")
    elif task_status == "READY_FOR_VERIFY":
        # Start the task before validation
        start_task(token=token, task_id=task_id, proxies=proxies)
        keyword = get_value_from_title(filename=keyword_file, target_title=task_name)
        if keyword:
            validate_status = validate_task(token=token, task_id=task_id, keyword=keyword, proxies=proxies)
            if validate_status:
                claim_status = claim_task(token=token, task_id=task_id, proxies=proxies)
                if claim_status == "FINISHED":
                    print(f"{Fore.GREEN}{task_name}: Claim Success{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}{task_name}: Claim Fail{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}{task_name}: Validate Fail{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{task_name}: Keyword not found{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}{task_name}: Unknown Status - {task_status}{Style.RESET_ALL}")

# Function to process specific tasks
def process_specific_tasks(token, keyword_file, task_ids, proxies=None):
    try:
        earn_section = get_task(token=token, proxies=proxies)
        if not earn_section:
            print(f"{Fore.RED}No tasks fetched. Exiting task processing.{Style.RESET_ALL}")
            return

        processed_ids = set()  # To keep track of already processed task IDs
        for earn in earn_section:
            tasks = earn.get("tasks", []) + earn.get("subSections", [])
            for task in tasks:
                if isinstance(task, dict):
                    sub_tasks = task.get("tasks", task.get("subTasks", []))
                    for sub_task in sub_tasks:
                        task_id = sub_task["id"]
                        if task_id in task_ids and task_id not in processed_ids:
                            task_name = sub_task["title"]
                            task_status = sub_task["status"]
                            do_task(
                                token=token,
                                task_id=task_id,
                                task_name=task_name,
                                task_status=task_status,
                                keyword_file=keyword_file,
                                proxies=proxies,
                            )
                            random_delay = random.randint(3, 5)
                            countdown_timer(random_delay)
                            processed_ids.add(task_id)
                else:
                    task_id = task["id"]
                    if task_id in task_ids and task_id not in processed_ids:
                        task_name = task["title"]
                        task_status = task["status"]
                        do_task(
                            token=token,
                            task_id=task_id,
                            task_name=task_name,
                            task_status=task_status,
                            keyword_file=keyword_file,
                            proxies=proxies,
                        )
                        random_delay = random.randint(3, 5)
                        countdown_timer(random_delay)
                        processed_ids.add(task_id)
    except Exception as e:
        print(f"{Fore.RED}Error processing specific tasks: {e}{Style.RESET_ALL}")

# Existing functions to clear terminal and print ASCII art
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def art():
    print(Fore.GREEN + Style.BRIGHT + r"""
   ______ __  __ __               _______ __            __ __
  |   __ \  |/  |__|.-----.-----.|     __|  |_.--.--.--|  |__|.-----.
  |   __ <     <|  ||     |  _  ||__     |   _|  |  |  _  |  ||  _  |
  |______/__|\__|__||__|__|___  ||_______|____|_____|_____|__||_____|
                          |_____|
  
    """ + Style.RESET_ALL)   

    print(Fore.CYAN + " This Script is Not For Sale \n Join our Telegram Channel: @BKingStudio" + Style.RESET_ALL)

# Function to get query IDs from a file
def get_query_ids_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            query_ids = [line.strip() for line in file.readlines()]
            return query_ids
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

# Function to save a token to a file
def save_token(token, file_path):
    try:
        with open(file_path, 'w') as file:
            file.write(token)
    except Exception as e:
        print(f"Error saving token: {e}")

# Function to clear the token file
def clear_token_file(file_path):
    try:
        with open(file_path, 'w') as file:
            file.write('')  # Clear the file content
        print(f"{Fore.GREEN + Style.BRIGHT}Token file cleared successfully.")
    except Exception as e:
        print(f"Error clearing token file: {e}")

# Function to get a new token
def get_new_token(query_id):
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://telegram.blum.codes",
        "referer": "https://telegram.blum.codes/",
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ])
    }
    data = json.dumps({"query": query_id})
    url = "https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP"

    while True:
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                response_json = response.json()
                token = response_json.get('token', {}).get('refresh', None)
                if token:
                    return token
            countdown_timer(random.randint(5, 10))
        except requests.exceptions.RequestException:
            clear_terminal()
            art()
            print(f"{Fore.RED + Style.BRIGHT}Network Problem")
            countdown_timer(5)

# Function to claim farming
def claim_farming(token):
    url = "https://game-domain.blum.codes/api/v1/farming/claim"
    headers = get_headers(token)
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print(f"{Fore.GREEN + Style.BRIGHT}Farming Claimed Successfully [✓]")
            return True
        elif response.status_code == 425:
            print(f"{Fore.RED + Style.BRIGHT}Farming Already Claimed [✓]")
            return False
    except requests.exceptions.RequestException:
        pass
    return False

# Function to check farming status
def check_farming_status(token):
    url = "https://game-domain.blum.codes/api/v1/user/balance"
    headers = get_headers(token)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            timestamp = data.get("timestamp", 0) / 1000
            end_farming = data.get("farming", {}).get("endTime", 0) / 1000
            return timestamp > end_farming or end_farming == 0
    except requests.exceptions.RequestException:
        pass
    return False

# Function to start farming
def start_farming(token):
    if check_farming_status(token):
        url_farming = "https://game-domain.blum.codes/api/v1/farming/start"
        headers = get_headers(token)
        try:
            response = requests.post(url_farming, headers=headers)
            if response.status_code == 200:
                data = response.json()
                end_time = data.get("endTime", None)
                if end_time:
                    end_date = datetime.fromtimestamp(end_time / 1000)
                    print(f"{Fore.GREEN + Style.BRIGHT}Farming Successfully Started [✓]")
                    print(f"{Fore.GREEN + Style.BRIGHT}End Farming: {end_date}")
                    return end_date
            elif response.status_code == 425:
                print(f"{Fore.RED + Style.BRIGHT}Farming Already Started [✓]")
        except requests.exceptions.RequestException:
            print(f"{Fore.RED + Style.BRIGHT}Network error during farming start")
            countdown_timer(5)
    else:
        print(f"{Fore.RED + Style.BRIGHT}Farming Already Started [✓]")

# Function to get daily reward
def get_daily_reward(token):
    url = "https://game-domain.blum.codes/api/v1/daily-reward"
    headers = get_headers(token)
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            print(f"{Fore.GREEN + Style.BRIGHT}Daily Reward Claimed Successfully [✓]{Style.RESET_ALL}")
            countdown_timer(random.randint(2, 3))
            return True
        elif response.status_code == 400:
            print(f"{Fore.RED + Style.BRIGHT}Daily Reward Already Claimed [✓]{Style.RESET_ALL}")
            return False
    except requests.exceptions.RequestException:
        pass
    return False

# Function to check if it's time for daily reward
def check_daily_reward_time():
    current_time = datetime.now()
    target_time = current_time.replace(hour=11, minute=30, second=0, microsecond=0)
    return current_time >= target_time

# Function to get new balance
def new_balance(token):
    url = "https://game-domain.blum.codes/api/v1/user/balance"
    headers = get_headers(token)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data_balance = response.json()
            new_balance = data_balance.get("availableBalance", "N/A")
            play_passes = data_balance.get("playPasses", 0)
            return new_balance, play_passes
        else:
            countdown_timer(random.randint(5, 10))
    except requests.exceptions.RequestException:
        countdown_timer(random.randint(5, 10))
    return None, None

# Function to play a game
def play_game(token):
    url = "https://game-domain.blum.codes/api/v1/game/play"
    headers = get_headers(token)
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            gameid = data.get("gameId")
            if gameid:
                print(f"{Fore.YELLOW + Style.BRIGHT}Game Started....")
                countdown_timer(32)
                return gameid
    except requests.exceptions.RequestException:
        countdown_timer(random.randint(5, 10))
    return None

# Function to claim game rewards
def claim_game(token, gameId, points):
    url = "https://game-domain.blum.codes/api/v1/game/claim"
    headers = get_headers(token)
    body = {"gameId": gameId, "points": points}

    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            print(f"{Fore.GREEN + Style.BRIGHT}Game Reward Claimed Successfully: {points} points [✓]")
            return points
    except requests.exceptions.RequestException:
        countdown_timer(random.randint(5, 10))
    return 0

# Function to solve tasks
def solve_task(token):
    url_task = "https://earn-domain.blum.codes/api/v1/tasks"
    headers = get_headers(token)
    try:
        res = requests.get(url_task, headers=headers)
        task_data = res.json()
        for tasks in task_data:
            if isinstance(tasks, str):
                print(f"{Fore.YELLOW + Style.BRIGHT}Failed to get task list!")
                return
            for k in list(tasks.keys()):
                if k != "tasks" and k != "subSections":
                    continue
                subtasks = tasks.get(k)
                if subtasks is not None:
                    for t in subtasks:
                        if isinstance(t, dict):
                            sub_task_list = t.get("subTasks")
                            if sub_task_list is not None:
                                for task in sub_task_list:
                                    solve(task, token)
                                solve(t, token)
                                continue
                        task_list = t.get("tasks")
                        if task_list is not None:
                            for task in task_list:
                                solve(task, token)
                        else:
                            print(f"{Fore.RED + Style.BRIGHT}No tasks found in the response.")
    except json.JSONDecodeError:
        print(f"{Fore.RED + Style.BRIGHT}Failed to decode JSON response from tasks API.")
    except requests.exceptions.RequestException:
        print(f"{Fore.RED + Style.BRIGHT}Failed to fetch tasks due to a network error.")
        countdown_timer(random.randint(5, 10))

# Function to solve a specific task
def solve(task, token):
    headers = get_headers(token)
    task_id = task.get("id")  # Use task id
    task_name = task.get("title", "Unnamed Task")  # Use task name
    task_status = task.get("status")
    start_task_url = f"https://earn-domain.blum.codes/api/v1/tasks/{task_id}/start"
    claim_task_url = f"https://earn-domain.blum.codes/api/v1/tasks/{task_id}/claim"
    if task_status == "FINISHED":
        print(f"{Fore.RED}Already complete task: {task_name} [✓]!")
        return
    if task_status == "READY_FOR_CLAIM":
        res = requests.post(claim_task_url, headers=headers)
        if res.json().get("status") == "FINISHED":
            print(f"{Fore.GREEN}Success complete task: {task_name} [✓]!")
            return
    res = requests.post(start_task_url, headers=headers)
    delay = random.uniform(2, 5)
    countdown_timer(int(delay))  # Random delay between requests
    if res.json().get("status") == "STARTED":
        res = requests.post(claim_task_url, headers=headers)
        if res.json().get("status") == "FINISHED":
            print(f"{Fore.GREEN}Success complete task: {task_name} [✓]!")

# Function to solve specific tasks
def solve_specific_tasks(token, task_ids):
    url_task = "https://earn-domain.blum.codes/api/v1/tasks"
    headers = get_headers(token)
    try:
        res = requests.get(url_task, headers=headers)
        task_data = res.json()
        for tasks in task_data:
            if isinstance(tasks, str):
                print(f"{Fore.YELLOW + Style.BRIGHT}Failed to get task list!")
                return
            for k in list(tasks.keys()):
                if k != "tasks" and k != "subSections":
                    continue
                subtasks = tasks.get(k)
                if subtasks is not None:
                    for t in subtasks:
                        if isinstance(t, dict):
                            sub_task_list = t.get("subTasks")
                            if sub_task_list is not None:
                                for task in sub_task_list:
                                    if task.get("id") in task_ids:
                                        solve(task, token)
                                continue
                        task_list = t.get("tasks")
                        if task_list is not None:
                            for task in task_list:
                                if task.get("id") in task_ids:
                                    solve(task, token)
                        else:
                            print(f"{Fore.RED + Style.BRIGHT}No tasks found in the response.")
    except json.JSONDecodeError:
        print(f"{Fore.RED + Style.BRIGHT}Failed to decode JSON response from tasks API.")
    except requests.exceptions.RequestException:
        print(f"{Fore.RED + Style.BRIGHT}Failed to fetch tasks due to a network error.")
        countdown_timer(random.randint(5, 10))

# Function for countdown timer
def countdown_timer(seconds):
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        hours, mins = divmod(mins, 60)
        print(f"{Fore.CYAN + Style.BRIGHT}Wait {hours:02}:{mins:02}:{secs:02}", end='\r')
        time.sleep(1)
    print(' ' * 40, end='\r')  # Clears the line after the countdown
    print(f"{Fore.GREEN + Style.BRIGHT}Timer ended. Proceeding...")

# Function to handle signals
def signal_handler(sig, frame):
    print("\nExiting gracefully...")
    sys.exit(0)

# Function to display all tasks for a single account
def display_all_tasks_for_single_account(token):
    tasks_data = get_task(token=token)
    if tasks_data:
        print(f"{Fore.GREEN + Style.BRIGHT}Tasks for the Account:")
        for task_group in tasks_data:
            if "tasks" in task_group:
                tasks = task_group["tasks"]
                for task in tasks:
                    task_id = task.get("id", "N/A")
                    task_name = task.get("title", "N/A")
                    print(f"Task ID: {Fore.YELLOW + task_id + Fore.RESET}, Task Name: {Fore.BLUE + task_name + Fore.RESET}")
            if "subSections" in task_group:
                sub_sections = task_group["subSections"]
                for sub_section in sub_sections:
                    sub_section_tasks = sub_section.get("tasks", [])
                    for sub_task in sub_section_tasks:
                        task_id = sub_task.get("id", "N/A")
                        task_name = sub_task.get("title", "N/A")
                        print(f"Task ID: {Fore.YELLOW + task_id + Fore.RESET}, Task Name: {Fore.BLUE + task_name + Fore.RESET}")
    else:
        print(f"{Fore.RED + Style.BRIGHT}Failed to fetch tasks.")

# Main function with modified logic
def main():
    signal.signal(signal.SIGINT, signal_handler)  # Handle CTRL + C
    clear_terminal()
    art()

    # Specific task IDs
    task_ids = [
        "38f6dd88-57bd-4b42-8712-286a06dac0a0",
        "6af85c01-f68d-4311-b78a-9cf33ba5b151",
        "d95d3299-e035-4bf6-a7ca-0f71578e9197",
        "53044aaf-a51f-4dfc-851a-ae2699a5f729",
        "835d4d8a-f9af-4ff5-835e-a15d48e465e6",
        "3c048e58-6bb5-4cba-96cb-e564c046de58"
    ]

    game_points_min, game_points_max = 183, 256

    while True:
        total_balance = 0.0  # Initialize total balance as float
        print("\n" + Fore.MAGENTA + "="*50)
        print(f"{Fore.YELLOW + Style.BRIGHT}Choose an option:{Style.RESET_ALL}")
        print(Fore.MAGENTA + "="*50)
        print(f"{Fore.CYAN + Style.BRIGHT}1. All Tasks{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}2. Auto Farming{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}3. Auto Game Play{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}4. Weekly Social Task{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}5. Game Point Adjustment{Style.RESET_ALL}")
        print(f"{Fore.CYAN + Style.BRIGHT}6. New Task (with validation, start, and claim){Style.RESET_ALL}")
        print(Fore.MAGENTA + "="*50 + Style.RESET_ALL)
        user_choice = input("Enter your choice (1, 2, 3, 4, 5, 6'): ").strip()

        if user_choice == 'showtasks':
            query_ids = get_query_ids_from_file('data.txt')
            if query_ids:
                query_id = query_ids[0]  # Only show tasks for the first account
                countdown_timer(random.randint(3, 5))
                token = get_new_token(query_id)
                if not token:
                    print(f"{Fore.RED + Style.BRIGHT}Token generation failed.")
                else:
                    save_token(token, 'token.txt')
                    print(f"\n--- Displaying Tasks for Account 1 ---")
                    display_all_tasks_for_single_account(token)
                    clear_token_file('token.txt')
            else:
                print(f"{Fore.RED + Style.BRIGHT}No accounts found in data.txt.")
            continue

        if user_choice not in ['1', '2', '3', '4', '5', '6']:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, or 'showtasks'.")
            continue

        query_ids = get_query_ids_from_file('data.txt')

        # Prompt for auto-task options once
        if user_choice == '1':
            auto_task_choice = input("Auto Task (y/n): ").strip().lower()
            auto_game_choice = input("Auto Game Play (y/n): ").strip().lower()
            auto_new_task_choice = input("Auto New Task (y/n): ").strip().lower()

        for index, query_id in enumerate(query_ids):
            if not query_id:
                print(f"{Fore.RED + Style.BRIGHT}Account No.{index + 1}: Query ID not found.")
                continue

            # Parse username from query ID
            username = parse_username_from_query(query_id)

            countdown_timer(random.randint(3, 5))
            token = get_new_token(query_id)
            if not token:
                print(f"{Fore.RED + Style.BRIGHT}Account No.{index + 1}: Token generation failed.")
                continue

            save_token(token, 'token.txt')
            print(f"\n--- Account No. {index + 1} ---")
            print(f"Username: {username}")

            prev_balance, _ = new_balance(token)
            print(f"{Fore.GREEN + Style.BRIGHT}Previous Balance: {prev_balance}")

            try:
                if user_choice == '1':
                    # Automatically perform daily check-in, farming claim, and start
                    if check_daily_reward_time():
                        if get_daily_reward(token):
                            countdown_timer(random.randint(2, 3))
                    else:
                        print(f"{Fore.YELLOW + Style.BRIGHT}Daily Check-In will work after 11:30 AM{Style.RESET_ALL}")

                    if claim_farming(token):
                        countdown_timer(random.randint(3, 4))
                    start_farming(token)

                    if auto_task_choice == 'y':
                        solve_task(token)

                    if auto_game_choice == 'y':
                        total_reward = 0
                        while True:
                            current_balance, play_passes = new_balance(token)
                            if current_balance is None or play_passes is None:
                                print(f"{Fore.RED + Style.BRIGHT}Failed to retrieve balance or play passes.")
                                break

                            if play_passes > 0:
                                print(f"{Fore.CYAN + Style.BRIGHT}Play Passes Available: {play_passes}")
                                game_id = play_game(token)
                                if game_id:
                                    points = random.randint(game_points_min, game_points_max)
                                    reward = claim_game(token, game_id, points)
                                    total_reward += reward
                                    countdown_timer(random.randint(3, 10))
                                _, play_passes = new_balance(token)
                            else:
                                print(f"{Fore.RED + Style.BRIGHT}Play Pass is 0")
                                break

                        print(f"{Fore.GREEN + Style.BRIGHT}Total Reward Claimed: {total_reward} points [✓]")

                    if auto_new_task_choice == 'y':
                        keyword_file = 'Keyword.txt'  # Assuming the keyword file path
                        process_specific_tasks(token, keyword_file, task_ids)

                if user_choice == '2':
                    if check_daily_reward_time():
                        if get_daily_reward(token):
                            countdown_timer(random.randint(2, 3))
                    else:
                        print(f"{Fore.YELLOW + Style.BRIGHT}Daily Check-In will work after 11:30 AM{Style.RESET_ALL}")

                    if claim_farming(token):
                        countdown_timer(random.randint(3, 4))
                    start_farming(token)

                if user_choice == '3':
                    total_reward = 0
                    while True:
                        current_balance, play_passes = new_balance(token)
                        if current_balance is None or play_passes is None:
                            print(f"{Fore.RED + Style.BRIGHT}Failed to retrieve balance or play passes.")
                            break

                        if play_passes > 0:
                            print(f"{Fore.CYAN + Style.BRIGHT}Play Passes Available: {play_passes}")
                            game_id = play_game(token)
                            if game_id:
                                points = random.randint(game_points_min, game_points_max)
                                reward = claim_game(token, game_id, points)
                                total_reward += reward
                                countdown_timer(random.randint(3, 10))
                            _, play_passes = new_balance(token)
                        else:
                            print(f"{Fore.RED + Style.BRIGHT}Play Pass is 0")
                            break

                    print(f"{Fore.GREEN + Style.BRIGHT}Total Reward Claimed: {total_reward} points [✓]")

                if user_choice == '4':
                    print(f"{Fore.BLUE + Style.BRIGHT}Performing Task⌛")
                    solve_specific_tasks(token, task_ids)

                if user_choice == '6':
                    keyword_file = 'Keyword.txt'  # Assuming the keyword file path
                    process_specific_tasks(token, keyword_file, task_ids)

            finally:
                updated_balance, _ = new_balance(token)
                if updated_balance is not None:
                    print(f"{Fore.GREEN + Style.BRIGHT}Final Updated Balance: {updated_balance} [✓]")
                    total_balance += float(updated_balance)

        clear_token_file('token.txt')
        print(f"{Fore.YELLOW + Style.BRIGHT}Total Balance of All Accounts: {total_balance} [✓]")

if __name__ == "__main__":
    main()