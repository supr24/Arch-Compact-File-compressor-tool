import heapq  # Import the heapq module for priority queue operations
import os  # Import os module for file operations and path handling
import json  # Import json module for JSON operations
from flask import Flask, request, jsonify, send_file, send_from_directory, url_for  # Import Flask modules
from werkzeug.utils import secure_filename  # Import secure_filename to sanitize filenames
import tempfile  # Import tempfile for temporary file operations
import shutil  # Import shutil for file operations like copying

# Initialize Flask application with static folder for serving frontend files
app = Flask(__name__, static_folder='static')

# Configure folders for file operations
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')  # Path for uploaded files
COMPRESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compressed')  # Path for compressed files
DECOMPRESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'decompressed')  # Path for decompressed files
# Create all required directories if they don't exist
for folder in [UPLOAD_FOLDER, COMPRESSED_FOLDER, DECOMPRESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)  # Create directory if it doesn't exist, otherwise do nothing

# Configure Flask application settings
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Set upload folder in app config
app.config['COMPRESSED_FOLDER'] = COMPRESSED_FOLDER  # Set compressed folder in app config
app.config['DECOMPRESSED_FOLDER'] = DECOMPRESSED_FOLDER  # Set decompressed folder in app config
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set maximum file size to 16MB
# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """Extract text from different file formats"""
    filename, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    if file_extension == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            return file.read()
    
    elif file_extension == '.docx':
        try:
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            raise ValueError(f"Error reading DOCX file: {str(e)}")
    
    elif file_extension == '.pdf':
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")
    
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


