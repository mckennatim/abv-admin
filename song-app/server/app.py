#!/usr/bin/env python3
"""
Flask server for ABV song management system
Simple proof of concept
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import sys
import json
import logging
import re
import subprocess
import tempfile
import shutil
from werkzeug.utils import secure_filename
import abv
from importlib import reload

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add lib to path to import abv
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import abv

app = Flask(__name__)
CORS(app)  # Enable CORS for development

# Configuration
directory = '../process/'
DATABASE = directory + 'songs.db'
UPLOAD_FOLDER = '../resources/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'html', 'css', 'js', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size (10,000K)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def camel_case_filename(filename):
    """Convert filename to camelCase, removing spaces and special characters"""
    if '.' in filename:
        name, extension = filename.rsplit('.', 1)
    else:
        name, extension = filename, ''
    
    # Split on spaces, underscores, hyphens
    words = name.replace('_', ' ').replace('-', ' ').split()
    
    if not words:
        return filename  # Return original if no valid words
    
    # First word lowercase, subsequent words capitalized
    camel_name = words[0].lower()
    for word in words[1:]:
        if word:  # Skip empty words
            camel_name += word.capitalize()
    
    # Remove any remaining special characters except alphanumeric
    camel_name = ''.join(char for char in camel_name if char.isalnum())
    
    # Add extension back
    if extension:
        return f"{camel_name}.{extension.lower()}"
    return camel_name

def replace_spaces_with_underscores(filename):
    """Replace spaces in filename with underscores"""
    return filename.replace(' ', '_').replace('%20', '_').replace('%27', '_').replace("'", '_')      

def get_db_connection():
    # """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def clean_filename_for_abv(original_filename):
    """Clean filename while preserving extension - ABV style with duplicate underscore removal"""
    original_filename = original_filename.strip()
    
    if '.' in original_filename:
        name, ext = original_filename.rsplit('.', 1)
        # Replace all non-alphanumeric characters with underscores in name part
        cleaned_name = ''.join(c if c.isalnum() else '_' for c in name)
        # Remove duplicate underscores and leading/trailing underscores
        cleaned_name = re.sub(r'_+', '_', cleaned_name).strip('_')
        return f"{cleaned_name}.{ext}"
    else:
        # No extension, clean the whole filename
        cleaned_filename = ''.join(c if c.isalnum() else '_' for c in original_filename)
        # Remove duplicate underscores and leading/trailing underscores
        return re.sub(r'_+', '_', cleaned_filename).strip('_')

def generate_directory_name(song_name):
    """
    Generate filesystem-safe directory name from song name
    
    Args:
        song_name (str): Original song name
        
    Returns:
        str: Directory-safe name
    """
    import re
    
    return re.sub(r'[^a-z0-9]+', '_', 
                  song_name.lower().strip()).strip('_').replace('__', '_')

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory('../app', 'index.html')

@app.route('/api/')
def api_root():
    """API root endpoint for testing"""
    return jsonify({
        'message': 'ABV Song Management API is running!',
        'version': '1.0',
        'endpoints': [
            '/api/songs (GET, POST)',
            '/api/songs/<id> (GET, PUT)',
            '/api/upload',
            '/api/sync',
            '/api/sync-back'
        ]
    })

@app.route('/test')
def test():
    """Simple test endpoint"""
    return '<h1>ABV Server is running!</h1><p>Flask server is working correctly.</p>'

@app.route('/app/<path:filename>')
def serve_app_files(filename):
    """Serve static app files"""
    return send_from_directory('../app', filename)

