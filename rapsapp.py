import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import PlayerDashboardByLastNGames
from rapsdb import *
import sqlite3

# Create the main window first
root = tk.Tk()
root.title("Raptors Roster App")

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set the window size to a fraction of the screen size, for example, 80% of the screen size
window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)

# Set the window size
root.geometry(f"{window_width}x{window_height}")

# Initialize the database
create_database()
create_schedule_table()  # Ensure the schedule table is created
ensure_time_column_exists()  # Ensure the time column exists

# Load schedule from a text file
def load_schedule_from_file(filename):
    try:
        # Connect to the database
        conn = sqlite3.connect('raptors.db')
        cursor = conn.cursor()

        # Read the file and process each line
        with open(filename, 'r') as file:
            new_games_added = 0
            duplicate_games = 0

            for line in file:
                # Split the line into components
                game_date, opponent, location, time = line.strip().split(', ')

                # Check if this exact game already exists in the database
                cursor.execute('''
                    SELECT COUNT(*) FROM schedule 
                    WHERE game_date = ? AND opponent = ? AND location = ? AND time = ?
                ''', (game_date, opponent, location, time))
                
                # If the game doesn't exist, add it
                if cursor.fetchone()[0] == 0:
                    add_game(game_date, opponent, location, time)
                    new_games_added += 1
                else:
                    duplicate_games += 1

        # Commit changes and close connection
        conn.commit()
        conn.close()

        # Show a summary message
        message = f"Schedule upload complete.\n"
        message += f"New games added: {new_games_added}\n"
        message += f"Duplicate games skipped: {duplicate_games}"
        
        messagebox.showinfo("Schedule Upload", message)
        
        # Refresh the schedule view
        show_schedule()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load schedule: {e}")

# Function to get full Raptors schedule
def get_full_raptors_schedule():
    raptors_id = [team for team in teams.get_teams() if team['full_name'] == 'Toronto Raptors'][0]['id']
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=raptors_id, season_nullable="2024-25")
    games = gamefinder.get_data_frames()[0]
    
    schedule = {}
    for _, game in games.iterrows():
        date = datetime.strptime(game['GAME_DATE'], '%Y-%m-%d').strftime('%b %d, %Y')
        opponent = game['MATCHUP'].split()[-1]
        home_away = 'vs' if game['MATCHUP'].startswith('TOR') else '@'
        schedule.setdefault(date, []).append(f"{home_away} {opponent}")
    
    return schedule


from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerDashboardByLastNGames

def get_player_season_stats(player_name, season):
    try:
        # Find the NBA player ID based on the name
        nba_player = [p for p in players.get_players() if p['full_name'].lower() == player_name.lower()]
        
        if not nba_player:
            print(f"No NBA player found for name: {player_name}")
            return None

        nba_player_id = nba_player[0]['id']

        # Get stats for the specified season
        player_stats = PlayerDashboardByLastNGames(
            player_id=nba_player_id, 
            season=season,
            last_n_games=82  # Full season
        )
        
        # Extract the overall season averages
        season_stats = player_stats.get_data_frames()[0]
        
        # Calculate per-game averages
        games_played = season_stats['GP'].iloc[0]
        
        return {
            'PPG': round(season_stats['PTS'].iloc[0] / games_played, 1) if games_played > 0 else 0,
            'RPG': round(season_stats['REB'].iloc[0] / games_played, 1) if games_played > 0 else 0,
            'APG': round(season_stats['AST'].iloc[0] / games_played, 1) if games_played > 0 else 0,
            'FG_PCT': f"{round(season_stats['FG_PCT'].iloc[0] * 100, 1)}%",
            '3PT_PCT': f"{round(season_stats['FG3_PCT'].iloc[0] * 100, 1)}%",
            'GP': games_played
        }
    except Exception as e:
        print(f"Error retrieving stats for {player_name}: {e}")
        return None

