#!/usr/bin/env python3
"""
Simple CLI todo application.

Usage:
    python todo.py add <task>    - Add a new task
    python todo.py list          - List all tasks
    python todo.py done <id>     - Mark task as done
    python todo.py rm <id>       - Remove a task
"""

import argparse
import json
import os
from pathlib import Path

TODO_FILE = Path(__file__).parent / "todos.json"


def load_todos():
    """Load todos from JSON file."""
    if not TODO_FILE.exists():
        return []
    with open(TODO_FILE, "r") as f:
        return json.load(f)


def save_todos(todos):
    """Save todos to JSON file."""
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)


def add_task(task_text):
    """Add a new task to the todo list."""
    todos = load_todos()
    task_id = max([t["id"] for t in todos], default=0) + 1
    todos.append({
        "id": task_id,
        "text": task_text,
        "done": False
    })
    save_todos(todos)
    print(f"Added task: {task_text}")


def list_tasks():
    """List all tasks in the todo list."""
    todos = load_todos()
    if not todos:
        print("No tasks found.")
        return
    for task in todos:
        status = "[x]" if task["done"] else "[ ]"
        print(f"{task['id']}. {status} {task['text']}")


def done_task(task_id):
    """Mark a task as done."""
    todos = load_todos()
    for task in todos:
        if task["id"] == task_id:
            task["done"] = True
            save_todos(todos)
            print(f"Task {task_id} marked as done.")
            return
    print(f"Task {task_id} not found.")


def rm_task(task_id):
    """Remove a task from the todo list."""
    todos = load_todos()
    original_len = len(todos)
    todos = [t for t in todos if t["id"] != task_id]
    if len(todos) < original_len:
        save_todos(todos)
        print(f"Task {task_id} removed.")
    else:
        print(f"Task {task_id} not found.")


def main():
    """Main CLI entry point using argparse."""
    parser = argparse.ArgumentParser(
        description="Simple CLI todo application",
        prog="todo.py"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("task", type=str, help="The task to add")
    
    # list command
    subparsers.add_parser("list", help="List all tasks")
    
    # done command
    done_parser = subparsers.add_parser("done", help="Mark a task as done")
    done_parser.add_argument("id", type=int, help="Task ID to mark as done")
    
    # rm command
    rm_parser = subparsers.add_parser("rm", help="Remove a task")
    rm_parser.add_argument("id", type=int, help="Task ID to remove")
    
    args = parser.parse_args()
    
    if args.command == "add":
        add_task(args.task)
    elif args.command == "list":
        list_tasks()
    elif args.command == "done":
        done_task(args.id)
    elif args.command == "rm":
        rm_task(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
