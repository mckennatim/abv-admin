# JavaScript Development Guidelines

## For AI Assistants Working on This Project

### 🎯 Primary Directive: Use Modern JavaScript (ES6+)

When writing JavaScript code for this project, always prefer modern syntax patterns:

#### Variables & Scope
```javascript
// ✅ Use const/let with block scope
const apiUrl = '/api/songs';
let currentSong = null;

// ❌ Avoid var
var oldStyle = 'avoid this';
```

#### Functions  
```javascript
// ✅ Arrow functions for callbacks and short functions
const processData = (data) => data.map(item => item.name);

// ✅ Named functions for main logic (better stack traces)
function handleSongUpload(file) { /* main logic */ }
```

#### Strings
```javascript
// ✅ Template literals
const message = `Processing ${filename} in ${directory}`;

// ❌ String concatenation
const message = 'Processing ' + filename + ' in ' + directory;
```

#### Arrays & Objects
```javascript
// ✅ Destructuring and modern methods
const {name, artist} = song;
const directories = paths.map(path => path.split('/')[1]);

// ✅ Object shorthand
const songData = {name, artist, duration};
```

### 🔬 For Jupyter Notebooks
Use IIFE patterns to avoid variable conflicts:

```javascript
// ✅ Named IIFE for complex logic
(function extractResourceDirectories(markdown) {
    const regex = /\]\(resources\/([^)]+)\)/g;
    const results = [...markdown.matchAll(regex)];
    console.log('Found:', results);
    return results;
})(md_text);

// ✅ Arrow IIFE for quick tests
(() => {
    const test = 'quick experiment';
    console.log(test);
})();
```

### 📁 File Locations
- **Main instructions**: `.ai-instructions.md` (this file)
- **JSON config**: `.ai-config.json` 
- **ESLint rules**: `.eslintrc.js`

### 🚫 When NOT to Use Modern Syntax
- Quick experiments and Jupyter notebook exploration
- User explicitly requests older syntax for learning  
- Working with legacy code that needs consistency
- Performance-critical sections where older patterns are faster
- Rapid prototyping where speed matters more than style

### 💡 Project-Specific Context
This is a song management application with:
- Resource directory extraction from markdown
- File upload and processing
- Flask backend integration
- Nginx deployment

Always consider this context when writing code and choosing patterns.