import streamlit as st
import os
import time
import numpy as np
from Bio.PDB import PDBParser
import py3Dmol
from stmol import showmol
import tempfile

# Set page config
st.set_page_config(
    page_title="PDB Grid Generator",
    page_icon="🧬",
    layout="wide"
)

# Folder for uploaded files
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to visualize protein structure and grid box
def visualize_protein_and_grid(pdb_path, grid_dimensions=None):
    """
    Display the protein structure with optional grid box.
    """
    # Read PDB file
    with open(pdb_path, 'r') as f:
        pdb_data = f.read()
    
    # Set up the viewer
    xyzview = py3Dmol.view(width=700, height=500)
    xyzview.addModel(pdb_data, 'pdb')
    xyzview.setStyle({'cartoon': {'color': 'spectrum'}})
    
    # Add grid box if dimensions are provided
    if grid_dimensions:
        center_x = grid_dimensions['center_x']
        center_y = grid_dimensions['center_y']
        center_z = grid_dimensions['center_z']
        size_x = grid_dimensions['size_x']
        size_y = grid_dimensions['size_y']
        size_z = grid_dimensions['size_z']
        
        # Calculate box corners
        corner1 = [center_x - size_x/2, center_y - size_y/2, center_z - size_z/2]
        corner2 = [center_x + size_x/2, center_y + size_y/2, center_z + size_z/2]
        
        # Add box to viewer
        xyzview.addBox({
            'center': {'x': center_x, 'y': center_y, 'z': center_z},
            'dimensions': {'w': size_x, 'h': size_y, 'd': size_z},
            'color': 'green',
            'opacity': 0.5
        })
    
    # Set camera
    xyzview.zoomTo()
    # Return the viewer
    showmol(xyzview, height=500, width=700)

def generate_grid_config(pdb_path, mode, residues=None):
    """
    Generate grid configuration based on PDB file and docking mode.
    """
    try:
        # Parse the PDB file
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('protein', pdb_path)

        coords = []
        if mode == 'blind':
            # Collect all atom coordinates for blind docking
            for atom in structure.get_atoms():
                coords.append(atom.coord)
        elif mode == 'targeted':
            if not residues:
                st.error('No residues specified for targeted docking.')
                return None
            
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

        if not coords:
            st.error('No atoms found for the specified criteria.')
            return None

        coords = np.array(coords)
        min_coords = coords.min(axis=0) - 5  # Add buffer
        max_coords = coords.max(axis=0) + 5  # Add buffer

        center = (min_coords + max_coords) / 2
        size = max_coords - min_coords

        # Create configuration file for grid box
        config = f"""center_x = {center[0]}
center_y = {center[1]}
center_z = {center[2]}
size_x = {size[0]}
size_y = {size[1]}
size_z = {size[2]}"""

        # Generate a unique filename using timestamp and mode
        timestamp = int(time.time())
        config_filename = f'config_{mode}_{timestamp}.txt'
        config_path = os.path.join(UPLOAD_FOLDER, config_filename)
        
        with open(config_path, 'w') as f:
            f.write(config)

        # Extract grid dimensions to return
        grid_dimensions = {
            'center_x': float(center[0]),
            'center_y': float(center[1]),
            'center_z': float(center[2]),
            'size_x': float(size[0]),
            'size_y': float(size[1]),
            'size_z': float(size[2]),
        }

        return {
            'config_path': config_path,
            'config_filename': config_filename,
            'grid_dimensions': grid_dimensions,
            'config_text': config
        }
        
    except Exception as e:
        st.error(f"Error during grid generation: {str(e)}")
        return None

# Main Streamlit UI
st.title("PDB Grid Generator")
st.markdown("""
This application helps you generate grid box configurations for molecular docking.
Upload a PDB file and choose between blind docking or targeted docking based on specific residues.
""")

# File upload section
uploaded_file = st.file_uploader("Upload a PDB file", type=['pdb'])

if uploaded_file:
    # Save the uploaded file
    pdb_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(pdb_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"File uploaded: {uploaded_file.name}")
    
    # Docking mode selection
    st.header("Docking Configuration")
    docking_mode = st.radio("Select docking mode:", ["blind", "targeted"])
    
    residues_input = None
    if docking_mode == "targeted":
        st.info("Specify residues in format 'Chain:ResidueNumber', one per line (e.g., A:156)")
        residues_input = st.text_area("Enter target residues:", height=150)
    
    # Generate grid button
    if st.button("Generate Grid Configuration"):
        with st.spinner("Generating grid configuration..."):
            # Process residues input if in targeted mode
            residues = None
            if docking_mode == "targeted":
                if residues_input:
                    residues = [line for line in residues_input.split('\n') if line.strip()]
                    if not residues:
                        st.error("Please specify at least one residue for targeted docking.")
                        st.stop()
                else:
                    st.error("Please specify residues for targeted docking.")
                    st.stop()
            
            # Generate grid configuration
            result = generate_grid_config(pdb_path, docking_mode, residues)
            
            if result:
                st.success("Grid configuration generated successfully!")
                
                # Display grid parameters
                st.subheader("Grid Parameters")
                grid_params = result['grid_dimensions']
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Center X:** {grid_params['center_x']:.3f}")
                    st.write(f"**Center Y:** {grid_params['center_y']:.3f}")
                    st.write(f"**Center Z:** {grid_params['center_z']:.3f}")
                
                with col2:
                    st.write(f"**Size X:** {grid_params['size_x']:.3f}")
                    st.write(f"**Size Y:** {grid_params['size_y']:.3f}")
                    st.write(f"**Size Z:** {grid_params['size_z']:.3f}")
                
                # Display configuration text
                st.subheader("Configuration File")
                st.code(result['config_text'])
                
                # Download button for configuration
                with open(result['config_path'], "rb") as file:
                    st.download_button(
                        label="Download Grid Configuration",
                        data=file,
                        file_name=result['config_filename'],
                        mime="text/plain"
                    )
                
                # Visualize the protein and grid box
                st.subheader("Protein Structure with Grid Box")
                visualize_protein_and_grid(pdb_path, grid_params)
    
    # Always show the protein structure when a file is uploaded
    else:
        st.header("Protein Structure Preview")
        visualize_protein_and_grid(pdb_path)

# Information in sidebar
st.sidebar.header("About the Grid Generator")
st.sidebar.markdown("""
This tool helps you generate grid box configurations for molecular docking simulations.

**Features:**
- Upload PDB structure files
- Generate grid boxes for blind docking
- Generate grid boxes for targeted docking based on specific residues
- Interactive 3D visualization of the protein and grid box
- Download configuration files for docking software

**How to use:**
1. Upload a PDB file
2. Select docking mode (blind or targeted)
3. If targeted, specify residues in the format 'Chain:ResidueNumber'
4. Click "Generate Grid Configuration"
5. Download the configuration file

This tool is particularly useful for preparing files for AutoDock Vina and similar molecular docking software.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Created by [Your Name]")
st.sidebar.markdown("[GitHub Repository](https://github.com/pritampanda15)")