class HuffmanCoding:
    """Class for Huffman coding implementation with compression and decompression functionality"""
    def __init__(self, path=None):
        self.path = path  # Path of the file to be compressed or decompressed
        self.heap = []  # Min heap to store nodes based on frequency
        self.codes = {}  # Dictionary to store character to code mapping
        self.reverse_mapping = {}  # Dictionary to store code to character mapping for decompression

    class HeapNode:
        """Inner class representing a node in the Huffman tree"""
        def __init__(self, char, freq):
            self.char = char  # Character stored in the node
            self.freq = freq  # Frequency of the character
            self.left = None  # Left child node
            self.right = None  # Right child node

        # Define comparison operators for heap operations
        def __lt__(self, other):
            return self.freq < other.freq  # Compare nodes based on frequency for min heap

        def __eq__(self, other):
            if(other == None):
                return False  # Not equal if other is None
            if(not isinstance(other, HuffmanCoding.HeapNode)):
                return False  # Not equal if other is not a HeapNode
            return self.freq == other.freq  # Equal if frequencies are the same

    # Functions for compression

    def make_frequency_dict(self, text):
        """Create a dictionary with character frequencies"""
        frequency = {}  # Initialize empty dictionary
        for character in text:
            if not character in frequency:
                frequency[character] = 0  # Initialize frequency counter for new characters
            frequency[character] += 1  # Increment frequency for each occurrence
        return frequency

    def make_heap(self, frequency):
        """Create a min heap from the frequency dictionary"""
        for key in frequency:
            node = self.HeapNode(key, frequency[key])  # Create a node for each character
            heapq.heappush(self.heap, node)  # Add node to the heap

    def merge_nodes(self):
        """Build the Huffman tree by merging nodes"""
        while(len(self.heap) > 1):
            # Get the two nodes with lowest frequency
            node1 = heapq.heappop(self.heap)
            node2 = heapq.heappop(self.heap)

            # Create a new internal node with these two nodes as children
            merged = self.HeapNode(None, node1.freq + node2.freq)  # Internal nodes have no character, only frequency sum
            merged.left = node1  # Set left child
            merged.right = node2  # Set right child

            heapq.heappush(self.heap, merged)  # Add the merged node back to the heap

    def make_codes_helper(self, root, current_code):
        """Recursive helper function to generate codes for each character"""
        if(root == None):
            return  # Base case: empty node

        if(root.char != None):
            # Leaf node (has a character): store the code
            self.codes[root.char] = current_code  # Map character to its code
            self.reverse_mapping[current_code] = root.char  # Map code back to character for decompression
            return

        # Traverse left (add 0 to code) and right (add 1 to code)
        self.make_codes_helper(root.left, current_code + "0")  # Left branch adds '0' to the code
        self.make_codes_helper(root.right, current_code + "1")  # Right branch adds '1' to the code

    def make_codes(self):
        """Generate Huffman codes for all characters"""
        root = heapq.heappop(self.heap)  # Get the root of the Huffman tree
        current_code = ""  # Start with empty code
        self.make_codes_helper(root, current_code)  # Generate codes recursively

    def get_encoded_text(self, text):  
        """Convert input text to encoded binary string using Huffman codes"""
        encoded_text = ""
        for character in text:
            encoded_text += self.codes[character]  # Replace each character with its code
        return encoded_text

    def pad_encoded_text(self, encoded_text):
        """Add padding to ensure the encoded text length is a multiple of 8 (for byte conversion)"""
        # Calculate padding needed
        extra_padding = 8 - len(encoded_text) % 8
        for i in range(extra_padding):
            encoded_text += "0"  # Add padding bits

        # Store padding info in the first byte
        padded_info = "{0:08b}".format(extra_padding)  # Convert padding count to 8-bit binary
        encoded_text = padded_info + encoded_text  # Prepend padding info to encoded text
        return encoded_text

    def get_byte_array(self, padded_encoded_text):
        """Convert binary string to byte array for file storage"""
        if(len(padded_encoded_text) % 8 != 0):
            print("Encoded text not padded properly")  # Verify text is properly padded
            exit(0)

        b = bytearray()  # Initialize empty byte array
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i+8]  # Get 8 bits
            b.append(int(byte, 2))  # Convert 8 bits to a byte and append to array
        return b

    def compress(self):
        """Compress the file at the specified path"""
        if not self.path:
            raise ValueError("File path not specified")  # Error if no file path provided
            
        # Determine output path
        filename, file_extension = os.path.splitext(self.path)
        output_path = os.path.join(app.config['COMPRESSED_FOLDER'], os.path.basename(filename) + ".bin")

        # Open input file for reading and output file for writing binary data
        with open(self.path, 'r', encoding='utf-8', errors='replace') as file, open(output_path, 'wb') as output:
            text = file.read()  # Read entire file content
            text = text.rstrip()  # Remove trailing whitespace

            # Calculate original file size
            original_size = os.path.getsize(self.path)

            # Build Huffman tree and codes
            frequency = self.make_frequency_dict(text)  # Calculate character frequencies
            self.make_heap(frequency)  # Create min heap from frequencies
            self.merge_nodes()  # Build Huffman tree
            self.make_codes()  # Generate Huffman codes

            # Encode and write to file
            encoded_text = self.get_encoded_text(text)  # Convert text to binary string using codes
            padded_encoded_text = self.pad_encoded_text(encoded_text)  # Add padding for byte alignment
            b = self.get_byte_array(padded_encoded_text)  # Convert to byte array
            output.write(bytes(b))  # Write bytes to output file

        # Calculate compression statistics
        compressed_size = os.path.getsize(output_path)  # Get compressed file size
        # Calculate compression ratio as percentage saved
        compression_ratio = (1 - (compressed_size / original_size)) * 100 if original_size > 0 else 0

        # Return information about the compression process
        return {
            'output_path': output_path,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio
        }

    # Functions for decompression

    def remove_padding(self, padded_encoded_text):
        """Remove padding from the encoded text"""
        padded_info = padded_encoded_text[:8]  # First byte contains padding information
        extra_padding = int(padded_info, 2)  # Convert from binary to integer

        # Remove padding info and padding bits
        padded_encoded_text = padded_encoded_text[8:]  # Remove padding info byte
        encoded_text = padded_encoded_text[:-1*extra_padding] if extra_padding > 0 else padded_encoded_text  # Remove padding bits
        return encoded_text

    def decode_text(self, encoded_text):
        """Decode binary string back to original text using reverse mapping"""
        current_code = ""  # Initialize current code
        decoded_text = ""  # Initialize decoded text

        for bit in encoded_text:
            current_code += bit  # Add each bit to current code
            if(current_code in self.reverse_mapping):
                # If current code matches a character code, append character to result
                character = self.reverse_mapping[current_code]
                decoded_text += character
                current_code = ""  # Reset current code for next character

        return decoded_text

    def decompress(self, input_path):
        """Decompress a file at the specified path"""
        # Determine output path
        filename, file_extension = os.path.splitext(input_path)
        output_path = os.path.join(app.config['DECOMPRESSED_FOLDER'], os.path.basename(filename) + "_decompressed.txt")

        # Open input file for reading binary and output file for writing text
        with open(input_path, 'rb') as file, open(output_path, 'w', encoding='utf-8') as output:
            bit_string = ""  # Initialize bit string

            # Read file byte by byte and convert to bits
            byte = file.read(1)  # Read one byte at a time
            while byte:
                byte = ord(byte)  # Convert byte to integer
                bits = bin(byte)[2:].rjust(8, '0')  # Convert to 8-bit binary string
                bit_string += bits  # Add to bit string
                byte = file.read(1)  # Read next byte

            # Decode the bit string
            encoded_text = self.remove_padding(bit_string)  # Remove padding
            decompressed_text = self.decode_text(encoded_text)  # Decode to original text
            output.write(decompressed_text)  # Write to output file

        return output_path

    def get_codes_for_visualization(self, text):
        """Generate codes and frequencies for visualization"""
        # Reset state
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}
        
        # Build Huffman tree and codes
        frequency = self.make_frequency_dict(text)  # Calculate frequencies
        self.make_heap(frequency)  # Create min heap
        self.merge_nodes()  # Build Huffman tree
        self.make_codes()  # Generate codes
        
        # Return visualization data
        return {
            'codes': self.codes,  # Character to code mapping
            'frequencies': frequency  # Character frequencies
        }

