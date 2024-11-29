import sqlite3

# Function to create the database and the roster table
def create_database():
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            age INTEGER NOT NULL,
            height TEXT NOT NULL,
            weight TEXT NOT NULL,
            salary REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a player to the roster
def add_player(name, position, age, height, weight, salary):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    # Convert salary to float, handle potential input errors
    try:
        salary = float(salary)
    except ValueError:
        salary = 0.0
    
    cursor.execute('''
        INSERT INTO roster (name, position, age, height, weight, salary)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, position, age, height, weight, salary))
    
    conn.commit()
    conn.close()

# Function to delete a player from the roster
def delete_player_from_db(player_id):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM roster WHERE id = ?
    ''', (player_id,))
    
    conn.commit()
    conn.close()

# Function to retrieve all players from the roster
def get_all_players():
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM roster')
    players = cursor.fetchall()
    
    conn.close()
    return players

# Function to update a player's information
def update_player(player_id, name, position, age, height, weight, salary):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    # Convert salary to float, handle potential input errors
    try:
        salary = float(salary)
    except ValueError:
        salary = 0.0
    
    cursor.execute('''
        UPDATE roster 
        SET name=?, position=?, age=?, height=?, weight=?, salary=?
        WHERE id=?
    ''', (name, position, age, height, weight, salary, player_id))
    
    conn.commit()
    conn.close()

# Function to retrieve a player by ID
def get_player_by_id(player_id):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM roster WHERE id = ?', (player_id,))
    player = cursor.fetchone()
    
    conn.close()
    return player

# Schedule-related functions
def create_schedule_table():
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT NOT NULL,
            opponent TEXT NOT NULL,
            location TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    
def ensure_time_column_exists():
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(schedule)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'time' not in columns:
        try:
            cursor.execute("ALTER TABLE schedule ADD COLUMN time TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError as e:
            print(f"Error adding column: {e}")

    conn.commit()
    conn.close()
    
def add_game(game_date, opponent, location, time):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO schedule (game_date, opponent, location, time) VALUES (?, ?, ?, ?)',
                   (game_date, opponent, location, time))
    conn.commit()
    conn.close()
    
def get_games_by_date(game_date):
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schedule WHERE game_date = ?', (game_date,))
    games = cursor.fetchall()
    conn.close()
    return games

def delete_all_games():
    conn = sqlite3.connect('raptors.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM schedule')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="schedule"')
    
    conn.commit()
    conn.close()