@app.route('/api/songs', methods=['GET'])
def get_songs():
    """Get list of all songs"""
    try:
        logger.info(f"Getting all songs from {DATABASE}")
        conn = get_db_connection()
        songs = conn.execute('SELECT rowid, * FROM songs ORDER BY song_name').fetchall()
        conn.close()
        
        # Convert to list of dicts
        songs_list = [dict(song) for song in songs]
        logger.info(f"Returning {len(songs_list)} songs")
        return jsonify(songs_list)
    except Exception as e:
        logger.error(f"Error getting songs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>', methods=['GET'])
def get_song(song_id):
    """Get specific song details"""
    try:
        conn = get_db_connection()
        song = conn.execute('SELECT rowid, * FROM songs WHERE rowid = ?', (song_id,)).fetchone()
        conn.close()
        
        if song:
            return jsonify(dict(song))
        else:
            return jsonify({'error': 'Song not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs', methods=['POST'])
def create_song():
    """Create a new song with proper dir field handling"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('song_name'):
            return jsonify({'error': 'Song name is required'}), 400
        
        song_name = data.get('song_name').strip()
        dir_name = data.get('dir', '').strip()
        
        # If no dir provided, generate one from song_name
        if not dir_name:
            dir_name = generate_directory_name(song_name)
        
        logger.info(f"Creating new song: '{song_name}' with directory: '{dir_name}'")
        
        conn = get_db_connection()
        
        # Check if song with same name or directory already exists
        existing = conn.execute(
            'SELECT song_name FROM songs WHERE song_name = ? OR dir = ?',
            (song_name, dir_name)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'error': f'Song with name "{song_name}" or directory "{dir_name}" already exists'
            }), 400
        
        # Insert new song with all required fields
        cursor = conn.execute('''
            INSERT INTO songs (song_name, md_text, dir, current, season)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            song_name,
            data.get('md_text', ''),
            dir_name,
            data.get('current', 0),
            data.get('season')
        ))
        
        song_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created new song with ID: {song_id}, name: '{song_name}', dir: '{dir_name}'")
        
        return jsonify({
            'success': True,
            'song_id': song_id,
            'song_name': song_name,
            'dir': dir_name,
            'message': f'Song "{song_name}" created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating song: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    """Update song record"""
    try:
        data = request.get_json()
        conn = get_db_connection()
        
        conn.execute('''
            UPDATE songs 
            SET song_name = ?, md_text = ?, dir = ?, current = ?, season = ?
            WHERE rowid = ?
        ''', (
            data.get('song_name'),
            data.get('md_text'),
            data.get('dir'),
            data.get('current', 0),
            data.get('season'),
            song_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    """Delete a song from the database"""
    try:
        conn = get_db_connection()
        
        # First check if song exists
        cursor = conn.cursor()
        cursor.execute('SELECT song_name FROM songs WHERE rowid = ?', (song_id,))
        song = cursor.fetchone()
        
        if not song:
            conn.close()
            return jsonify({'error': 'Song not found'}), 404
        
        # Delete the song
        cursor.execute('DELETE FROM songs WHERE rowid = ?', (song_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Song "{song[0]}" deleted successfully'
        })
        
    except sqlite3.Error as e:
        print(f"Database error deleting song {song_id}: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Error deleting song {song_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def convert_docx_to_pdf(docx_path, pdf_path):
    """Convert .docx to PDF using LibreOffice headless mode"""
    try:
        # Create temporary directory for conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run LibreOffice in headless mode
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                docx_path
            ]
            
            logger.info(f"Running LibreOffice conversion: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Find the generated PDF
                docx_name = os.path.basename(docx_path)
                pdf_name = os.path.splitext(docx_name)[0] + '.pdf'
                temp_pdf = os.path.join(temp_dir, pdf_name)
                
                if os.path.exists(temp_pdf):
                    # Ensure target directory exists
                    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                    
                    # Move to final location
                    shutil.move(temp_pdf, pdf_path)
                    logger.info(f"✅ Converted using LibreOffice: {pdf_path}")
                    return True
                else:
                    logger.error(f"❌ Expected PDF not found at: {temp_pdf}")
                    return False
            else:
                logger.error(f"❌ LibreOffice conversion failed: {result.stderr}")
                return False
                
    except subprocess.TimeoutExpired:
        logger.error("❌ LibreOffice conversion timed out")
        return False
    except Exception as e:
        logger.error(f"❌ LibreOffice conversion error: {e}")
        return False

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': 'File size exceeds the maximum limit of 10MB (10,000KB)',
        'max_size': '10MB'
    }), 413

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file to resources directory with ABV filename cleaning"""
    try:
        logger.info(f"Upload request received. Files: {list(request.files.keys())}")
        logger.info(f"Form data: {dict(request.form)}")
        
        if 'file' not in request.files:
            logger.error("No 'file' key in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        folder = request.form.get('folder', 'general')
        cleaned_name = request.form.get('cleanedName')  # From ABVFileUploader
        original_name = request.form.get('originalName')  # From ABVFileUploader
        full_path = request.form.get('fullPath')  # From ABVFileUploader
        
        logger.info(f"File received: filename='{file.filename}', folder='{folder}'")
        logger.info(f"ABV data: cleanedName='{cleaned_name}', originalName='{original_name}', fullPath='{full_path}'")
        
        if file.filename == '':
            logger.error("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Use ABV cleaned filename if provided, otherwise clean it ourselves
            if cleaned_name:
                filename = secure_filename(cleaned_name)
                original_filename = original_name or file.filename
            else:
                # Fallback to original cleaning method
                original_filename = file.filename
                filename_u = replace_spaces_with_underscores(original_filename)
                filename = secure_filename(filename_u)
            
            logger.info(f"File upload: '{original_filename}' -> '{filename}'")
            
            # Check if file needs conversion (.docx to PDF)
            file_ext = os.path.splitext(original_filename)[1].lower()
            needs_conversion = file_ext == '.docx'
            
            if needs_conversion:
                # For .docx files, change the target filename to .pdf
                pdf_filename = os.path.splitext(filename)[0] + '.pdf'
                logger.info(f"📄 .docx file detected, will convert to: {pdf_filename}")
            else:
                pdf_filename = filename
            
            # Handle full resource paths vs simple folder names
            if folder.startswith('resources/'):
                # Full path provided (e.g., "resources/audio/ale_brider/")
                folder_path = folder.replace('resources/', '').rstrip('/')
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_path)
                relative_path = f"resources/{folder_path}/{pdf_filename}"
            else:
                # Simple folder name provided (e.g., "audio")
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
                relative_path = f"resources/{folder}/{pdf_filename}"
            
            # Use full_path if provided by ABVFileUploader (adjust for conversion)
            if full_path:
                if needs_conversion:
                    # Convert .docx extension to .pdf in the path
                    relative_path = os.path.splitext(full_path)[0] + '.pdf'
                else:
                    relative_path = full_path
                # Extract upload path from relative_path
                path_parts = relative_path.replace('resources/', '').split('/')
                if len(path_parts) > 1:
                    folder_path = '/'.join(path_parts[:-1])
                    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_path)
            
            # Create directory if it doesn't exist
            os.makedirs(upload_path, exist_ok=True)
            
            if needs_conversion:
                # Handle .docx to PDF conversion
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                    file.save(temp_docx.name)
                    temp_docx_path = temp_docx.name
                
                try:
                    final_file_path = os.path.join(upload_path, pdf_filename)
                    success = convert_docx_to_pdf(temp_docx_path, final_file_path)
                    
                    if success:
                        logger.info(f"✅ File converted and uploaded: {relative_path}")
                        logger.info(f"=== UPLOADED FILE TRACKING === Converted file added to pending sync: {relative_path}")
                        
                        return jsonify({
                            'success': True,
                            'filename': pdf_filename,
                            'original_filename': original_filename,
                            'path': relative_path,
                            'cleaned_name': pdf_filename,
                            'converted': True,
                            'conversion_type': 'docx_to_pdf',
                            'message': f'File converted from .docx to PDF and uploaded as {pdf_filename}'
                        })
                    else:
                        return jsonify({'error': 'PDF conversion failed'}), 500
                        
                finally:
                    # Clean up temporary file
                    os.unlink(temp_docx_path)
            else:
                # Regular file upload (no conversion)
                file_path = os.path.join(upload_path, filename)
                file.save(file_path)
                
                # Return the relative path for markdown links
                logger.info(f"File uploaded: {relative_path}")
                logger.info(f"=== UPLOADED FILE TRACKING === File added to pending sync: {relative_path}")
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'original_filename': original_filename,
                    'path': relative_path,
                    'cleaned_name': filename,
                    'converted': False
                })
        else:
            logger.error(f"File type not allowed: {file.filename}")
            return jsonify({'error': 'File type not allowed'}), 400
            
    except Exception as e:
        logger.error(f"Upload exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync_with_legacy():
    """Sync database with legacy HTML site"""
    import abv
    from importlib import reload
    reload(abv)
    
    remote_dir = "/public_html/"
    filename = "music-complete.html"
    try:
        import abv
        from importlib import reload
        reload(abv)
        # directory = "../../process/"
        # Download legacy music-complete.html
        remote_dir ="public_html/"
        filename="music-complete.html"
        logger.info("Downloading legacy HTML...")
        abv.download_file(directory, remote_dir, filename)
        with open(directory+"steps.json", "w") as f:
            f.write("[]")
        abv.add_step(filename, directory)
        ## pre-process and save
        processed_file_name = abv.preprocess_and_save(directory, filename)
        logger.info(f"processing complete and in {processed_file_name}.")
        abv.add_step(processed_file_name, directory) 
        ## split to songlist and header
        songlist_md_text = abv.split_to_songlist_and_header(directory,processed_file_name)
        logger.info("HTML split into header.html and songlist.md_html")
        abv.add_step("songlist.html", directory)
        # recreate song database from songlist_md_text
        abv.recreate_song_db(directory, songlist_md_text)
        logger.info("Songs database recreated from songlist_md_text")
        # reset_current from currentSongs.json
        abv.reset_current(directory, "currentSongs.json")
        logger.info("Current songs reset from currentSongs.json")


        return jsonify({
            'success': True,
            'message': 'Database synced and HTML regenerated successfully',
            'steps_completed': [
                'Downloaded legacy HTML',
                'Processed and cleaned HTML',
                'Split HTML into header and songlist.md',
                'Rebuilt songs.db',
                'Reset current songs from currentSongs.json'
            ]
        })
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Sync process failed'
        }), 500

