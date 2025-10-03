def stitch_and_register_tiles_ashlar(
    input_files,
    output_path="ashlar_output.ome.tif",
    align_channel=0,
    maximum_shift=15,
    filter_sigma=None,
    tile_size=1024,
    ffp_files=None,
    dfp_files=None,
    flip_x=False,
    flip_y=False,
    output_dir="./",
):
    """Stitch and register multi-tile microscopy images using ASHLAR.
    
    ASHLAR performs fast, high-quality stitching of microscopy images and co-registers
    multiple rounds of cyclic imaging for methods such as CyCIF and CODEX.
    
    Parameters
    ----------
    input_files : list of str
        List of image file paths to be processed, one per cycle. Can be BioFormats-supported
        vendor formats or plain TIFF files.
    output_path : str, optional
        Output file path. If ends in .ome.tif, writes pyramidal OME-TIFF. 
        Default: "ashlar_output.ome.tif"
    align_channel : int, optional
        Reference channel number for image alignment. Numbering starts at 0. Default: 0
    maximum_shift : float, optional
        Maximum allowed per-tile corrective shift in microns. Default: 15
    filter_sigma : float, optional
        Filter images before alignment using Gaussian kernel with this standard deviation
        in pixels. Default: None (no filtering)
    tile_size : int, optional
        Pyramid tile size for OME-TIFF output. Default: 1024
    ffp_files : list of str, optional
        Flat field profile image file(s) for illumination correction. Specify one common
        file for all cycles or one per cycle. Default: None
    dfp_files : list of str, optional
        Dark field profile image file(s) for illumination correction. Specify one common
        file for all cycles or one per cycle. Default: None
    flip_x : bool, optional
        Flip tile positions left-to-right. Default: False
    flip_y : bool, optional
        Flip tile positions top-to-bottom. Default: False
    output_dir : str, optional
        Directory to save output files. Default: "./"
        
    Returns
    -------
    str
        Research log summarizing the stitching and registration process
        
    Examples
    --------
    >>> # Stitch tiles from a single cycle
    >>> log = stitch_and_register_tiles_ashlar(
    ...     input_files=['cycle1_tile1.tif', 'cycle1_tile2.tif'],
    ...     output_path='stitched.ome.tif'
    ... )
    
    >>> # Register multiple cycles with flat field correction
    >>> log = stitch_and_register_tiles_ashlar(
    ...     input_files=['cycle1.rcpnl', 'cycle2.rcpnl'],
    ...     ffp_files=['ffp.tif'],
    ...     align_channel=1,
    ...     maximum_shift=30
    ... )
    """
    import os
    import subprocess
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize research log
    log = []
    log.append("# ASHLAR Image Stitching and Registration")
    log.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Validate inputs
    if not input_files:
        return "Error: No input files provided"
    
    if not isinstance(input_files, list):
        input_files = [input_files]
    
    # Check that input files exist
    missing_files = [f for f in input_files if not os.path.exists(f)]
    if missing_files:
        return f"Error: Input files not found: {missing_files}"
    
    log.append("## Input Parameters")
    log.append(f"- Number of input files: {len(input_files)}")
    log.append(f"- Output path: {output_path}")
    log.append(f"- Alignment channel: {align_channel}")
    log.append(f"- Maximum shift: {maximum_shift} microns")
    if filter_sigma:
        log.append(f"- Gaussian filter sigma: {filter_sigma} pixels")
    log.append(f"- Tile size: {tile_size} pixels")
    
    # Build the ashlar command
    cmd = ["ashlar"]
    
    # Add input files
    cmd.extend(input_files)
    
    # Add output path
    full_output_path = os.path.join(output_dir, output_path)
    cmd.extend(["-o", full_output_path])
    
    # Add alignment channel
    cmd.extend(["-c", str(align_channel)])
    
    # Add maximum shift
    cmd.extend(["-m", str(maximum_shift)])
    
    # Add filter sigma if specified
    if filter_sigma is not None:
        cmd.extend(["--filter-sigma", str(filter_sigma)])
    
    # Add tile size
    cmd.extend(["--tile-size", str(tile_size)])
    
    # Add flat field profiles if specified
    if ffp_files:
        if not isinstance(ffp_files, list):
            ffp_files = [ffp_files]
        cmd.append("--ffp")
        cmd.extend(ffp_files)
        log.append(f"- Flat field profiles: {len(ffp_files)} file(s)")
    
    # Add dark field profiles if specified
    if dfp_files:
        if not isinstance(dfp_files, list):
            dfp_files = [dfp_files]
        cmd.append("--dfp")
        cmd.extend(dfp_files)
        log.append(f"- Dark field profiles: {len(dfp_files)} file(s)")
    
    # Add flip options
    if flip_x:
        cmd.append("--flip-x")
        log.append("- Flip X: enabled")
    if flip_y:
        cmd.append("--flip-y")
        log.append("- Flip Y: enabled")
    
    log.append("\n## Processing")
    log.append(f"Command: {' '.join(cmd)}\n")
    
    # Run ASHLAR
    try:
        log.append("Running ASHLAR stitching and registration...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        log.append("✓ ASHLAR completed successfully\n")
        
        # Log stdout if available
        if result.stdout:
            log.append("## ASHLAR Output")
            log.append(result.stdout)
        
        # Check output file exists
        if os.path.exists(full_output_path):
            file_size = os.path.getsize(full_output_path) / (1024**2)  # Size in MB
            log.append("\n## Results")
            log.append(f"- Output file: {full_output_path}")
            log.append(f"- File size: {file_size:.2f} MB")
        
    except subprocess.CalledProcessError as e:
        log.append(f"\n✗ Error: ASHLAR failed with exit code {e.returncode}")
        log.append(f"\nError message:\n{e.stderr}")
        return "\n".join(log)
    
    except Exception as e:
        log.append(f"\n✗ Error: {str(e)}")
        return "\n".join(log)
    
    log.append("\n## Conclusion")
    log.append("Image stitching and registration completed successfully.")
    log.append(f"Registered image saved to: {full_output_path}")
    
    return "\n".join(log)


def align_cyclic_images_ashlar(
    cycle_files,
    output_path="registered_cycles.ome.tif",
    align_channel=0,
    maximum_shift=30,
    output_dir="./",
):
    """Align multiple rounds of cyclic imaging (e.g., CyCIF, CODEX) using ASHLAR.
    
    This is a simplified wrapper specifically for multi-cycle registration, which is
    common in cyclic immunofluorescence methods.
    
    Parameters
    ----------
    cycle_files : list of str
        List of image files, one per imaging cycle, in order
    output_path : str, optional
        Output OME-TIFF file path. Default: "registered_cycles.ome.tif"
    align_channel : int, optional
        Channel to use for alignment across cycles. Default: 0
    maximum_shift : float, optional
        Maximum shift between cycles in microns. Default: 30
    output_dir : str, optional
        Output directory. Default: "./"
        
    Returns
    -------
    str
        Research log summarizing the registration
    """
    return stitch_and_register_tiles_ashlar(
        input_files=cycle_files,
        output_path=output_path,
        align_channel=align_channel,
        maximum_shift=maximum_shift,
        output_dir=output_dir
    )


def stitch_microscopy_tiles_ashlar(
    tile_directory,
    output_path="stitched.ome.tif",
    file_pattern="*.tif",
    maximum_shift=15,
    filter_sigma=None,
    output_dir="./",
):
    """Stitch microscopy tiles from a directory using ASHLAR.
    
    Convenience function for stitching tiles from a single imaging round when
    all tiles are in one directory.
    
    Parameters
    ----------
    tile_directory : str
        Directory containing image tiles
    output_path : str, optional
        Output file name. Default: "stitched.ome.tif"
    file_pattern : str, optional
        Glob pattern to match tile files. Default: "*.tif"
    maximum_shift : float, optional
        Maximum corrective shift in microns. Default: 15
    filter_sigma : float, optional
        Gaussian filter sigma for pre-alignment filtering. Default: None
    output_dir : str, optional
        Output directory. Default: "./"
        
    Returns
    -------
    str
        Research log
    """
    import glob
    import os
    
    # Find all matching files in directory
    pattern = os.path.join(tile_directory, file_pattern)
    tile_files = sorted(glob.glob(pattern))
    
    if not tile_files:
        return f"Error: No files matching pattern '{file_pattern}' found in {tile_directory}"
    
    return stitch_and_register_tiles_ashlar(
        input_files=tile_files,
        output_path=output_path,
        maximum_shift=maximum_shift,
        filter_sigma=filter_sigma,
        output_dir=output_dir
    )