def view_player_profile(player_id):
    # Clear existing content
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    # Fetch the full player details
    player = get_player_by_id(player_id)
    
    # Create a frame for the profile details
    profile_frame = tk.Frame(main_frame)
    profile_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    
    # Profile Title
    title_label = tk.Label(profile_frame, text=player[1], font=('Arial', 18, 'bold'))
    title_label.pack(pady=(0, 20))
    
    # Create labels for basic player information
    details = [
        ("Position", player[2]),
        ("Age", player[3]),
        ("Height", player[4]),
        ("Weight", player[5]),
        ("Salary", f"${float(player[6]):,.2f}")
    ]
    
    for label, value in details:
        detail_frame = tk.Frame(profile_frame)
        detail_frame.pack(fill=tk.X, pady=5)
        
        label_widget = tk.Label(detail_frame, text=f"{label}:", font=('Arial', 14, 'bold'), anchor='w')
        label_widget.pack(side=tk.LEFT)
        
        value_widget = tk.Label(detail_frame, text=value, font=('Arial', 14), anchor='w')
        value_widget.pack(side=tk.LEFT)
    
    # Retrieve and display current season stats
    current_nba_stats = get_player_season_stats(player[1], '2024-25')
    last_nba_stats = get_player_season_stats(player[1], '2023-24')
    
    # Display current season stats
    if current_nba_stats:
        # Stats Title
        stats_title_label = tk.Label(profile_frame, text="2024-2025 Season Stats", font=('Arial', 16, 'bold'))
        stats_title_label.pack(pady=(20, 10))
        
        # Create a frame for the current season stats table
        stats_table_frame = tk.Frame(profile_frame)
        stats_table_frame.pack(fill=tk.X, pady=10)

        # Create table headers for current season
        headers = ["Points Per Game", "Rebounds Per Game", "Assists Per Game", "Field Goal %", "3-Point %"]
        for col, header in enumerate(headers):
            header_label = tk.Label(stats_table_frame, text=header, font=('Arial', 14, 'bold'))
            header_label.grid(row=0, column=col, padx=10, pady=5)

        # Populate current season stats
        values = [
            current_nba_stats['PPG'],
            current_nba_stats['RPG'],
            current_nba_stats['APG'],
            current_nba_stats['FG_PCT'],
            current_nba_stats['3PT_PCT']
        ]
        
        for col, value in enumerate(values):
            value_label = tk.Label(stats_table_frame, text=value, font=('Arial', 12))
            value_label.grid(row=1, column=col, padx=10, pady=5)

    # Display last season stats
    if last_nba_stats:
        # Stats Title
        last_stats_title_label = tk.Label(profile_frame, text="2023-2024 Season Stats", font=('Arial', 16, 'bold'))
        last_stats_title_label.pack(pady=(20, 10))
        
        # Create a frame for the last season stats table
        last_stats_table_frame = tk.Frame(profile_frame)
        last_stats_table_frame.pack(fill=tk.X, pady=10)

        # Create table headers for last season
        for col, header in enumerate(headers):
            header_label = tk.Label(last_stats_table_frame, text=header, font=('Arial', 14, 'bold'))
            header_label.grid(row=0, column=col, padx=10, pady=5)

        # Populate last season stats
        last_values = [
            last_nba_stats['PPG'],
            last_nba_stats['RPG'],
            last_nba_stats['APG'],
            last_nba_stats['FG_PCT'],
            last_nba_stats['3PT_PCT']
        ]
        
        for col, value in enumerate(last_values):
            last_value_label = tk.Label(last_stats_table_frame, text=value, font=('Arial', 12))
            last_value_label.grid(row=1, column=col, padx=10, pady=5)

    # Add a button to go back to the player list
    back_button = tk.Button(profile_frame, text="Back to Player List", command=lambda: display_roster())
    back_button.pack(pady=(20, 0))
    
def display_roster():
    # Clear existing content
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Create a frame for the roster
    roster_frame = tk.Frame(main_frame)
    roster_frame.pack(fill=tk.BOTH, expand=True)

    # Create headers
    headers = ["Name", "Position", "Age", "Height", "Weight", "Salary", "Actions"]
    for col, header in enumerate(headers):
        header_label = tk.Label(roster_frame, text=header, font=('bold', 12))
        header_label.grid(row=0, column=col, padx=5, pady=5, sticky='w')

    players = get_all_players()
    
    for row, player in enumerate(players, start=1):
        # Convert salary to float, handling potential errors
        try:
            salary = float(player[6])
        except (ValueError, TypeError):
            salary = 0.0

        # Display player information
        player_info = [
            player[1],  # Name
            player[2],  # Position
            player[3],  # Age
            player[4],  # Height
            player[5],  # Weight
            f"${salary:,.2f}"  # Formatted salary
        ]
        
        for col, info in enumerate(player_info):
            if col == 0:  # Name column
                # Make the name clickable and blue
                name_label = tk.Label(roster_frame, text=info, fg='blue', cursor='hand2')
                name_label.grid(row=row, column=col, padx=5, pady=5, sticky='w')
                # Bind click event to open player profile
                name_label.bind('<Button-1>', lambda e, pid=player[0]: view_player_profile(pid))
            else:
                player_label = tk.Label(roster_frame, text=info)
                player_label.grid(row=row, column=col, padx=5, pady=5, sticky='w')
        
        edit_button = tk.Button(roster_frame, text="Edit", command=lambda id=player[0]: edit_player(id))
        edit_button.grid(row=row, column=len(player_info), padx=5, pady=5)

        delete_button = tk.Button(roster_frame, text="Delete", command=lambda id=player[0]: delete_player(id))
        delete_button.grid(row=row, column=len(player_info)+1, padx=5, pady=5)

    # Add 'Back to Home' button
    back_button = tk.Button(main_frame, text="Back to Home Page", command=show_home)
    back_button.pack(pady=10)

    # Add 'Add Player' button
    add_player_button = tk.Button(main_frame, text="Add Player", command=add_player_window)
    add_player_button.pack(pady=10)

