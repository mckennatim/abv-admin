// ABV Song Management System - Frontend JavaScript with ABVFileUploader Integration

// ABVFileUploader Class - Service for handling file uploads with batch link generation
class ABVFileUploader {
    constructor(songManager) {
        this.songManager = songManager; // Reference to SongManager
        this.fileInput = document.getElementById('fileInput');
        this.uploadedFiles = []; // Track for sync-back
        this.pendingLinks = []; // Collect files for batch linking
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // ✅ Use 'change' event instead of 'click'
        this.fileInput.addEventListener('change', (event) => {
            this.handleFileSelection(event);
        });
    }
    
    handleFileSelection(event) {
        const files = event.target.files;
        
        if (files.length > 0) {
            console.log(`📁 ${files.length} files selected`);
            
            // Get current song FROM SongManager
            const currentSong = this.songManager.getCurrentSong();
            
            if (!currentSong) {
                alert('Please select a song first');
                return;
            }
            
            // Get folder info at upload time, not selection time
            const customFolder = this.songManager.getSelectedFolder();
            
            // Process and upload files
            this.processAndUploadFiles(files, currentSong.dir, customFolder);
        }
    }
    
    cleanFileName(originalName) {
        // Clean filename while preserving extension - with duplicate underscore removal
        if (originalName.includes('.')) {
            const lastDotIndex = originalName.lastIndexOf('.');
            const name = originalName.substring(0, lastDotIndex);
            const ext = originalName.substring(lastDotIndex);
            
            const cleanedName = name
                .replace(/[^a-zA-Z0-9]/g, '_')  // Replace non-alphanumeric with underscores
                .replace(/^_+|_+$/g, '')        // Remove leading/trailing underscores
                .replace(/_+/g, '_');           // Replace multiple underscores with single
            
            return cleanedName + ext;
        } else {
            // No extension, clean the whole filename
            return originalName
                .replace(/[^a-zA-Z0-9]/g, '_')
                .replace(/^_+|_+$/g, '')
                .replace(/_+/g, '_');
        }
    }
    
    generateFilePath(songDir, customFolder, fileName) {
        const cleanedName = this.cleanFileName(fileName);
        
        // Check if file will be converted (.docx to PDF)
        const isDocx = fileName.toLowerCase().endsWith('.docx');
        const finalName = isDocx ? cleanedName.replace(/\.docx$/i, '.pdf') : cleanedName;
        
        // If customFolder contains a full path (like "audio/zzTest"), use it as-is
        // If it's just a simple folder name (like "audio"), combine with songDir
        if (customFolder && customFolder.includes('/')) {
            // Full path provided (e.g., "audio/zzTest")
            return `resources/${customFolder}/${finalName}`;
        } else {
            // Simple folder name (e.g., "audio") - combine with song directory
            const folder = customFolder || 'general';
            return `resources/${songDir}/${folder}/${finalName}`;
        }
    }
    
    async processAndUploadFiles(files, songDir, customFolder) {
        // Show upload progress in SongManager UI
        this.songManager.showUploadProgress(true);
        this.pendingLinks = []; // Clear pending links
        
        console.log(`🚀 Batch processing ${files.length} files...`);
        
        // Upload all files first (no individual prompts)
        for (const file of files) {
            try {
                const fileData = {
                    originalName: file.name,
                    cleanedName: this.cleanFileName(file.name),
                    fullPath: this.generateFilePath(songDir, customFolder, file.name),
                    size: file.size,
                    type: file.type
                };
                
                console.log(`📁 Uploading: ${fileData.originalName}`);
                
                // Upload to server
                await this.uploadFileToServer(file, fileData);
                
                // Track for sync-back
                this.trackUploadedFile(fileData.fullPath);
                
                // ADD TO PENDING LINKS (instead of individual prompt)
                this.pendingLinks.push(fileData);
                
                // NOTIFY SongManager of upload (for tracking)
                this.songManager.onFileUploaded(fileData);
                
                console.log(`✅ Uploaded: ${fileData.cleanedName}`);
                
            } catch (error) {
                console.error(`❌ Error processing ${file.name}:`, error);
                this.songManager.showUploadError(file.name, error.message);
            }
        }
        
        this.songManager.showUploadProgress(false);
        
        // BATCH LINK GENERATION: Show all files at once
        if (this.pendingLinks.length > 0) {
            this.songManager.promptForBatchMarkdownLinks(this.pendingLinks);
        }
        
        // Clear file input
        this.fileInput.value = '';
    }
    