@app.route('/api/sync-back', methods=['POST'])
def sync_back_to_legacy():
    """
    Enhanced sync back functionality:
    - Always regenerates HTML from songs.db
    - Processes pending files if they exist
    - Uploads to legacy server
    """
    try:
        data = request.get_json() or {}
        files_to_sync = data.get('files', [])
        
        logger.info(f"Sync back request with {len(files_to_sync)} files")
        
        # STEP 1: ALWAYS regenerate HTML from database
        regenerate_html_from_database()
        
        # STEP 2: If there are pending files, process them
        if files_to_sync:
            logger.info(f"Processing {len(files_to_sync)} pending files")
            upload_files_to_legacy_server(files_to_sync)
        
        # STEP 3: ALWAYS upload regenerated HTML to legacy server
        upload_html_to_legacy_server()
        
        # Determine response message
        if files_to_sync:
            message = f"Regenerated HTML and processed {len(files_to_sync)} files"
        else:
            message = "Regenerated HTML from database"
            
        logger.info(f"Sync back completed: {message}")
        
        return jsonify({
            'success': True,
            'message': message,
            'files_processed': len(files_to_sync),
            'html_regenerated': True
        })
        
    except Exception as e:
        logger.error(f"Sync back error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Sync back operation failed'
        }), 500