# Function to delete a player
def delete_player(player_id):
    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this player?")
    if confirm:
        delete_player_from_db(player_id)
        display_roster()

# Function to edit a player
def edit_player(player_id):
    # Fetch the current player data
    player = get_player_by_id(player_id)
    
    # Create a new window for editing
    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Player")
    
    # Create entry fields for each piece of information
    name_entry = tk.Entry(edit_window)
    name_entry.insert(0, player[1])
    name_entry.pack(pady=5)
    
    position_entry = tk.Entry(edit_window)
    position_entry.insert(0, player[2])
    position_entry.pack(pady=5)
    
    age_entry = tk.Entry(edit_window)
    age_entry.insert(0, player[3])
    age_entry.pack(pady=5)

    height_entry = tk.Entry(edit_window)
    height_entry.insert(0, player[4])
    height_entry.pack(pady=5)

    weight_entry = tk.Entry(edit_window)
    weight_entry.insert(0, player[5])
    weight_entry.pack(pady=5)

    salary_entry = tk.Entry(edit_window)
    salary_entry.insert(0, player[6])
    salary_entry.pack(pady=5)
    
    def save_changes():
        # Get the updated information from the entry fields
        updated_name = name_entry.get()
        updated_position = position_entry.get()
        updated_age = age_entry.get()
        updated_height = height_entry.get()
        updated_weight = weight_entry.get()
        updated_salary = salary_entry.get()
        
        # Update the database
        update_player(player_id, updated_name, updated_position, updated_age, updated_height, updated_weight, updated_salary)
        
        # Close the edit window and refresh the roster display
        edit_window.destroy()
        display_roster()
    
    save_button = tk.Button(edit_window, text="Save Changes", command=save_changes)
    save_button.pack(pady=5)

# Function to add a new player
def add_player_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add New Player")

    tk.Label(add_window, text="Name:").pack()
    name_entry = tk.Entry(add_window)
    name_entry.pack()

    tk.Label(add_window, text="Position:"). pack()
    position_entry = tk.Entry(add_window)
    position_entry.pack()

    tk.Label(add_window, text="Age:").pack()
    age_entry = tk.Entry(add_window)
    age_entry.pack()

    tk.Label(add_window, text="Height:").pack()
    height_entry = tk.Entry(add_window)
    height_entry.pack()

    tk.Label(add_window, text="Weight:").pack()
    weight_entry = tk.Entry(add_window)
    weight_entry.pack()

    tk.Label(add_window, text="Salary:").pack()
    salary_entry = tk.Entry(add_window)
    salary_entry.pack()

def add_player_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add New Player")

    tk.Label(add_window, text="Name:").pack()
    name_entry = tk.Entry(add_window)
    name_entry.pack()

    tk.Label(add_window, text="Position:"). pack()
    position_entry = tk.Entry(add_window)
    position_entry.pack()

    tk.Label(add_window, text="Age:").pack()
    age_entry = tk.Entry(add_window)
    age_entry.pack()

    tk.Label(add_window, text="Height:").pack()
    height_entry = tk.Entry(add_window)
    height_entry.pack()

    tk.Label(add_window, text="Weight:").pack()
    weight_entry = tk.Entry(add_window)
    weight_entry.pack()

    tk.Label(add_window, text="Salary:").pack()
    salary_entry = tk.Entry(add_window)
    salary_entry.pack()

    def save_new_player():
        name = name_entry.get()
        position = position_entry.get()
        age = age_entry.get()
        height = height_entry.get()
        weight = weight_entry.get()
        salary = salary_entry.get()

        add_player(name, position, age, height, weight, salary)
        add_window.destroy()
        display_roster()

    add_button = tk.Button(add_window, text="Add Player", command=save_new_player)
    add_button.pack(pady=5)
    