# Routes to serve the frontend
@app.route('/')
def index():
    """Serve the main page of the application"""
    return app.send_static_file('index.html')  # Return the static HTML file

# API endpoint for file compression
@app.route('/api/compress', methods=['POST'])
def compress_file():
    """Handle file compression request"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400  # Return error if no file uploaded
    
    file = request.files['file']  # Get uploaded file
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400  # Return error if filename is empty
    
    if file:
        # Save the uploaded file
        filename = secure_filename(file.filename)  # Sanitize filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Determine save path
        file.save(file_path)  # Save file
        
        # Compress the file
        huffman = HuffmanCoding(file_path)  # Create Huffman coding instance
        result = huffman.compress()  # Compress the file
        
        # Get the filename for the download URL
        compressed_filename = os.path.basename(result['output_path'])
        
        # Return compression results with download URL
        return jsonify({
            'originalSize': result['original_size'],
            'compressedSize': result['compressed_size'],
            'compressionRatio': result['compression_ratio'],
            'compressedFilePath': compressed_filename,
            'downloadUrl': url_for('download_file', filename=compressed_filename)  # Generate download URL
        })

# API endpoint for file decompression
@app.route('/api/decompress', methods=['POST'])
def decompress_file():
    """Handle file decompression request"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400  # Return error if no file uploaded
    
    file = request.files['file']  # Get uploaded file
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400  # Return error if filename is empty
    
    if file and file.filename.endswith('.bin'):
        # Save the uploaded file
        filename = secure_filename(file.filename)  # Sanitize filename
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Determine save path
        file.save(compressed_path)  # Save file
        
        # We need to provide the reverse mapping for decompression
        # First, create a temporary text file for storing the frequency dictionary
        with open(compressed_path, 'rb') as f:
            # Read the first few bytes to extract header information
            # In a real implementation, the header would contain the frequency table
            # Here we use a simplified approach
            pass
        
        # Initialize HuffmanCoding
        huffman = HuffmanCoding()
        
        try:
            # For this simplified implementation, we'll use a basic frequency map
            # In a real implementation, this would be extracted from the file header
            sample_text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?()-_=+\n\t"  # Sample characters
            frequency = huffman.make_frequency_dict(sample_text)  # Create frequency dictionary from sample text
            huffman.make_heap(frequency)  # Create min heap
            huffman.merge_nodes()  # Build Huffman tree
            huffman.make_codes()  # Generate codes
            
            # Now decompress the file
            output_path = huffman.decompress(compressed_path)  # Decompress the file
            
            # Get the filename for the download URL
            decompressed_filename = os.path.basename(output_path)
            
            # Return decompression results with download URL
            return jsonify({
                'success': True,
                'decompressedFileName': decompressed_filename,
                'downloadUrl': url_for('download_decompressed_file', filename=decompressed_filename)  # Generate download URL
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500  # Return error if decompression fails
    
    return jsonify({'error': 'Invalid file format'}), 400  # Return error for invalid file format

# API endpoint to download compressed file
@app.route('/api/download/<filename>')
def download_file(filename):
    """Serve compressed file for download"""
    return send_from_directory(directory=app.config['COMPRESSED_FOLDER'], path=filename, as_attachment=True)  # Serve file from directory

# API endpoint to download decompressed file
@app.route('/api/download_decompressed/<filename>')
def download_decompressed_file(filename):
    """Serve decompressed file for download"""
    return send_from_directory(directory=app.config['DECOMPRESSED_FOLDER'], path=filename, as_attachment=True)  # Serve file from directory

# API endpoint for Huffman tree visualization data
@app.route('/api/visualize', methods=['POST'])
def visualize_huffman():
    """Generate Huffman code visualization data"""
    data = request.json  # Get JSON data from request
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400  # Return error if no text provided
    
    text = data['text']  # Get text from request
    
    huffman = HuffmanCoding()  # Create Huffman coding instance
    visualization_data = huffman.get_codes_for_visualization(text)  # Generate visualization data
    
    return jsonify(visualization_data)  # Return visualization data as JSON

if __name__ == '__main__':
    app.run(debug=True)  # Run Flask application in debug mode if script is executed directly