    async uploadFileToServer(file, fileData) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('cleanedName', fileData.cleanedName);
        formData.append('fullPath', fileData.fullPath);
        formData.append('originalName', fileData.originalName);
        formData.append('folder', fileData.fullPath.split('/').slice(0, -1).join('/'));
        
        // Check if this file will be converted
        const isDocx = file.name.toLowerCase().endsWith('.docx');
        if (isDocx) {
            console.log('📄 .docx file detected - server will convert to PDF');
        }
        
        const response = await fetch(`${this.songManager.API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Handle conversion response
        if (result.converted) {
            console.log(`🔄 File converted: ${result.original_filename} → ${result.filename}`);
            console.log(`📂 Stored as: ${result.path}`);
            
            // Update fileData with converted info
            fileData.cleanedName = result.filename;
            fileData.fullPath = result.path;
            fileData.wasConverted = true;
            fileData.conversionType = result.conversion_type;
            fileData.conversionMessage = result.message;
        }
        
        console.log('✅ Upload successful:', result);
        return result;
    }
    
    trackUploadedFile(filePath) {
        if (!this.uploadedFiles.includes(filePath)) {
            this.uploadedFiles.push(filePath);
            console.log(`📋 Tracked for sync: ${filePath}`);
        }
    }
    
    getFilesForSyncBack() {
        return [...this.uploadedFiles];
    }
    
    clearSyncList() {
        this.uploadedFiles = [];
        console.log('🧹 ABVFileUploader sync list cleared');
    }
}

// Enhanced SongManager Class with ABVFileUploader Integration
class SongManager {
    constructor() {
        this.songs = [];
        this.currentSong = null;
        this.selectedSongId = null;
        
        // Extract the base path from current location
        const currentPath = window.location.pathname;
        const basePath = currentPath.replace(/\/app\/?$/, ''); // Remove /app from end
        
        // Check if we're on localhost development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Development: API on port 8001, static files on port 8000
            this.API_BASE = 'http://127.0.0.1:8001';
        } else {
            // Production: API on same server as static files  
            this.API_BASE = window.location.origin + basePath;
        }
        
        console.log('SongManager initialized');
        console.log('Current origin:', window.location.origin);
        console.log('Current pathname:', window.location.pathname);
        console.log('Calculated API_BASE:', this.API_BASE);
        
        this.initializeElements();
        
        // Initialize file uploader AFTER elements are initialized
        this.fileUploader = new ABVFileUploader(this);
        this.syncBackFiles = []; // Track files for sync-back
        
        this.attachEventListeners();
        this.testAPI();
        this.loadSongs();
        
        // Initialize pending files counter
        this.updatePendingFilesCounter();
    }

    async testAPI() {
        try {
            console.log('Testing API connection...');
            const response = await fetch(`${this.API_BASE}/api/`);
            console.log('API test response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('API test data:', data);
                this.setStatus('API connection successful');
            } else {
                console.log('API test failed with status:', response.status);
                this.setStatus('API connection failed', 'error');
            }
        } catch (error) {
            console.error('API test error:', error);
            this.setStatus('API connection error: ' + error.message, 'error');
        }
    }

    initializeElements() {
        // Main elements
        this.songList = document.getElementById('songList');
        this.editorPanel = document.getElementById('editorPanel');
        this.searchInput = document.getElementById('searchInput');
        
        // Editor elements
        this.songNameInput = document.getElementById('songNameInput');
        this.currentSelect = document.getElementById('currentSelect');
        this.markdownEditor = document.getElementById('markdownEditor');
        this.markdownPreview = document.getElementById('markdownPreview');
        
        // Upload elements
        this.fileInput = document.getElementById('fileInput');
        this.folderSelect = document.getElementById('folderSelect');
        this.customFolder = document.getElementById('customFolder');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.uploadStatus = document.getElementById('uploadStatus');
        
        // Batch link modal elements
        this.batchLinkModal = document.getElementById('batchLinkModal');
        this.batchFileList = document.getElementById('batchFileList');
        this.generateAllLinksBtn = document.getElementById('generateAllLinksBtn');
        this.cancelBatchLinksBtn = document.getElementById('cancelBatchLinksBtn');
        this.modalCloseBtn = document.getElementById('modalCloseBtn');
        
        // Buttons
        this.saveBtn = document.getElementById('saveBtn');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.syncBtn = document.getElementById('syncBtn');
        this.syncBackBtn = document.getElementById('syncBackBtn');
        this.newSongBtn = document.getElementById('newSongBtn');
        this.deleteSongBtn = document.getElementById('deleteSongBtn');
        this.pendingFilesCounter = document.getElementById('pendingFiles');
        
        // Track uploaded files for sync back
        this.uploadedFilesSinceSync = new Set();
        
        // Make this available globally for debugging
        window.songManager = this;
        
        // Status
        this.status = document.getElementById('status');
    }

    attachEventListeners() {
        // Search functionality
        this.searchInput.addEventListener('input', (e) => {
            this.filterSongs(e.target.value);
        });

        // Editor functionality
        this.markdownEditor.addEventListener('input', (e) => {
            this.updatePreview(e.target.value);
            // Update folder select when markdown changes
            this.populateFolderSelect();
        });
        
        // Handle folder selection from dropdown
        this.folderSelect.addEventListener('change', () => {
            if (this.folderSelect.value) {
                this.customFolder.value = this.folderSelect.value;
            }
        });
        
        // Batch link modal event listeners
        this.generateAllLinksBtn.addEventListener('click', () => this.generateSelectedLinks());
        this.cancelBatchLinksBtn.addEventListener('click', () => this.hideBatchLinkModal());
        this.modalCloseBtn.addEventListener('click', () => this.hideBatchLinkModal());
        
        // Close modal on outside click
        this.batchLinkModal.addEventListener('click', (e) => {
            if (e.target === this.batchLinkModal) {
                this.hideBatchLinkModal();
            }
        });

        // Save and Cancel
        this.saveBtn.addEventListener('click', () => {
            this.saveSong();
        });

        this.cancelBtn.addEventListener('click', () => {
            this.cancelEdit();
        });

        // Sync button
        this.syncBtn.addEventListener('click', () => {
            this.syncWithLegacy();
        });

        // Sync Back to Legacy button
        this.syncBackBtn.addEventListener('click', () => {
            this.syncBackToLegacy();
        });

        this.currentSelect.addEventListener('change', () => {
            this.saveSong();
        });

        // New song button
        this.newSongBtn.addEventListener('click', () => {
            this.createNewSong();
        });

        // Delete song button
        this.deleteSongBtn.addEventListener('click', () => {
            this.deleteSong();
        });
    }
    
    // NEW METHODS FOR FILE UPLOAD INTEGRATION
    
    getCurrentSong() {
        // Return current song data that ABVFileUploader needs
        return this.currentSong || null;
    }
    
    getSelectedFolder() {
        // Get the selected folder from UI
        const customFolderValue = this.customFolder?.value?.trim();
        
        if (customFolderValue) {
            // If custom folder is provided, use it
            if (customFolderValue.startsWith('resources/')) {
                // Remove 'resources/' prefix and trailing slash
                return customFolderValue.replace('resources/', '').replace(/\/$/, '');
            } else {
                // Add to current song directory
                return customFolderValue.replace(/\/$/, '');
            }
        }
        
        // Default to audio folder
        return 'audio';
    }
    
    onFileUploaded(fileData) {
        // Called by ABVFileUploader when a file is successfully uploaded
        console.log(`📁 File uploaded: ${fileData.cleanedName}`);
        
        // Add to sync-back tracking
        this.addToSyncBackList(fileData.fullPath);
    }
    
    addToSyncBackList(filePath) {
        if (!this.syncBackFiles.includes(filePath)) {
            this.syncBackFiles.push(filePath);
            console.log(`📋 Added to sync-back list: ${filePath}`);
        }
        
        // Also add to the main tracking set
        this.uploadedFilesSinceSync.add(filePath);
        this.updatePendingFilesCounter();
    }
    
    promptForBatchMarkdownLinks(uploadedFiles) {
        console.log(`🔗 Prompting for batch links: ${uploadedFiles.length} files`);
        this.showBatchLinkModal(uploadedFiles);
    }
    
    showBatchLinkModal(uploadedFiles) {
        console.log('📋 Showing batch link dialog');
        
        // Generate HTML for file list
        this.batchFileList.innerHTML = uploadedFiles.map((file, index) => {
            const defaultLinkText = file.cleanedName
                .replace(/\.[^.]+$/, '') // Remove extension
                .replace(/_/g, ' ') // Replace underscores with spaces
                .replace(/\b\w/g, l => l.toUpperCase()); // Capitalize words
            
            // Show conversion info if file was converted
            const conversionInfo = file.wasConverted ? 
                `<div class="conversion-info">🔄 Converted from .docx to PDF</div>` : '';
            
            return `
                <div class="batch-file-item" data-index="${index}">
                    <div class="file-checkbox">
                        <label>
                            <input type="checkbox" checked data-index="${index}">
                            <strong>${file.cleanedName}</strong>
                        </label>
                        ${file.wasConverted ? '<span class="converted-badge">📄→📕</span>' : ''}
                    </div>
                    <div class="file-link-input">
                        <label>Link text:</label>
                        <input type="text" value="${defaultLinkText}" data-index="${index}" class="link-text-input">
                    </div>
                    <div class="file-path">${file.fullPath}</div>
                    ${conversionInfo}
                </div>
            `;
        }).join('');
        
        // Store files for later use
        this.currentBatchFiles = uploadedFiles;
        
        // Show modal
        this.batchLinkModal.style.display = 'block';
        
        // Focus first link text input
        const firstInput = this.batchFileList.querySelector('.link-text-input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
    
    hideBatchLinkModal() {
        this.batchLinkModal.style.display = 'none';
        this.currentBatchFiles = null;
    }
    
    generateSelectedLinks() {
        if (!this.currentBatchFiles) return;
        
        const selectedFiles = [];
        
        // Get selected files and their custom link text
        this.currentBatchFiles.forEach((file, index) => {
            const checkbox = this.batchFileList.querySelector(`input[type="checkbox"][data-index="${index}"]`);
            const textInput = this.batchFileList.querySelector(`input[type="text"][data-index="${index}"]`);
            
            if (checkbox && checkbox.checked) {
                selectedFiles.push({
                    ...file,
                    linkText: textInput.value || file.cleanedName.replace(/\.[^.]+$/, '')
                });
            }
        });
        
        if (selectedFiles.length === 0) {
            alert('Please select at least one file to create links');
            return;
        }
        
        // Generate markdown links
        const markdownLinks = selectedFiles.map(file => 
            `    - [${file.linkText}](${file.fullPath})`
        );
        
        // Insert into song markdown
        this.insertBatchMarkdownLinks(markdownLinks);
        
        // Close modal
        this.hideBatchLinkModal();
        
        // Show success message
        this.showUploadStatus(`Generated ${markdownLinks.length} markdown links successfully!`, 'success');
    }
    
    insertBatchMarkdownLinks(markdownLinks) {
        const textarea = this.markdownEditor;
        
        if (textarea && this.currentSong) {
            const cursorPos = textarea.selectionStart;
            const currentText = textarea.value;
            
            // Join all links with newlines
            const allLinks = markdownLinks.join('\n');
            
            // Add proper spacing
            const prefix = (currentText.slice(0, cursorPos) && !currentText.slice(0, cursorPos).endsWith('\n')) ? '\n' : '';
            const suffix = '\n';
            
            // Insert at cursor position
            const newText = currentText.slice(0, cursorPos) + 
                           prefix + allLinks + suffix + 
                           currentText.slice(cursorPos);
            
            textarea.value = newText;
            this.currentSong.md_text = newText;
            
            // Update preview
            this.updatePreview(newText);
            
            console.log(`📝 Inserted ${markdownLinks.length} links into song markdown`);
        }
    }
    
    showUploadProgress(show) {
        // Show/hide upload progress indicator
        if (this.uploadProgress) {
            this.uploadProgress.style.display = show ? 'block' : 'none';
        }
    }
    
    showUploadError(fileName, errorMessage) {
        // Display upload error to user
        this.showUploadStatus(`Upload failed for "${fileName}": ${errorMessage}`, 'error');
    }

    getResourcePathsWithPrefix = (text) => {
        let dirSet = new Set();
        let regex = /\]\(resources\/([^)]+)\)/g;
        let match;
        
        while ((match = regex.exec(text)) !== null) {
            let filePath = match[1];
            let lastSlash = filePath.lastIndexOf('/');
            if (lastSlash > 0) {
                let directoryPath = filePath.substring(0, lastSlash);
                dirSet.add('resources/' + directoryPath + '/');
            }
        }
        return Array.from(dirSet);
    }

    async loadSongs() {
        try {
            this.setStatus('Loading songs...');
            console.log('API_BASE:', this.API_BASE);
            console.log('Fetching from:', `${this.API_BASE}/api/songs`);
            
            const response = await fetch(`${this.API_BASE}/api/songs`);
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received data:', data);
            
            this.songs = data;
            this.renderSongList();
            this.setStatus(`Loaded ${this.songs.length} songs`);
        } catch (error) {
            console.error('Error loading songs:', error);
            this.setStatus('Error loading songs: ' + error.message, 'error');
            this.songList.innerHTML = '<div class="error">Failed to load songs: ' + error.message + '</div>';
        }
    }

    renderSongList(filteredSongs = null) {
        const songsToRender = filteredSongs || this.songs;
        
        if (songsToRender.length === 0) {
            this.songList.innerHTML = '<div class="loading">No songs found</div>';
            return;
        }

        this.songList.innerHTML = songsToRender.map(song => `
            <div class="song-item" data-id="${song.rowid}" onclick="songManager.selectSong(${song.rowid})">
                <div class="song-name">
                    ${this.escapeHtml(song.song_name)}
                    ${song.current ? '<span class="current-badge">Current</span>' : ''}
                </div>
                <div class="song-dir">${song.dir || 'No directory'}</div>
            </div>
        `).join('');
    }

    filterSongs(searchTerm) {
        if (!searchTerm.trim()) {
            this.renderSongList();
            return;
        }

        const filtered = this.songs.filter(song => 
            song.song_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (song.dir && song.dir.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        
        this.renderSongList(filtered);
    }

    async selectSong(songId) {
        try {
            // Update visual selection
            document.querySelectorAll('.song-item').forEach(item => {
                item.classList.remove('selected');
            });
            document.querySelector(`[data-id="${songId}"]`).classList.add('selected');

            this.setStatus('Loading song details...');
            console.log('Fetching song details from:', `${this.API_BASE}/api/songs/${songId}`);
            const response = await fetch(`${this.API_BASE}/api/songs/${songId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.currentSong = await response.json();
            this.selectedSongId = songId;
            this.populateEditor();
            this.showEditor();
            
            // Enable delete button when song is selected
            this.deleteSongBtn.disabled = false;
            
            this.setStatus(`Editing: ${this.currentSong.song_name}`);
        } catch (error) {
            console.error('Error loading song:', error);
            this.setStatus('Error loading song: ' + error.message, 'error');
        }
    }