def show_schedule():
    # Clear existing content
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Create a notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # Define months and their details
    months = [
        ('October 2024', range(1, 32)),
        ('November 2024', range(1, 31)),
        ('December 2024', range(1, 32)),
        ('January 2025', range(1, 32)),
        ('February 2025', range(1, 29)),
        ('March 2025', range(1, 32)),
        ('April 2025', range(1, 31)),
        ('May 2025', range(1, 32)),
        ('June 2025', range(1, 31))
    ]

    # Calendar headers
    weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    # Retrieve games from the database
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schedule ORDER BY game_date')
    games = cursor.fetchall()
    conn.close()

    # Organize games by date
    schedule_dict = {}
    for game in games:
        try:
            # Try multiple date formats
            try:
                # First try the standard format
                game_date = datetime.strptime(game[1], '%Y-%m-%d')
            except ValueError:
                try:
                    # Try alternative formats
                    game_date = datetime.strptime(game[1], '%m-%d-%Y')
                except ValueError:
                    # If all parsing fails, skip this game
                    print(f"Could not parse date: {game[1]}")
                    continue

            # Ensure we're using the correct year for 2024 games
            if game_date.year < 2024:
                game_date = game_date.replace(year=2024)

            formatted_date = game_date.strftime('%b %d, %Y')
            
            opponent = game[2]
            location = game[3]
            time = game[4] if len(game) > 4 else "Time Not Specified"

            # Debug print
            print(f"Processed game: {formatted_date}, {opponent}, {location}, {time}")

            schedule_dict.setdefault(formatted_date, []).append(f"{opponent} ({location}, {time})")
        except Exception as e:
            print(f"Error processing game: {game}, Error: {e}")

    # Function to upload a schedule file
    def upload_schedule_file():
        filename = filedialog.askopenfilename(title="Select Schedule File", filetypes=[("Text Files", "*.txt")])
        if filename:
            load_schedule_from_file(filename)
            messagebox.showinfo("Success", "Schedule loaded successfully!")
            # Refresh the calendar to reflect the new schedule
            show_schedule()

    for month_name, days in months:
        # Create frame for each month
        month_frame = ttk.Frame(notebook)
        notebook.add(month_frame, text=month_name)

        # Add weekday headers
        for i, day in enumerate(weekdays):
            label = tk.Label(month_frame, text=day, font=('Arial', 10, 'bold'))
            label.grid(row=0, column=i, padx=5, pady=5)

        # Calculate first day of month
        first_day = datetime.strptime(f'1 {month_name}', '%d %B %Y').weekday()
        first_day = (first_day + 1) % 7  # Adjust to start with Sunday

        # Add calendar days
        row = 1
        col = first_day

        for day in days:
            # Create the date string for this specific day
            current_date = datetime.strptime(f'{month_name.split()[0]} {day} {month_name.split()[1]}', '%B %d %Y')
            formatted_date = current_date.strftime('%b %d, %Y')
            
            date_frame = tk.Frame(month_frame, width=100, height=80, relief='solid', borderwidth=1)
            date_frame.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            date_frame.grid_propagate(False)

            # Date number
            date_label = tk.Label(date_frame, text=str(day), anchor='nw')
            date_label.grid(row=0, column=0, padx=5, pady=2, sticky='nw')

            # If there are games on this date, display them
            if formatted_date in schedule_dict:
                games_info = "\n".join(schedule_dict[formatted_date])
                games_label = tk.Label(date_frame, text=games_info, anchor='nw', justify='left', font=('Arial', 8))
                games_label.grid(row=1, column=0, padx=5, pady=2, sticky='nw')

            col += 1
            if col > 6:
                col = 0
                row += 1

        # Configure grid weights
        for i in range(7):
            month_frame.grid_columnconfigure(i, weight=1)

    # Add 'Upload Schedule File' button
    upload_button = tk.Button(main_frame, text="Upload Schedule File", command=upload_schedule_file)
    upload_button.pack(pady=10)

    # Add 'Clear Schedule' button
    clear_schedule_button = tk.Button(main_frame, text="Clear All Schedules", 
                                      command=clear_schedule_confirmation)
    clear_schedule_button.pack(pady=10)

    # Add 'Back to Home' button
    back_button = tk.Button(main_frame, text="Back to Home Page", command=show_home)
    back_button.pack(pady=10)

# Add this new function
def clear_schedule_confirmation():
    # Show a confirmation dialog
    confirm = messagebox.askyesno("Confirm Clear", 
                                  "Are you sure you want to clear ALL schedules? This cannot be undone.")
    if confirm:
        # Call the function to delete all games
        delete_all_games()
        
        # Refresh the schedule view
        show_schedule()
        
        # Show a confirmation message
        messagebox.showinfo("Schedule Cleared", "All schedules have been removed.")
        
# Function to show the home page
def show_home():
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    home_label = tk.Label(main_frame, text="Welcome to the Raptors Roster App", font=('Arial', 16))
    home_label.pack(pady=20)

    schedule_button = tk.Button(main_frame, text="View Schedule", command=show_schedule)
    schedule_button.pack(pady=10)

    roster_button = tk.Button(main_frame, text="View Roster", command=display_roster)
    roster_button.pack(pady=10)

# Main frame for content
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Show the home page initially
show_home()

# Start the application
root.mainloop()