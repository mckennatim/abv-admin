from email.mime import message
from fileinput import filename
import abv
from bs4 import BeautifulSoup
import re
import markdown
import markdown2
import json
import sqlite3

def setup(directory):
    global abv
    import abv
    from importlib import reload
    reload(abv)
    global tryit, local, abvpath
    tryit = "https://tryit.parleyvale.com/abv/process/"
    local = "http://localhost:8000/abv/process/"
    abvpath = "https://abvchorus.org/"
    return directory, tryit, local, abvpath


def html_list_to_md(ul, indent=0):
    # print(ul)
    md = ""
    for li in ul.find_all("li", recursive=False):
        # Get text and handle links
        line = ""
        for child in li.children:
          if isinstance(child, str):
            line += child.strip()+" "
          elif child.name == "a":
            line += f"[{child.text.strip()}]({child['href']}) "
            # Markdown list item
        md += "  " * indent + f"- {line}\n"
        # Handle nested <ul>
        for child_ul in li.find_all("ul", recursive=False):
            md += html_list_to_md(child_ul, indent + 1)
    # Handle sibling <ul> (not inside <li>)
    for child_ul in ul.find_all("ul", recursive=False):
        md += html_list_to_md(child_ul, indent + 1)
    return md

def split_html(fixed_html):
    phrase = 'Recorded performances'
    tag = '</ul>'
    phrase_idx = fixed_html.find(phrase)
    if phrase_idx == -1:
        raise ValueError(f"Phrase '{phrase}' not found.")
    # Find next occurrence of '</u>' after the phrase
    tag_idx = fixed_html.find(tag, phrase_idx)
    if tag_idx == -1:
        raise ValueError(f"Tag '{tag}' not found after '{phrase}'.")
    split_idx = tag_idx + len(tag)  # Split after the tag
    header = fixed_html[:split_idx]
    body = fixed_html[split_idx:]
    print("HTML split into header and songlist.")
    return header, body 

def pre_process(html):
  import re
  from bs4 import BeautifulSoup
  def fix_orphaned_ul(html):
    soup = BeautifulSoup(html, "html.parser")
    # Find all <ul> tags
    for ul in soup.find_all("ul"):
      prev = ul.find_previous_sibling("li")
      # If <ul> is not inside a <li> but immediately follows one
      if prev and ul.parent.name != "li":
        prev.append(ul.extract())
    return str(soup)
  html_clean = re.sub(r'\s+', ' ', html)
  fixed_html = fix_orphaned_ul(html_clean)
  print("Pre-processing complete.")
  return fixed_html

def html_list_to_md(ul, indent=0):
    # print(ul)
    md = ""
    for li in ul.find_all("li", recursive=False):
        # Get text and handle links
        line = ""
        for child in li.children:
          if isinstance(child, str):
            line += child.strip()+" "
          elif child.name == "a":
            line += f"[{child.text.strip()}]({child['href']}) "
            # Markdown list item
        md += "  " * indent + f"- {line}\n"
        # Handle nested <ul>
        for child_ul in li.find_all("ul", recursive=False):
            md += html_list_to_md(child_ul, indent + 1)
    # Handle sibling <ul> (not inside <li>)
    for child_ul in ul.find_all("ul", recursive=False):
        md += html_list_to_md(child_ul, indent + 1)
    return md

def create_songlist_md(soup):
    markdown = ""
    for ul in soup.find_all("ul", recursive=False):
        markdown += html_list_to_md(ul)
    return markdown

def create_current_songs_table(directory):
    import sqlite3
    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    c = conn.cursor() 
    c.execute('''
    CREATE TABLE IF NOT EXISTS current_songs (
      song TEXT,
      season TEXT
    )
    ''')
    conn.commit()   
    conn.close()
    print("current_songs table created (if not exists).")

def create_current_mdlist_from_db(directory):
    """
    Query songs.db for current songs (current=1) and create current_mdlist.md
    Args:
        directory (str): Base directory path (e.g., "../../")
    Returns:
        str: Path to the created markdown file
    """
    message = ""
    import sqlite3
    import os
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
            message += "No current songs found in database\n"
            return None
        # Generate markdown content
        markdown_content = []
        markdown_content.append("### Current Repertoire\n")
        markdown_content.append(f"*Generated from songs.db - {len(current_songs)} current songs*\n")
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
        message += f"✓ Created {output_path} with {len(current_songs)} current songs\n"
        return message
    except Exception as e:
        message += f"Error creating current_mdlist.md: {e}\n"
        return message