# STUB FUNCTIONS for Sync Back Enhancement
# Replace these with your actual implementations

def regenerate_html_from_database():
    """
    STUB: Your code to reconstitute HTML from songs.db
    This should:
    1. Read all songs from the database
    2. Generate HTML pages/files
    3. Save them to the local filesystem
    """
    logger.info("STUB: Regenerating HTML from songs database...")
    # TODO: Implement your HTML generation logic here
    # Example:
    # conn = get_db_connection()
    # songs = conn.execute('SELECT * FROM songs ORDER BY song_name').fetchall()
    # generate_html_files(songs)
    # conn.close()
    pass

def upload_files_to_legacy_server(file_paths):
    """
    STUB: Your code to upload specific files to legacy server
    This handles the pending files that were recently uploaded
    """
    logger.info(f"file_paths: {file_paths}")
    abv.save_resource_list(directory,file_paths)#resource_list.json
    rl = abv.open_resource_list(directory)# ../process/
    logger.info(rl)
    message = abv.upload_abv("../", rl)
    logger.info(message)
    message = abv.delete_resource_list(directory)
    logger.info(message)
    pass

def upload_html_to_legacy_server():
    """
    STUB: Your code to upload regenerated HTML to legacy server
    This uploads the HTML files created from the database
    """
    logger.info("STUB: Uploading regenerated HTML to legacy server...")
    import abv
    from importlib import reload
    reload(abv)

    message = abv.update_current(directory,"currentSongs.json")
    logger.info(message)
    message = abv.create_mdlist_from_db(directory)
    logger.info(message)
    md_file = "mdList_from_songs.md"
    html_file = "mdList_from_songs.html" 
    message = abv.md_to_html(directory, md_file, html_file)
    logger.info(message)
    header_file = "header.html"
    footer_file = "footer.html"
    output_file = "music-complete-updated.html"
    message = abv.recombine_html(directory,header_file, html_file, footer_file, output_file)
    logger.info(message)
    updated_file = "music-complete-updated.html"
    replaced_file = "music-complete.html"
    message = abv.copy_from_to(directory,updated_file, replaced_file)
    logger.info(message)
    message =abv.backup_remote_file(directory, "music-complete.html")
    logger.info(message)
    message = abv.upload_abv(directory,["music-complete.html"])
    logger.info(message)
    message = abv.create_current_mdlist_from_db(directory)
    logger.info(message)
    md_file = "current_mdlist.md"
    html_file = "current_mdlist.html"
    message = abv.md_to_html(directory, md_file, html_file)
    logger.info(message)
    header_file = "current_head.html"
    body_file = "current_mdlist.html"
    footer_file = "footer.html"
    output_file = "music-current-updated.html"
    message = abv.recombine_html(directory,header_file, body_file, footer_file, output_file)
    logger.info(message)
    updated_file = "music-current-updated.html"
    replaced_file = "music-current.html"
    message = abv.copy_from_to(directory,updated_file, replaced_file)
    logger.info(message)
    message = abv.backup_remote_file(directory, "music-current.html")
    logger.info(message)
    message = abv.upload_abv(directory,["music-current.html"])
    logger.info(message)
    pass

def get_server_config():
    """Get appropriate host/port configuration for the current environment"""
    
    # Check if running on Windows
    is_windows = os.name == 'nt'
    
    if is_windows:
        # Windows localhost configuration - force port 8001 to avoid conflict with static server
        host = '127.0.0.1'
        
        # Try to find an available port starting from 8001 (not 8000)
        for port in range(8001, 8010):
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, port))
                    return host, port
            except OSError:
                continue
        
        # If no port found in range, use Flask default
        return host, 5000
    else:
        # Linux server configuration (tryit.parleyvale.com)
        # Bind to all interfaces for external access
        return '0.0.0.0', 5000

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE):
        print(f"Warning: Database {DATABASE} not found!")
    
    # Get environment-appropriate configuration
    host, port = get_server_config()
    
    print("=" * 60)
    print("Starting ABV Song Management Server...")
    print(f"Environment: {'Windows' if os.name == 'nt' else 'Linux'}")
    print(f"Server URL: http://{host}:{port}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Database: {DATABASE}")
    print("=" * 60)
    
    # Run with cross-platform configuration
    app.run(debug=True, host=host, port=port)