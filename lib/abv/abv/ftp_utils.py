
import ftplib
import os
import shutil
import re
from pathlib import Path
import unicodedata
from docx2pdf import convert
import io


# def download_abv(directory, file_array):
#   import ftplib
#   import sys
#   import os
#   # Configuration - modify these values
#   HOST = "ftp.abvchorus.org"
#   USERNAME = "abvch0" 
#   PASSWORD = "abeserevelt10"
#   FILES = file_array  # Files to download (can include subdirs like "images/logo.png")
#   REMOTE_DIR = "public_html/"  # Base remote directory
#   try:
#     ftp = ftplib.FTP(HOST)
#     ftp.login(USERNAME, PASSWORD)
#     # Change to base remote directory
#     if REMOTE_DIR != "/":
#         ftp.cwd(REMOTE_DIR)
    
#     for file_path in FILES:
#         # Construct full local path
#         local_full_path = os.path.join(directory, file_path)
#         remote_path = os.path.join(REMOTE_DIR, file_path)
        
#         # Check if local file exists
#         if not os.path.exists(directory):
#             print(f"✗ Local file {directory} not found, skipping...")
#             continue

#         print(f"downloading from {file_path} to {local_full_path}...")
#         # print(f"Downloading {file_path}...")
        
#         # Split path into directory and filename
#         dir_path = os.path.dirname(file_path)
#         filename = os.path.basename(file_path)
        
#         # Create local directory if it doesn't exist
#         if dir_path:
#             os.makedirs(dir_path, exist_ok=True)
#         try:
#             with open(REMOTE_DIR, 'wb') as f:
#                 ftp.retrbinary(f'RETR {filename}', f.write)
#             print(f"✓ {remote_path} downloaded")
#         except ftplib.error_perm as e:
#             print(f"✗ Error downloading {file_path}: {e}")
        
#         # Return to base directory for next file
#         if dir_path and REMOTE_DIR != "/":
#             ftp.cwd(f"/{REMOTE_DIR}")
#     ftp.quit()
#     print("All files downloaded successfully!")
#   except Exception as e:
#       print(f"Error: {e}")


# def upload_abv(directory, file_array):
#     import ftplib
#     import os
    
#     # Configuration - same as download
#     HOST = "ftp.abvchorus.org"
#     USERNAME = "abvch0" 
#     PASSWORD = "abeserevelt10"
#     FILES = file_array  # Files to upload (can include subdirs like "images/logo.png")
#     REMOTE_DIR = "public_html/"  # Base remote directory
#     message = ""
#     try:
#         ftp = ftplib.FTP(HOST)
#         ftp.login(USERNAME, PASSWORD)
        
        
#         # Change to base remote directory
#         if REMOTE_DIR != "/":
#             ftp.cwd(REMOTE_DIR)
        
#         for file_path in FILES:
#             # Construct full local path
#             local_full_path = os.path.join(directory, file_path)
            
#             # Check if local file exists
#             if not os.path.exists(local_full_path):
#                 message += f"✗ Local file {local_full_path} not found, skipping...\n"
#                 continue
            
#             message += f"Uploading {local_full_path} to {file_path}...\n"
#             # Split remote path into directory and filename
#             remote_dir_path = os.path.dirname(file_path)
#             filename = os.path.basename(file_path)
            
#             # Create remote subdirectory if needed
#             if remote_dir_path:
#                 try:
#                     # Try to create the directory structure
#                     subdirs = remote_dir_path.split('/')
#                     current_path = ""
#                     for subdir in subdirs:
#                         if subdir:  # Skip empty strings from leading slashes
#                             current_path = os.path.join(current_path, subdir).replace('\\', '/')
#                             try:
#                                 ftp.mkd(current_path)
#                                 message += f"Created remote directory: {current_path}\n"
#                             except ftplib.error_perm:
#                                 # Directory might already exist, that's ok
#                                 pass
                    
#                     # Navigate to the target remote directory
#                     ftp.cwd(remote_dir_path.replace('\\', '/'))
#                 except ftplib.error_perm as e:
#                     message += f"✗ Error accessing remote directory {remote_dir_path}: {e}\n"
#                     continue
            
#             # Upload the file using the correct local path
#             try:
#                 with open(local_full_path, 'rb') as f:
#                     ftp.storbinary(f'STOR {filename}', f)
#             except ftplib.error_perm as e:
#                 message += f"✗ Error uploading {local_full_path}: {e}\n"
#             # Return to base directory for next file
#             if remote_dir_path and REMOTE_DIR != "/":
#                 ftp.cwd(f"/{REMOTE_DIR}")
#         ftp.quit()
#     except Exception as e:
#         message += f"Error: {e}\n"
#     return message

