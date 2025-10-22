# Contabulate

A digital humanities project exploring literary works through structured tables and data visualization.

## About

Contabulate transforms literary analysis by presenting classic works in structured, searchable tables. This approach reveals patterns, connections, and insights that traditional reading methods might overlook.

Currently featuring:
- **Shakespeare's Complete Works** - Comprehensive analysis of plays and sonnets

## Live Site

Visit the site at: [https://brainheart.github.io/contabulate](https://brainheart.github.io/contabulate)

## Project Structure

```
contabulate/
├── index.html              # Main landing page
├── css/
│   └── style.css           # Main stylesheet
├── shakespeare/
│   ├── index.html          # Shakespeare collection page
│   ├── shakespeare.css     # Shakespeare-specific styles
│   └── [content files]     # Shakespeare HTML content
├── table-template.html     # Example table implementation
└── README.md              # This file
```

## Features

- **Responsive Design** - Works on desktop and mobile devices
- **Table-Focused Layout** - Optimized for displaying literary data
- **Sortable Tables** - Interactive sorting and filtering
- **Expandable Structure** - Ready for additional literary collections
- **GitHub Pages Ready** - Static site deployment

## Adding Content

### Shakespeare Content
1. Copy your Shakespeare HTML files into the `shakespeare/` directory
2. Update internal links to work with the new structure
3. The existing CSS will automatically style your tables and content
4. Add navigation links to your new content

### Additional Literary Collections
1. Create a new directory for your collection (e.g., `dickens/`, `austen/`)
2. Follow the same structure as the Shakespeare directory
3. Update the main navigation in `index.html`
4. Create collection-specific CSS if needed

## Development

This is a static HTML site designed for GitHub Pages deployment. No build process is required.

### Local Development
Simply open `index.html` in a web browser or serve the files with a local web server:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js
npx serve .
```

### Deployment
The site is configured for automatic deployment to GitHub Pages from the main branch.

## Technologies Used

- HTML5
- CSS3 (with Grid and Flexbox)
- Vanilla JavaScript (for table interactions)
- GitHub Pages (for hosting)

## Contributing

This project is designed to be easily extensible for additional literary collections and analysis tools.

## License

MIT License - see the repository for details.