from rfsoc_rfdc.sample_logger import SampleLogger

# Initialize global sample logger for efficient large file handling (HDF5 backend)
_sample_logger = SampleLogger(
    backend='hdf5', async_write=True, compression=True)


def save_to_file(data, filename):
    """
    Save IQ samples to HDF5 file for efficient storage of large datasets.

    This function uses SampleLogger with HDF5 backend for efficient handling of 
    large arrays (>64MB). Files are automatically compressed using gzip and written
    asynchronously to avoid blocking data acquisition.

    Args:
        data: Numpy array of IQ samples
        filename: Full path including directory (e.g., "./wave_files/Rx0_raw")
                 Extension will be replaced with .h5, timestamp will be added
    """
    # Strip only known file extensions to preserve paths with dots (like ./wave_files)
    base_name = filename
    for ext in ['.npy', '.npz', '.h5', '.hdf5']:
        if filename.endswith(ext):
            base_name = filename[:-len(ext)]
            break

    # Use SampleLogger for efficient HDF5 storage
    _sample_logger.save(data, base_name, add_timestamp=True)