    populateEditor() {
        if (!this.currentSong) return;
        
        this.songNameInput.value = this.currentSong.song_name || '';
        this.currentSelect.value = this.currentSong.current || 0;
        this.markdownEditor.value = this.currentSong.md_text || '';
        this.updatePreview(this.currentSong.md_text || '');
        
        // Set default custom folder based on current song
        if (this.currentSong.dir) {
            this.customFolder.value = `resources/audio/${this.currentSong.dir}/`;
        }
        
        // Populate folder select with resource paths from current song
        this.populateFolderSelect();
    }

    populateFolderSelect() {
        // Get current markdown text
        const markdownText = this.markdownEditor.value || '';
        
        // Extract resource paths using the existing function
        const resourcePaths = this.getResourcePathsWithPrefix(markdownText);
        
        // Clear existing options except the first one
        this.folderSelect.innerHTML = '<option value="">-- Select or use custom below --</option>';
        
        // Add detected resource paths as options
        resourcePaths.forEach(path => {
            if (path) {
                const option = document.createElement('option');
                option.value = path;
                option.textContent = path;
                this.folderSelect.appendChild(option);
            }
        });
        
        // Update help text
        const helpText = document.getElementById('folderHelp');
        if (helpText) {
            const detectedCount = resourcePaths.length;
            if (detectedCount > 0) {
                helpText.textContent = `Found ${detectedCount} directory(ies) in current song. Select from dropdown or type custom path.`;
            } else {
                helpText.textContent = 'No directories detected. Type custom directory path below.';
            }
        }
    }

