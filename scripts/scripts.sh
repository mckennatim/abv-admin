scp -r /mnt/c/Users/mcken/OneDrive/chorus/abv/tech/process*.* 107.175.134.21:/var/www/html/files/me2/2024


python -m http.server 8000 from git bash ./gitpush.sh


when in tryit and you want to fetch and update to the latest from local
* git fetch origin
* git reset --hard origin/main

tail -f nohup.out


### windows
### git bash
# Quick Git Bash setup for your miniconda path (run once in VS Code Git Bash terminal)
echo "Setting up miniconda for Git Bash in VS Code..."

# Add to bashrc
echo '# Miniconda setup for Git Bash' >> ~/.bashrc
echo 'export PATH="/c/Users/mcken/miniconda3/Scripts:/c/Users/mcken/miniconda3:$PATH"' >> ~/.bashrc
echo '. "/c/Users/mcken/miniconda3/etc/profile.d/conda.sh"' >> ~/.bashrc

# Apply changes
source ~/.bashrc

echo "✅ Setup complete! Now you can use 'conda activate base' in Git Bash"
echo "Test with: conda --version"
#-------------------------------------------------------------------
# Then you can use conda commands
conda activate base  # or your specific environment name
python app.py &

### cmd