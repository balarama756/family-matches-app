// Use PDF.js and Tesseract.js for client-side processing
async function processPDFClientSide(file) {
    // Load PDF.js
    const pdfjsLib = window['pdfjs-dist/build/pdf'];
    
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
    
    const images = [];
    
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        const viewport = page.getViewport({ scale: 2.0 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        await page.render({ canvasContext: context, viewport }).promise;
        
        // Convert to image
        const imageData = canvas.toDataURL('image/png');
        
        // Extract text using Tesseract.js
        const { data: { text } } = await Tesseract.recognize(imageData, 'eng');
        
        images.push({
            image: imageData,
            text: text,
            page: i
        });
    }
    
    return images;
}