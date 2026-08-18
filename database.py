import sqlite3
import os

DB_NAME = "candlelight.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_database(): #creates player-profile table
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_profile (
            profile_id      INTEGER PRIMARY KEY,
            total_runs      INTEGER NOT NULL DEFAULT 0,
            total_deaths    INTEGER NOT NULL DEFAULT 0,
            highscore       INTEGER NOT NULL DEFAULT 0,
            furthest_depth  INTEGER NOT NULL DEFAULT 0
        )
    """)

    # ensure the single profile row exists
    cursor.execute("SELECT COUNT(*) FROM player_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO player_profile (profile_id) VALUES (1)")

    conn.commit()
    conn.close()

def get_profile(): #returns profile as dictionary
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_runs, total_deaths, highscore, furthest_depth
        FROM player_profile WHERE profile_id = 1
    """)
    row = cursor.fetchone()
    conn.close()

    return {
        "total_runs": row[0],
        "total_deaths": row[1],
        "highscore": row[2],
        "furthest_depth": row[3],
    }


def record_run(score, rooms_cleared): #updates profile at end of run
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE player_profile
        SET total_runs     = total_runs + 1,
            total_deaths   = total_deaths + 1,
            highscore      = MAX(highscore, ?),
            furthest_depth = MAX(furthest_depth, ?)
        WHERE profile_id = 1
    """, (score, rooms_cleared))

    conn.commit()
    conn.close()