def extract_dir(md_text): 
    # Find first link containing /print/ or /audio/
    match = re.search(r'\((resources/audio/([^/]+)/)', md_text)
    if match:
        cleaned = abv.clean_txt_or_fname(match.group(2))
        return cleaned.lower()
    else:
        return abv.make_dir_from_0level_lines(md_text)[0]

def recreate_song_db(directory, md_list):
    import abv
    import re
    import sqlite3
    from bs4 import BeautifulSoup

    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS songs')
    c.execute('''
    CREATE TABLE songs (
      song_name TEXT,
      md_text TEXT,
      dir TEXT,
      current INTEGER,
      season TEXT
    )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_song_name ON songs(song_name)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_current ON songs(current)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_current_season ON songs(current, season)")
    # print(md_list)
    lines = md_list.splitlines()
    records = []
    song_name = None
    md_text = ""
    for line in lines:
      if re.match(r'^- ', line):  # Level 0 item
        if song_name:
          dir_val = extract_dir(md_text)
          current = 0
          season = None
          records.append((song_name.strip(), md_text.strip(), dir_val, current, season))
        song_name = line[2:].strip()
        md_text = "- "+ song_name + "\n"
      else:
        md_text += line + "\n"
    # Add last record
    if song_name:
      dir_val = extract_dir(md_text)
      records.append((song_name.strip(), md_text.strip(), dir_val, current, season))
    c.executemany('INSERT INTO songs (song_name, md_text, dir, current, season) VALUES (?, ?, ?, ?, ?)', records)
    conn.commit()
    conn.close()
    print(f"{directory}songs.db database recreated from markdown list.")

def create_mdList_from_legacy(directory):
    import abv
    import re
    import sqlite3
    from bs4 import BeautifulSoup
    fileroot = "music-complete"
    filehtml = fileroot + ".html" 
    abv.download_abv([filehtml])  
    fixed_html = pre_process(open(filehtml, encoding="utf-8").read())
    header, songlist = split_html(fixed_html)
    headerloc = directory+"header.html"
    with open(headerloc, "w", encoding="utf-8") as f:
        f.write(header)
    songlistloc = directory+"songlist.html"
    with open(songlistloc, "w", encoding="utf-8") as f:
        f.write(songlist)    
    # print(songlist)
    soup = BeautifulSoup(songlist, "html.parser")
    md = create_songlist_md(soup)
    print("Markdown conversion complete.")
    mdlistloc = directory+"mdList.md"
    with open(mdlistloc, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown file written to {directory}mdList.md")
    return md

def create_songdb_from_legacy(directory):
    md_list = create_mdList_from_legacy(directory)
    recreate_song_db(directory, md_list)

def preprocess_and_save(directory,filename):
    fileroot = filename.split('.')[0]
    filepath =directory + filename
    print(filepath)
    fixed_html = pre_process(open(filepath, encoding="utf-8").read())
    soup = BeautifulSoup(fixed_html, 'html.parser')
    formatted_html = soup.prettify()
    proc_name = "processed.html"
    loc = directory + proc_name
    with open(loc, "w", encoding="utf-8") as f:
        f.write(formatted_html)
    return proc_name

def split_to_songlist_and_header(directory,filename):
    filepath =directory + filename
    fixed_html = pre_process(open(filepath, encoding="utf-8").read())
    header, songlist = split_html(fixed_html)
    headerloc = directory+"header.html"
    with open(headerloc, "w", encoding="utf-8") as f:
        f.write(header)
    mdloc= directory + "songlist.html"   
    with open(mdloc, "w", encoding="utf-8") as f:
        f.write(songlist)  
    print("songlist.html and header.html created.")
    soup = BeautifulSoup(songlist, "html.parser")
    md = create_songlist_md(soup)
    print("Markdown conversion complete.")
    mdlistloc = directory+"songlist.md"
    with open(mdlistloc, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown file written to {directory}songlist.md")
    return md

def create_mdList_from_html(directory, filename):
    import abv
    import re
    import sqlite3
    from bs4 import BeautifulSoup 
    filepath =directory + filename
    fixed_html = pre_process(open(filepath, encoding="utf-8").read())
    header, songlist = split_html(fixed_html)
    headerloc = directory+"header.html"
    with open(headerloc, "w", encoding="utf-8") as f:
        f.write(header)
    songlistloc = directory+"songlist.html"
    with open(songlistloc, "w", encoding="utf-8") as f:
        f.write(songlist)    
    # print(songlist)
    soup = BeautifulSoup(songlist, "html.parser")
    md = create_songlist_md(soup)
    print("Markdown conversion complete.")
    mdlistloc = directory+"mdList.md"
    with open(mdlistloc, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown file written to {directory}mdList.md")
    return md

def get_lib_info(lib):
  # List all functions and attributes in the abv library
  print("All attributes in abv:")
  print(dir(lib))
  print("\n" + "="*50)
  # Filter to show only functions (callable objects)
  print("Functions only:")
  functions = [name for name in dir(lib) if callable(getattr(lib, name)) and not name.startswith('_')]
  for func in functions:
      print(f"  {func}")
  print("\n" + "="*50)
  # Get help/documentation for the module
  print("Module documentation:")
  help(lib)

def recombine_html(directory, header_file, body_file, footer_file, output_file):
    headerloc = directory + header_file
    with open(headerloc, "r", encoding="utf-8") as f:
        header = f.read()
    bodyloc = directory + body_file
    with open(bodyloc, "r", encoding="utf-8") as f:
        body = f.read()
    footerloc = directory + footer_file
    with open(footerloc, "r", encoding="utf-8") as f:
        footer = f.read()
    combined_html = header + body + footer
    soup = BeautifulSoup(combined_html, 'html.parser')
    pretty_html = soup.prettify()
    outputloc = directory + output_file
    with open(outputloc, "w", encoding="utf-8") as f:
        f.write(pretty_html)
    message = f"Recombined HTML written to {output_file}\n"
    return message

def md_to_html(directory, md_file, html_file):
    import mistune 
    mdloc=directory + md_file
    with open(mdloc, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = mistune.html(md_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    h3_tag = soup.find('h3')
    if h3_tag:
        h3_tag['class'] = 'centitle'
    p_tag = soup.find('p')
    if p_tag:
        p_tag['class'] = 'songlist'
    em_tag = soup.find('em')
    if em_tag:
        em_tag['class'] = 'generated'
    first_ul = soup.find('ul')  # This gets the first ul it encounters
    if first_ul:
        first_ul['class'] = 'songlist'
    pretty_html = soup.prettify()
    htmlloc = directory + html_file
    with open(htmlloc, 'w', encoding='utf-8') as f:
        f.write(pretty_html)
    message = f"Converted {directory}{md_file} to {directory}{html_file}\n"
    return message

def recombine_head_md_foot(directory, head_file, md_file, footer_file, output_file):
    root = md_file.split('.')[0]
    mdhtml = root + ".html"
    md_to_html(directory, md_file, mdhtml)
    headloc = directory + head_file
    with open(headloc, "r", encoding="utf-8") as f:
        head = f.read()
    mdListloc=directory+ "mdList.html"   
    with open(mdListloc, "r", encoding="utf-8") as f:
        md = f.read()
    footerloc= directory + footer_file
    with open(footerloc, "r", encoding="utf-8") as f:
        footer = f.read()
    combined_md = head + "\n" + md + "\n" + footer
    soup = BeautifulSoup(combined_md, 'html.parser')
    pretty_html = soup.prettify()
    print("Recombining head, markdown, and footer...")
    outputloc = directory + output_file
    with open(outputloc, "w", encoding="utf-8") as f:
        f.write(pretty_html)
    # music_complete_loc = directory + "music-complete.html"    
    # with open(music_complete_loc, "w", encoding="utf-8") as f:
    #     f.write(pretty_html)
    print(f"Recombined markdown written to {directory}{output_file}")
    # print(f"Also updated {music_complete_loc}")

def save_resource_list(directory,array):
    filename = f"{directory}resource_list.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(array, f)
    return array

def open_resource_list(directory):
    filepath = directory + "resource_list.json"
    with open(filepath, 'r') as f:
        file_array = json.load(f)
    return file_array

def delete_resource_list(directory):
    filename = f"{directory}resource_list.json"
    with open(filename, "w") as f:
        f.write("[]")
    return "resource_list.json reset to []"


def recreate_current_songs_from_songs_db(directory):
    import abv
    import sqlite3
    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    c = conn.cursor()
    c.execute('DELETE FROM current_songs;')
    c.execute('''
    INSERT INTO current_songs (song, season)
    SELECT song_name, season FROM songs WHERE current = 1;
    ''')
    conn.commit()
    conn.close()
    print("current_songs table recreated from songs.db.")       

def mark_songs_current_from_current_songs(directory):
    import abv
    import sqlite3
    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    c = conn.cursor()
    c.execute('UPDATE songs SET current = 0;')
    c.execute('''
    UPDATE songs 
    SET current = 1 
    WHERE song_name IN (SELECT song FROM current_songs);
    ''')
    conn.commit()
    conn.close()
    print("Songs marked current from current_songs table.") 

def create_mdlist_from_db(directory):
    import sqlite3
    import os
    message = ""
    # Database path
    db_path = os.path.join(directory, "songs.db")
    output_path = os.path.join(directory, "mdList_from_songs.md")
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
            ORDER BY song_name
        """)
        songs = cursor.fetchall()
        conn.close()
        if not songs:
            message += "No current songs found in database\n"
            return message
        # Generate markdown content
        markdown_content = []
        markdown_content.append("### Complete Repertoire\n")
        markdown_content.append(f"*Generated from songs.db - {len(songs)} current songs*\n")
        for song_name, md_text, dir_name, season in songs:
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
        message += f"✓ Created {output_path} with {len(songs)} songs\n"
        return message
    except Exception as e:
        message += f"Error creating {output_path}: {e}\n"
        return message

# def create_mdlist_from_db(directory):
#     import abv
#     import sqlite3
#     import os
#     # Database path
#     db_path = os.path.join(directory, "songs.db")
#     output_path = os.path.join(directory, "current_mdlist.md")
#     if not os.path.exists(db_path):
#         raise FileNotFoundError(f"Database not found at {db_path}") 
#     conn = sqlite3.connect(db_path)
#     c = conn.cursor()
#     c.execute('SELECT song_name, md_text, dir, season FROM songs ORDER BY song_name ASC')
#     rows = c.fetchall()
#     # md_list = "".join(row[0] for row in rows)
#     conn.close()
#     markdown_content = []
#     markdown_content.append("### Songs\n")
#     markdown_content.append(f"*Generated from songs.db - {len(rows)} songs*\n")
#     for song_name, md_text, dir, season in rows:
#         # Add the song content
#         markdown_content.append(md_text)
#         if not md_text.endswith('\n'):
#             markdown_content.append('\n')
#         # if md_text:
#         #     markdown_content.append(md_text)
#         #     if not md_text.endswith('\n'):
#         #         markdown_content.append('\n')
#         # else:
#         #     # If no md_text, create basic entry
#         #     markdown_content.append(f"- {song_name}\n")
#     # Write to file
        
#     mdlistloc = directory+"mdList_from_songs.md"
#     with open(mdlistloc, "w", encoding="utf-8") as f:
#         f.writelines(markdown_content)
#     print(f"Markdown list created from database at {mdlistloc}")
#     return markdown_content

def copy_from_to(directory, src, dest):
    import shutil
    src = directory + src
    dest = directory + dest
    shutil.copy2(src, dest)
    message = f"Copied from {src} to {dest}\n"
    return message

def reset_current(directory,json_file):
    import abv
    import json
    filepath = directory + json_file
    print(filepath)
    with open(filepath, 'r') as f:
        names = json.load(f)
    print(names)
    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    c = conn.cursor()
    c.execute('UPDATE songs SET current = 0;')
    for name in names:
        c.execute('UPDATE songs SET current = 1 WHERE song_name = ?;', (name,))
    conn.commit()
    conn.close()
    print("Current songs reset from JSON file.")

def update_current(directory,json_file):
    message = ""
    import abv
    import json
    songsdbloc = directory + "songs.db"  
    conn = sqlite3.connect(songsdbloc)
    cursor = conn.cursor()
    cursor.execute("SELECT song_name FROM songs WHERE current = 1;")
    results = cursor.fetchall()
    conn.close()
    song_names = [row[0] for row in results]
    output_path = directory + json_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(song_names, f, indent=2, ensure_ascii=False)
    message += f"✅ Exported {len(song_names)} songs as simple array to {output_path}\n"
    message += f"song_names: {song_names}\n"
    return message

def upload_file(directory, updated_file, remote_dir, replaced_file):
    import abv
    local_path = directory + updated_file
    abv.upload_abv([local_path], remote_dir, [replaced_file])
    print(f"Uploaded {updated_file} to {remote_dir} as {replaced_file}")

def clean_txt_or_fname(original_filename):
    #"""Clean filename while preserving extension - ABV style"""
    original_filename = original_filename.strip()
    original_filename = original_filename.replace('%20', '_')
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        # Replace all non-alphanumeric characters with underscores in name part
        cleaned_name = ''.join(c if c.isalnum() else '_' for c in name)
        return f"{cleaned_name}.{ext}"
    else:
        # No extension, clean the whole filename
        return ''.join(c if c.isalnum() else '_' for c in original_filename)

def find_zero_level_lines(md_text):
    lines = md_text.strip().split('\n')
    zero_level_lines = [line for line in lines if line.startswith('- ')]
    nodash_lines = [line[2:] for line in zero_level_lines]
    nd_strip_lines = [line.strip() for line in nodash_lines]
    return nd_strip_lines

def make_dir_from_0level_lines(md_text):
    zlines = find_zero_level_lines(md_text)
    nopare_lines = [line.split('(')[0] for line in zlines]
    clean_lines = [clean_txt_or_fname(line) for line in nopare_lines]
    return [line.lower() for line in clean_lines]

def add_step(filename, localdir, otherdir=None):
    dname = localdir.rstrip('/').split('/')[-1]+"/" 
    tryit = "https://tryit.parleyvale.com/abv/"
    theurl = f"{tryit}{dname}{filename}"
    stepsloc = f"{localdir}/steps.json"
    with open(stepsloc, "r") as f:
        steps = json.load(f)    
    if otherdir:
        url = f"{otherdir}/{filename}"
    else:
        url = theurl
    steps.append(url)
    with open(stepsloc, "w") as f:
        json.dump(steps, f, indent=2)
    for step in steps:
        print("- " + step)
    
        
def run_sync_back_to_legacy(directory):
    message = ""
    message += create_mdlist_from_db(directory)
    
    md_file = "mdList_from_songs.md"
    html_file = "mdList_from_songs.html" 
    message += md_to_html(directory, md_file, html_file)
    
    header_file = "header.html"
    body_file = "mdList_from_songs.html"
    footer_file = "footer.html"
    output_file = "music-complete-updated.html"
    message += recombine_html(directory,header_file, body_file, footer_file, output_file)
    
    updated_file = "music-complete-updated.html"
    replaced_file = "music-complete.html"
    message += copy_from_to(directory,updated_file, replaced_file)
    
    filename = "music-complete.html"
    backupname = "music-complete_backup.html"
    remote_dir = "public_html/"
    originalpath = f"{remote_dir}{filename}"
    backuppath = f"{remote_dir}{backupname}"
    message += abv.create_remote_backup(originalpath, backuppath)
    
    fromdir = directory
    todir = "public_html/"
    tofiles = ["music-complete.html", "styles.css"]
    files_array =[
        [f"{fromdir}music-complete.html", f"{todir}music-complete.html"],
        [f"{fromdir}styles.css", f"{todir}styles.css"]
    ]
    message += abv.upload_many_files(files_array)
    
    message += abv.create_current_mdlist_from_db(directory)
    
    md_file = "current_mdlist.md"
    html_file = "current_mdlist.html"
    message += abv.md_to_html(directory, md_file, html_file)

    header_file = "header.html"
    body_file = "current_mdlist.html"
    footer_file = "footer.html"
    output_file = "music-current-updated.html"
    message += abv.recombine_html(directory,header_file, body_file, footer_file, output_file)

    updated_file = "music-current-updated.html"
    replaced_file = "music-current.html"
    message += copy_from_to(directory,updated_file, replaced_file)
    
    orig_filename = "music-current.html"
    backup_filename = "music-current_backup.html"
    original_path = f"{remote_dir}{orig_filename}"
    backup_path = f"{remote_dir}{backup_filename}"
    message += abv.create_remote_backup(original_path, backup_path)
    
    filename = "music-current.html"
    localpath = f"{directory}{filename}"
    remotepath = f"{remote_dir}{filename}"
    message += abv.upload_afile(localpath, remotepath)
    print(message)
    return message
