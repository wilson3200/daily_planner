import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import datetime
import os


class DailyPlanner:
    """The main class to manage and interact with the daily planner."""

    def __init__(self, root):
        self.root = root
        self.root.title("Daily Planner")

        # Make the window fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.bind("<F11>", self.toggle_fullscreen)  # Toggle fullscreen mode with F11
        self.root.bind("<Escape>", self.quit_fullscreen)  # Exit fullscreen mode with Escape

        # Save when closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Define task tiers and their weights
        self.weights = {'Tier 1': 4, 'Tier 2': 2, 'Tier 3': 1, 'Tier 4': 0.5}
        self.tier_map = {1: 'Tier 1', 2: 'Tier 2', 3: 'Tier 3', 4: 'Tier 4'}
        self.tasks = []

        # Store default tasks
        self.default_tasks = []

        # Create UI components
        self.create_widgets()

        # Load state from file (but not default tasks)
        self.load_state()

    def create_widgets(self):
        """Create the UI widgets."""
        # Title label with larger font size and centered
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.label = tk.Label(self.root, text=f"Tasks for Today ({today_date})", font=("Helvetica", 24, "bold"))
        self.label.pack(pady=20, anchor='n')

        # Frame for tasks
        self.tasks_frame = tk.Frame(self.root)
        self.tasks_frame.pack()

        # Buttons for adding and removing tasks
        self.add_button = tk.Button(self.root, text="Add Task", command=self.open_add_task_dialog)
        self.add_button.pack(pady=5)

        self.remove_button = tk.Button(self.root, text="Remove Task", command=self.open_remove_task_dialog)
        self.remove_button.pack(pady=5)

        # Reset Tasks button
        self.reset_button = tk.Button(self.root, text="Reset Tasks", command=self.reset_all_tasks)
        self.reset_button.pack(pady=10)

        # Score label
        self.score_label = tk.Label(self.root, text="Score: 0.00%", font=("Helvetica", 18))
        self.score_label.pack(pady=10)

        # Submit Score button
        self.submit_button = tk.Button(self.root, text="Submit Score", command=self.save_score)
        self.submit_button.pack(pady=10)

    def load_tasks_from_file(self, filename):
        """Loads tasks from external file."""
        try:
            with open(filename, "r") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        task_name, tier_num = line.split(',', 1)
                        task_name = task_name.strip()
                        tier_num = int(tier_num.strip())
                        tier = self.tier_map.get(tier_num, "Unknown Tier")
                        if tier in self.weights:
                            self.default_tasks.append((task_name, tier))
                            self.add_task_to_ui(task_name, tier)
        except FileNotFoundError:
            messagebox.showwarning("File Not Found", f"{filename} not found. Starting with an empty task list.")
        except ValueError:
            messagebox.showwarning("File Error", f"Error reading {filename}. Check the format.")

    def add_task_to_ui(self, task_name, tier):
        """Integrate tasks from list into UI components."""
        var = tk.BooleanVar()
        chk = tk.Checkbutton(self.tasks_frame, text=f"{task_name} ({tier})", variable=var, command=self.update_score)
        chk.pack(anchor='w', padx=20)
        self.tasks.append((chk, var, tier))
        self.sort_tasks_by_tier()  # Ensure tasks are sorted
        self.update_score()

    def open_add_task_dialog(self):
        """Opens dialog box for adding tasks."""
        # Create a new top-level window for the task dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Task")

        # Task name entry
        tk.Label(dialog, text="Task Name:").pack(pady=5)
        task_name_entry = tk.Entry(dialog)
        task_name_entry.pack(pady=5)

        # Tier selection
        tk.Label(dialog, text="Select Tier:").pack(pady=5)
        tier_combobox = ttk.Combobox(dialog, values=list(self.weights.keys()))
        tier_combobox.pack(pady=5)
        tier_combobox.set("Select Tier")

        # Add button in dialog
        tk.Button(dialog, text="Add Task",
                  command=lambda: self.add_task(task_name_entry.get(), tier_combobox.get(), dialog)).pack(pady=10)

    def add_task(self, task_name, tier, dialog):
        """Adds a task to the current list of tasks."""
        if not task_name:
            messagebox.showwarning("Invalid Input", "Please enter a task name.")
            return

        if tier not in self.weights:
            messagebox.showwarning("Invalid Tier", "Please select a valid tier from the dropdown.")
            return

        self.add_task_to_ui(task_name, tier)
        dialog.destroy()  # Close the dialog after adding the task
        self.update_remove_task_dialog()  # Update the remove task dialog if open

    def open_remove_task_dialog(self):
        """Opens the dialog box for removing tasks."""
        # Create a new top-level window for the remove task dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Remove Task")

        # Dropdown for tasks to remove
        tk.Label(dialog, text="Select Task to Remove:").pack(pady=5)
        self.task_combobox = ttk.Combobox(dialog, values=self.get_task_names())
        self.task_combobox.pack(pady=5)
        self.task_combobox.set("Select Task")

        # Remove button in dialog
        tk.Button(dialog, text="Remove Task", command=lambda: self.remove_task(self.task_combobox.get(), dialog)).pack(
            pady=10)

    def get_task_names(self):
        """Gets the names of current tasks."""
        # Return the list of task names for the dropdown
        return [chk[0].cget("text") for chk in self.tasks]

    def update_remove_task_dialog(self):
        """Updates the dropdown for removing tasks."""
        # Update the remove task dropdown list with current tasks
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "Remove Task":
                task_names = self.get_task_names()
                combobox = widget.children['!combobox']
                combobox['values'] = task_names
                if task_names:
                    combobox.set(task_names[0])
                else:
                    combobox.set("Select Task")

    def remove_task(self, task_name, dialog):
        """Removes task from the current list of tasks."""
        if not task_name:
            messagebox.showwarning("No Task Selected", "Please select a task to remove.")
            return

        for chk in self.tasks:
            if chk[0].cget("text") == task_name:
                chk[0].pack_forget()  # Remove checkbox from the frame
                self.tasks.remove(chk)  # Remove task from list
                self.update_score()  # Update the score
                break

        dialog.destroy()  # Close the dialog after removing the task
        self.update_remove_task_dialog()  # Update the remove task dialog if open

    def update_score(self):
        """Updates the daily score based on checked and un-checked boxes."""
        total_weight = sum(self.weights[tier] for _, _, tier in self.tasks)
        weighted_completed = sum(self.weights[tier] for _, var, tier in self.tasks if var.get())
        percentage = (weighted_completed / total_weight) * 100 if total_weight > 0 else 0

        # Debug prints to check calculations
        print(f"Total Weight: {total_weight}")
        print(f"Weighted Completed: {weighted_completed}")
        print(f"Percentage: {percentage:.2f}")

        # Update score label
        self.score_label.config(text=f"Score: {percentage:.2f}%")

    def save_score(self):
        """Saves the score in an external file."""
        # Calculate and update score
        self.update_score()

        # Calculate the score
        total_weight = sum(self.weights[tier] for _, _, tier in self.tasks)
        weighted_completed = sum(self.weights[tier] for _, var, tier in self.tasks if var.get())
        percentage = (weighted_completed / total_weight) * 100 if total_weight > 0 else 0

        # Save the score to the file
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        with open("daily_scores.txt", "a") as file:
            file.write(f"{today_date}: {percentage:.2f}%\n")

        # Save the state
        self.save_state()

        # Reset tasks for the next day
        self.reset_tasks()

        # Ensure the score display is updated
        self.update_score()

    def reset_all_tasks(self):
        """Resets the tasks to the default values, with default tasks loaded."""
        # Clear the checkboxes and delete all tasks
        for chk, _, _ in self.tasks:
            chk.pack_forget()
        self.tasks = []

        # Wipe the save file
        if os.path.exists("save.txt"):
            os.remove("save.txt")

        # Load the default tasks
        self.load_tasks_from_file("default_schedule.txt")
        self.update_score()

    def save_state(self):
        """Saves the relevant information necessary for reloading the current state."""
        print("Saving state...")  # Debug statement
        with open("save.txt", "w") as file:
            # Save tasks and their states
            for chk, var, tier in self.tasks:
                task_name = chk.cget("text").split(' (')[0]  # Extract task name
                completed = var.get()
                file.write(f"{task_name},{tier},{completed}\n")

            # Save current score
            score = self.score_label.cget("text")
            file.write(f"{score}\n")

    def load_state(self):
        """Loads the information saved within the save file."""
        try:
            with open("save.txt", "r") as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        if line.startswith("Score:"):
                            score_text = line.split(":", 1)[1].strip()  # Extract the score value after "Score:"
                            self.score_label.config(text=f"Score: {score_text}")  # Set the score label with "Score:"
                        else:
                            task_name, tier, completed = line.split(',', 2)
                            tier = tier.strip()
                            completed = completed.strip() == 'True'
                            if tier in self.weights:
                                self.add_task_to_ui(task_name, tier)
                                var = self.tasks[-1][1]  # Get the BooleanVar of the newly added task
                                var.set(completed)
        except FileNotFoundError:
            print("No save file found, starting fresh.")
        except Exception as e:
            messagebox.showwarning("Load Error", f"Error loading save file: {e}")

    def sort_tasks_by_tier(self):
        """Sorts the tasks by their tier and updates the UI."""
        # Sort tasks based on tier weights
        self.tasks.sort(key=lambda x: -self.weights[x[2]])

        # Remove and re-add tasks in sorted order
        for chk, _, _ in self.tasks:
            chk.pack_forget()
        self.tasks_frame.update()  # Ensure the frame updates before re-adding

        for chk, var, tier in self.tasks:
            chk.pack(anchor='w', padx=20)

    def toggle_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    def quit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)

    def on_closing(self):
        self.save_state()  # Save state before closing
        self.root.destroy()  # Close the application


if __name__ == "__main__":
    root = tk.Tk()
    app = DailyPlanner(root)
    root.mainloop()
