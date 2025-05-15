// This script generates placeholder SVG images for the Star College logos
// Run this script in a browser console or with Node.js

function generateSVGLogo(type, color, text) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
        <polygon points="100,10 40,50 40,150 100,190 160,150 160,50" fill="#0a3d62" stroke="#fff" stroke-width="5"/>
        <polygon points="100,30 60,60 60,140 100,170 140,140 140,60" fill="#e74c3c" stroke="#fff" stroke-width="3"/>
        <rect x="50" y="100" width="100" height="30" fill="${color}" stroke="#fff" stroke-width="2"/>
        <text x="100" y="120" font-family="Arial" font-size="${text.length > 10 ? 14 : 16}" font-weight="bold" text-anchor="middle" fill="#fff">${text}</text>
        <text x="100" y="50" font-family="Arial" font-size="12" font-weight="bold" text-anchor="middle" fill="#fff">STAR COLLEGE</text>
    </svg>`;
    
    // Convert SVG to data URL
    const dataURL = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    
    console.log(`Generated ${type} logo with color ${color}`);
    return dataURL;
}

// Generate logos
const logos = [
    { type: 'boys_high', color: '#3498db', text: 'BOYS HIGH' },
    { type: 'girls_high', color: '#e84393', text: 'GIRLS HIGH' },
    { type: 'primary', color: '#27ae60', text: 'PRIMARY' },
    { type: 'pre_primary', color: '#e67e22', text: 'PRE-PRIMARY' },
    { type: 'default', color: '#3498db', text: 'DURBAN' }
];

// In a browser environment, this would create download links
// In Node.js, you would save these to files
logos.forEach(logo => {
    const dataURL = generateSVGLogo(logo.type, logo.color, logo.text);
    console.log(`${logo.type}_logo.png: ${dataURL.substring(0, 50)}...`);
    
    // In a browser, you could create a download link:
    // const link = document.createElement('a');
    // link.href = dataURL;
    // link.download = `${logo.type}_logo.png`;
    // link.click();
});

console.log('Generated all placeholder logos. Use the placeholder.html file to save them to your images folder.');