def download_file(local_dir, remote_dir, filename):
    HOST = "ftp.abvchorus.org"
    USERNAME = "abvch0" 
    PASSWORD = "abeserevelt10"
    message = ""
    try:
        ftp = ftplib.FTP(HOST)
        ftp.login(USERNAME, PASSWORD)
        # Change to the specified remote directory
        if remote_dir != "/":
            ftp.cwd(remote_dir)
        local_full_path = os.path.join(local_dir, filename)
        # Ensure local directory exists
        os.makedirs(local_dir, exist_ok=True)
        message += f"Downloading {filename} to {local_full_path}...\n"
        with open(local_full_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        message += f"✓ {filename} downloaded to {local_full_path}\n"
        ftp.quit()
    except Exception as e:
        message += f"Error downloading file: {e}\n"
    return message

# def upload_file(local_dir, remote_dir, filename):
#     import ftplib
#     import os
#     HOST = "ftp.abvchorus.org"
#     USERNAME = "abvch0" 
#     PASSWORD = "abeserevelt10"
#     message = ""
#     try:
#         ftp = ftplib.FTP(HOST)
#         ftp.login(USERNAME, PASSWORD)
#         # Change to the specified remote directory
#         if remote_dir != "/":
#             ftp.cwd(remote_dir)
#         local_full_path = os.path.join(local_dir, filename)
#         if not os.path.exists(local_full_path):
#             message += f"✗ Local file {local_full_path} not found, skipping...\n"
#             return message
#         message += f"Uploading {local_full_path} to {filename}...\n"
#         with open(local_full_path, 'rb') as f:
#             ftp.storbinary(f'STOR {filename}', f)
#         message += f"✓ {filename} uploaded from {local_full_path}\n"
#         ftp.quit()
#     except Exception as e:
#         message += f"Error uploading file: {e}\n"
#     return message  

def upload_afile(localpath, remotepath):
    HOST = "ftp.abvchorus.org"
    USERNAME = "abvch0" 
    PASSWORD = "abeserevelt10"
    message = ""
    try:
        ftp = ftplib.FTP(HOST)
        ftp.login(USERNAME, PASSWORD)
        # Change to the specified remote directory
        remote_dir = os.path.dirname(remotepath)
        filename = os.path.basename(remotepath)
        if remote_dir != "/":
            ftp.cwd(remote_dir)
        if not os.path.exists(localpath):
            message += f"✗ Local file {localpath} not found, skipping...\n"
            return message
        message += f"Uploading {localpath} to {remotepath}...\n"
        with open(localpath, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        message += f"✓ {remotepath} uploaded from {localpath}\n"
        ftp.quit()
    except Exception as e:
        message += f"Error uploading file: {e}\n"
    return message

# def backup_remote_file(directory, filename):
#     message = ""
#     backup_filename = filename.replace('.html', '_backup.html')
#     import ftplib
#     import os
#     HOST = "ftp.abvchorus.org"
#     USERNAME = "abvch0" 
#     PASSWORD = "abeserevelt10"
#     REMOTE_DIR = "public_html/"
#     backup_filename = filename.replace('.html', '_backup.html')
#     try:
#         # Create FTP connection
#         ftp = ftplib.FTP(HOST)
#         ftp.login(USERNAME, PASSWORD)
#         ftp.cwd(REMOTE_DIR)
#         message += f"ftp.cwd(): {ftp.pwd()}\n"
#         ftp.rename(filename, backup_filename)
#         message += f"Successfully renamed '{filename}' to '{backup_filename}'\n"
#         ftp.quit()
#     except ftplib.error_perm as e:
#         message += f"Permission error: {e}\n"
#     except ftplib.error_temp as e:
#         message += f"Temporary error: {e}\n"
#     except Exception as e:
#         message += f"Error: {e}\n"
#     return message

# def backup_html_file(remotepath):
#     message = ""
#     import ftplib
#     import os
#     HOST = "ftp.abvchorus.org"
#     USERNAME = "abvch0" 
#     PASSWORD = "abeserevelt10"
#     remote_dir = os.path.dirname(remotepath)    
#     filename = os.path.basename(remotepath) 
#     backup_filename = filename.replace('.html', '_backup.html')
#     try:    
#         # Create FTP connection
#         ftp = ftplib.FTP(HOST)
#         ftp.login(USERNAME, PASSWORD)
#         if remote_dir != "/":
#             ftp.cwd(remote_dir)
#         message += f"ftp.cwd(): {ftp.pwd()}\n"
#         ftp.rename(filename, backup_filename)
#         message += f"Successfully renamed '{filename}' to '{backup_filename}'\n"
#         ftp.quit()
#     except ftplib.error_perm as e:
#         message += f"Permission error: {e}\n"
#     except ftplib.error_temp as e:
#         message += f"Temporary error: {e}\n"
#     except Exception as e:
#         message += f"Error: {e}\n"
#     return message

def create_remote_backup(original_path, backup_path):

    HOST = "ftp.abvchorus.org"
    USERNAME = "abvch0" 
    PASSWORD = "abeserevelt10"
    message = ""
    try:
        ftp = ftplib.FTP(HOST)
        ftp.login(USERNAME, PASSWORD)
        buffer = io.BytesIO()
        ftp.retrbinary(f"RETR {original_path}", buffer.write)
        buffer.seek(0)
        ftp.storbinary(f"STOR {backup_path}", buffer)
        buffer.close()
        message += f"✅ Copied {original_path} to {backup_path}\n"
        ftp.quit()
        return message
    except Exception as e:
        ftp.quit()
        message += f"❌ Copy failed: {e}\n"     
        return message
    return message

def upload_many_files(files_array):
    message =""
    for fromto_array in files_array:
        localpath = fromto_array[0]
        remotepath = fromto_array[1]
        
        message += upload_afile(localpath, remotepath) 
    return message
                      
def replace_spaces_with_underscores(filename):
    """Replace spaces in filename with underscores"""
    return filename.replace(' ', '_').replace('%20', '_').replace('%27', '_').replace("'", '_') 

def clean_filename(original_filename):
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
    
def copy_clean_and_convert(source_path, 
                           target_directory, keep_original_source=True, 
                           convert_to_pdf=True, remove_copied_doc=True):
    """
    Single function to copy a file to target directory, clean filename, and convert DOC/DOCX to PDF.
    Args:
        source_path (str): Path to the source file
        target_directory (str): Target directory where file will be copied
        keep_original_source (bool): Whether to keep the original source file (default: True = copy, False = move)
        convert_to_pdf (bool): Whether to convert DOC/DOCX files to PDF
        remove_copied_doc (bool): Whether to remove the copied DOC/DOCX after PDF conversion
    Returns:
        dict: Complete information about the operation
    """
    source_path = Path(source_path)
    target_dir = Path(target_directory)
    # Validate source file exists
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    # Clean the filename
    cleaned_name = clean_filename(source_path.name)
    target_path = target_dir / cleaned_name
    # Handle name conflicts
    if target_path.exists():
        base_name = target_path.stem
        extension = target_path.suffix
        counter = 1
        while target_path.exists():
            new_name = f"{base_name}_{counter}{extension}"
            target_path = target_dir / new_name
            counter += 1
    result = {
        'source_path': str(source_path),
        'target_path': str(target_path),
        'cleaned_name': str(cleaned_name),
        'cleaned_path': f"{target_path}",
        'converted': False,
        'operation': 'copy' if keep_original_source else 'move',
        'error': None
    }
    print(f"cleaned_path: {result['cleaned_path']}")
    try:
        # Copy or move the file
        if keep_original_source:
            # Copy the file
            shutil.copy2(str(source_path), str(target_path))
            print(f"Copied: {source_path} -> {target_path}")
        else:
            # Move the file
            shutil.move(str(source_path), str(target_path))
            print(f"Moved: {source_path} -> {target_path}")
        # Check if we should convert to PDF
        if convert_to_pdf and target_path.suffix.lower() in ['.doc', '.docx']:
            try:
                # Create PDF filename
                pdf_path = target_path.with_suffix('.pdf')
                pdf_name = pdf_path.name
                # Convert to PDF
                print(f"Converting {target_path} to PDF...")
                convert(str(target_path), str(pdf_path))
                result['cleaned_path'] = str(pdf_path)
                result['cleaned_name'] = pdf_name
                result['converted'] = True
                print(f"Successfully converted to: {pdf_path}")
                # Optionally remove the copied DOC/DOCX file
                if remove_copied_doc:
                    target_path.unlink()
                    print(f"Removed copied DOC/DOCX file: {target_path}")
                    result['copied_path'] = None  # Indicate it was removed
            except Exception as e:
                result['error'] = f"PDF conversion failed: {str(e)}"
                print(f"Error converting {target_path} to PDF: {e}")
        return result
    except Exception as e:
        result['error'] = f"File operation failed: {str(e)}"
        raise Exception(f"Failed to copy/move file: {e}")   
    
def upload_cleaned_file(source_path, target_dir, link_path):
    result = copy_clean_and_convert(
        source_path=source_path,
        target_directory=target_dir
    )
    result["link_href"] = link_path + result["cleaned_name"]

    local_path = result["cleaned_path"]
    remotedir ="public_html/"
    remote_path = f"{remotedir}{result["link_href"]}"

    message = upload_afile(local_path, remote_path)
    return message, result   