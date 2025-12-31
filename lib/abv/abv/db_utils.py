"""Database utility functions for ABV Song Management"""

import sqlite3
import os


def create_current_mdlist_from_db(directory):
    """
    Query songs.db for current songs (current=1) and create current_mdlist.md
    
    Args:
        directory (str): Base directory path (e.g., "../../")
    
    Returns:
        str: Path to the created markdown file, or None if failed
    """
    # Database path
    db_path = os.path.join(directory, "songs.db")
    output_path = os.path.join(directory, "current_mdlist.md")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query current songs (current=1), ordered by song_name
        cursor.execute("""
            SELECT song_name, md_text, dir, season 
            FROM songs 
            WHERE current = 1 
            ORDER BY song_name
        """)
        
        current_songs = cursor.fetchall()
        conn.close()
        
        if not current_songs:
            print("No current songs found in database")
            return None
        
        # Generate markdown content
        markdown_content = []
        markdown_content.append("### Current Repertoire\n")
        markdown_content.append(f"*Generated from songs.db - {len(current_songs)} current songs*\n\n")
        
        for song_name, md_text, dir_name, season in current_songs:
            # Add the song content
            if md_text:
                markdown_content.append(md_text)
                if not md_text.endswith('\n'):
                    markdown_content.append('\n')
            else:
                # If no md_text, create basic entry
                markdown_content.append(f"- {song_name}\n")
            
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(markdown_content)
        
        print(f"✓ Created {output_path} with {len(current_songs)} current songs")
        return output_path
        
    except Exception as e:
        print(f"Error creating current_mdlist.md: {e}")
        return None


def get_current_songs(directory):
    """
    Query songs.db for current songs (current=1) and return them as a list
    
    Args:
        directory (str): Base directory path (e.g., "../../")
    
    Returns:
        list: List of tuples (song_name, md_text, dir, season) for current songs
    """
    db_path = os.path.join(directory, "songs.db")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT song_name, md_text, dir, season 
            FROM songs 
            WHERE current = 1 
            ORDER BY song_name
        """)
        
        current_songs = cursor.fetchall()
        conn.close()
        
        return current_songs
        
    except Exception as e:
        print(f"Error querying current songs: {e}")
        return []


def update_song_current_status(directory, song_name, is_current):
    """
    Update the current status of a song in the database
    
    Args:
        directory (str): Base directory path
        song_name (str): Name of the song to update
        is_current (bool): True to mark as current, False to mark as non-current
    
    Returns:
        bool: True if successful, False otherwise
    """
    db_path = os.path.join(directory, "songs.db")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE songs 
            SET current = ? 
            WHERE song_name = ?
        """, (1 if is_current else 0, song_name))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            status = "current" if is_current else "non-current"
            print(f"✓ Updated '{song_name}' to {status}")
            return True
        else:
            print(f"✗ Song '{song_name}' not found in database")
            return False
            
    except Exception as e:
        print(f"Error updating song status: {e}")
        return False