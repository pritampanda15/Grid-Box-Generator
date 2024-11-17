from flask import Flask, request, jsonify, send_file, render_template
from flask import send_from_directory, abort
from werkzeug.utils import safe_join
from flask import send_file, request
import os
from Bio.PDB import PDBParser
import numpy as np
import time


app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')
    return "Flask app is running. Use the /upload endpoint."


# Folder for uploaded files
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route for uploading files
@app.route('/upload', methods=['POST'])
def upload_pdb():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.pdb'):
        return jsonify({'error': 'Invalid file type. Please upload a PDB file.'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    return jsonify({'message': 'File uploaded successfully!', 'filepath': filepath})

@app.route('/grid', methods=['POST'])
def generate_grid():
    try:
        # Parse incoming JSON request
        data = request.json
        filepath = data.get('filepath')  # Path to the uploaded file
        mode = data.get('mode')  # Docking mode: "blind" or "targeted"
        residues = data.get('residues', [])  # Targeted residues as a list

        # Check if file exists
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found. Please upload a valid file.'}), 400

        # Parse the PDB file
        parser = PDBParser()
        structure = parser.get_structure('protein', filepath)

        coords = []
        if mode == 'blind':
            # Collect all atom coordinates for blind docking
            for atom in structure.get_atoms():
                coords.append(atom.coord)
        elif mode == 'targeted':
            if not residues:
                return jsonify({'error': 'No residues specified for targeted docking.'}), 400
            # Extract coordinates of specific residues
            for residue in residues:
                residue = residue.strip()
                chain_id, res_id = residue.split(':')
                chain_id = chain_id.strip()
                res_id = res_id.strip()
                for chain in structure.get_chains():
                    if chain.id == chain_id:
                        for res in chain.get_residues():
                            if res.id[1] == int(res_id):  # Match residue number
                                for atom in res:
                                    coords.append(atom.coord)
        else:
            return jsonify({'error': 'Invalid mode selected.'}), 400

        if not coords:
            return jsonify({'error': 'No atoms found for the specified residues.'}), 400

        coords = np.array(coords)
        min_coords = coords.min(axis=0) - 5  # Add buffer
        max_coords = coords.max(axis=0) + 5  # Add buffer

        center = (min_coords + max_coords) / 2
        size = max_coords - min_coords

        # Create configuration file for grid box
        config = f"""
center_x = {center[0]}
center_y = {center[1]}
center_z = {center[2]}
size_x = {size[0]}
size_y = {size[1]}
size_z = {size[2]}
"""

        # Generate a unique filename using timestamp and mode
        timestamp = int(time.time())
        config_filename = f'config_{mode}_{timestamp}.txt'
        config_path = os.path.join(app.config['UPLOAD_FOLDER'], config_filename)
        with open(config_path, 'w') as f:
            f.write(config)

        # Extract grid dimensions to send to the client
        grid_dimensions = {
        'center_x': float(center[0]),
        'center_y': float(center[1]),
        'center_z': float(center[2]),
        'size_x': float(size[0]),
        'size_y': float(size[1]),
        'size_z': float(size[2]),
        }

        # Return the filename to the client for reference or download
        return jsonify({
            'message': 'Grid configuration generated!',
            'config_file': config_filename,
            'config_path': config_path,
            'grid_dimensions': grid_dimensions
        })
    except Exception as e:
        app.logger.error(f"Error during grid generation: {e}")
        return jsonify({'error': 'An error occurred during grid generation.'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Log the filename
        app.logger.debug(f"Requested filename: {filename}")

        # Use safe_join to construct the file path
        file_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
        app.logger.debug(f"Constructed file path: {file_path}")

        # Check if the file exists
        if not os.path.isfile(file_path):
            app.logger.error(f"File not found at path: {file_path}")
            abort(404)

        # Send the file
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True
        )
    except Exception as e:
        app.logger.error(f"Error during file download: {e}")
        return jsonify({'error': 'An error occurred during file download.'}), 500

@app.route('/get_pdb', methods=['GET'])
def get_pdb():
    filepath = request.args.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'File not found.'}), 404
    return send_file(filepath, mimetype='chemical/x-pdb')


if __name__ == '__main__':
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000), debug=True))