    updatePreview(markdown) {
        try {
            const html = marked.parse(markdown);
            this.markdownPreview.innerHTML = html;
        } catch (error) {
            this.markdownPreview.innerHTML = '<p style="color: red;">Error rendering markdown: ' + error.message + '</p>';
        }
    }
    
    updatePendingFilesCounter() {
        const count = this.uploadedFilesSinceSync.size;
        console.log('updatePendingFilesCounter called:', count, 'files pending');
        
        this.pendingFilesCounter.textContent = `${count} file${count !== 1 ? 's' : ''} pending`;
        
        if (count > 0) {
            this.pendingFilesCounter.classList.add('has-files');
        } else {
            this.pendingFilesCounter.classList.remove('has-files');
        }
        
        // Sync back button is always enabled now
        this.syncBackBtn.disabled = false;
    }
    
    async syncBackToLegacy() {
        try {
            this.syncBackBtn.disabled = true;
            this.syncBackBtn.textContent = 'Syncing...';
            
            // Get pending files (could be empty array)
            const allFiles = [
                ...Array.from(this.uploadedFilesSinceSync),
                ...this.fileUploader.getFilesForSyncBack()
            ];
            const uniqueFiles = [...new Set(allFiles)];
            
            console.log(`Sync back request with ${uniqueFiles.length} files:`, uniqueFiles);
            
            const response = await fetch(`${this.API_BASE}/api/sync-back`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    files: uniqueFiles  // Backend always regenerates HTML regardless
                })
            });
            
            if (!response.ok) {
                throw new Error(`Sync back failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Clear pending files only if there were files to process
            if (uniqueFiles.length > 0) {
                this.uploadedFilesSinceSync.clear();
                this.fileUploader.clearSyncList();
                this.updatePendingFilesCounter();
            }
            
            this.setStatus(result.message || 'Sync operation completed successfully!', 'success');
            
        } catch (error) {
            console.error('Sync back error:', error);
            this.setStatus(`Sync back failed: ${error.message}`, 'error');
        } finally {
            this.syncBackBtn.disabled = false;
            this.syncBackBtn.textContent = 'Sync Back to Legacy';
        }
    }

    showEditor() {
        this.editorPanel.style.display = 'block';
    }

    hideEditor() {
        this.editorPanel.style.display = 'none';
        this.currentSong = null;
        this.selectedSongId = null;
        
        // Disable delete button when no song selected
        this.deleteSongBtn.disabled = true;
        
        // Clear selection
        document.querySelectorAll('.song-item').forEach(item => {
            item.classList.remove('selected');
        });
    }

    showUploadStatus(message, type) {
        this.uploadStatus.textContent = message;
        this.uploadStatus.className = type === 'error' ? 'upload-error' : 'upload-success';
        this.uploadStatus.style.display = 'block';
        
        setTimeout(() => {
            this.uploadStatus.style.display = 'none';
        }, 5000);
    }

    async saveSong() {
        if (!this.currentSong || !this.selectedSongId) {
            this.setStatus('No song selected to save', 'error');
            return;
        }

        try {
            this.saveBtn.disabled = true;
            this.saveBtn.textContent = 'Saving...';
            
            const updatedSong = {
                song_name: this.songNameInput.value,
                md_text: this.markdownEditor.value,
                dir: this.currentSong.dir, // Keep existing dir for now
                current: parseInt(this.currentSelect.value),
                season: this.currentSong.season
            };

            const response = await fetch(`${this.API_BASE}/api/songs/${this.selectedSongId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedSong)
            });

            if (!response.ok) {
                throw new Error(`Save failed: ${response.statusText}`);
            }

            // Update local data
            this.currentSong = { ...this.currentSong, ...updatedSong };
            const songIndex = this.songs.findIndex(s => s.rowid === this.selectedSongId);
            if (songIndex !== -1) {
                this.songs[songIndex] = { ...this.songs[songIndex], ...updatedSong };
            }

            this.renderSongList();
            this.setStatus('Song saved successfully!');
            
        } catch (error) {
            console.error('Save error:', error);
            this.setStatus('Save failed: ' + error.message, 'error');
        } finally {
            this.saveBtn.disabled = false;
            this.saveBtn.textContent = 'Save Song';
        }
    }

    cancelEdit() {
        if (this.currentSong) {
            this.populateEditor(); // Reset to original values
        }
        this.hideEditor();
        this.setStatus('Edit cancelled');
    }

    async syncWithLegacy() {
        try {
            this.syncBtn.disabled = true;
            this.syncBtn.textContent = 'Syncing...';
            this.setStatus('Syncing with legacy site...');

            const response = await fetch(`${this.API_BASE}/api/sync`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Sync failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.setStatus('Sync completed successfully!');
            
            // Reload songs after sync
            await this.loadSongs();
            
        } catch (error) {
            console.error('Sync error:', error);
            this.setStatus('Sync failed: ' + error.message, 'error');
        } finally {
            this.syncBtn.disabled = false;
            this.syncBtn.textContent = 'Sync with Legacy Site';
        }
    }

    insertAtCursor(textArea, text) {
        const start = textArea.selectionStart;
        const end = textArea.selectionEnd;
        const value = textArea.value;
        
        textArea.value = value.substring(0, start) + text + value.substring(end);
        textArea.selectionStart = textArea.selectionEnd = start + text.length;
        textArea.focus();
    }

    setStatus(message, type = 'info') {
        this.status.textContent = message;
        this.status.style.color = type === 'error' ? '#e74c3c' : '#7f8c8d';
    }

    async createNewSong() {
        const songName = prompt('Enter new song name:');
        
        if (!songName || !songName.trim()) {
            this.setStatus('Song name is required', 'error');
            return;
        }
        
        const cleanSongName = songName.trim();
        
        // Generate directory name from song name (filesystem-safe)
        const dirName = this.generateDirectoryName(cleanSongName);
        
        try {
            this.newSongBtn.disabled = true;
            this.newSongBtn.textContent = 'Creating...';
            this.setStatus('Creating new song...');
            
            // Create new song data with proper dir field
            const newSongData = {
                song_name: cleanSongName,  // Original user input (can have special chars)
                dir: dirName,              // Generated directory-safe name
                md_text: `- ${cleanSongName}\n  - [Sheet music](resources/print/)\n  - Audio files\n    - [SATB](resources/audio/${dirName}/)\n`,
                current: 0,
                season: null
            };
            
            console.log('Creating song with data:', newSongData);
            
            const response = await fetch(`${this.API_BASE}/api/songs`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newSongData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to create song: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Reload songs list and select the new song
            await this.loadSongs();
            this.selectSong(result.song_id);
            
            this.setStatus(`New song "${cleanSongName}" created successfully! Directory: ${dirName}`);
            
        } catch (error) {
            console.error('Error creating new song:', error);
            this.setStatus('Failed to create new song: ' + error.message, 'error');
        } finally {
            this.newSongBtn.disabled = false;
            this.newSongBtn.textContent = '➕ New Song';
        }
    }

    async deleteSong() {
        if (!this.currentSong || !this.selectedSongId) {
            this.setStatus('No song selected to delete', 'error');
            return;
        }
        
        const songName = this.currentSong.song_name;
        
        // Confirmation dialog
        const confirmDelete = confirm(
            `Are you sure you want to delete "${songName}"?\n\n` +
            `This will permanently remove the song from the database.\n` +
            `Files and resources will NOT be deleted.`
        );
        
        if (!confirmDelete) {
            return;
        }
        
        try {
            this.deleteSongBtn.disabled = true;
            this.deleteSongBtn.textContent = '🗑️ Deleting...';
            this.setStatus('Deleting song...');
            
            const response = await fetch(`${this.API_BASE}/api/songs/${this.selectedSongId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to delete song: ${response.statusText}`);
            }
            
            // Remove from local songs array
            this.songs = this.songs.filter(song => song.rowid !== this.selectedSongId);
            
            // Hide editor and refresh song list
            this.hideEditor();
            this.renderSongList();
            
            this.setStatus(`Song "${songName}" deleted successfully`);
            
        } catch (error) {
            console.error('Error deleting song:', error);
            this.setStatus('Failed to delete song: ' + error.message, 'error');
        } finally {
            this.deleteSongBtn.disabled = false;
            this.deleteSongBtn.textContent = '🗑️ Delete Song';
        }
    }

    // Enhanced directory name generation function
    generateDirectoryName(songName) {
        return songName
            .toLowerCase()                    // Convert to lowercase
            .trim()                          // Remove leading/trailing spaces
            .replace(/[^a-z0-9]+/g, '_')     // Replace non-alphanumeric with underscores
            .replace(/^_+|_+$/g, '')         // Remove leading/trailing underscores
            .replace(/_+/g, '_');            // Replace multiple underscores with single
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.songManager = new SongManager();
});