import numpy as np
import json
import time
import logging
from pathlib import Path
from typing import Optional, Union
import threading


class HDF5Logger:
    """
    logging using HDF5 format for efficient storage of large arrays.

    Advantages:
    - Automatic chunking and compression
    - Partial read/write without loading entire file
    - Stores metadata alongside data
    - Industry standard format

    Requires: h5py (pip install h5py)
    """

    def __init__(self, compression: str = 'gzip', compression_opts: int = 4):
        """
        Initialize HDF5 logging.

        Args:
            compression: Compression algorithm ('gzip', 'lzf', or None)
            compression_opts: Compression level (0-9 for gzip)
        """
        try:
            import h5py
            self.h5py = h5py
        except ImportError:
            raise ImportError(
                "h5py is required for HDF5Logger. Install with: pip install h5py"
            )

        self.compression = compression
        self.compression_opts = compression_opts

    def save(self, data: np.ndarray, filename: str,
             add_timestamp: bool = True,
             dataset_name: str = 'iq_samples',
             metadata: Optional[dict] = None) -> str:
        """
        Save numpy array to HDF5 file.

        Args:
            data: Numpy array to save
            filename: Output filename (without extension)
            add_timestamp: Whether to append timestamp to filename
            dataset_name: Name of dataset within HDF5 file
            metadata: Optional dictionary of metadata to store

        Returns:
            Path to saved HDF5 file
        """
        # Prepare filename
        if add_timestamp:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"

        if not filename.endswith('.h5'):
            filename = f"{filename}.h5"

        # Save to HDF5
        with self.h5py.File(filename, 'w') as f:
            # Create dataset with chunking and compression
            f.create_dataset(
                dataset_name,
                data=data,
                compression=self.compression,
                compression_opts=self.compression_opts if self.compression == 'gzip' else None,
                chunks=True
            )

            # Store metadata as attributes
            f[dataset_name].attrs['timestamp'] = time.strftime(
                "%Y-%m-%d %H:%M:%S")
            f[dataset_name].attrs['shape'] = data.shape
            f[dataset_name].attrs['dtype'] = str(data.dtype)

            if metadata:
                for key, value in metadata.items():
                    f[dataset_name].attrs[key] = value

        file_size_mb = Path(filename).stat().st_size / (1024 * 1024)
        logging.info(f"Saved {data.nbytes / (1024**2):.2f} MB data to {filename} "
                     f"(compressed to {file_size_mb:.2f} MB)")

        return filename

    def load(self, filename: str, dataset_name: str = 'iq_samples') -> tuple:
        """
        Load numpy array from HDF5 file.

        Args:
            filename: HDF5 file path
            dataset_name: Name of dataset to load

        Returns:
            Tuple of (data, metadata)
        """
        with self.h5py.File(filename, 'r') as f:
            data = f[dataset_name][:]
            metadata = dict(f[dataset_name].attrs)

        logging.info(f"Loaded dataset '{dataset_name}' from {filename}")
        return data, metadata

    def load_partial(self, filename: str, start: int, end: int,
                     dataset_name: str = 'iq_samples') -> np.ndarray:
        """
        Load partial data from HDF5 file without loading entire array.

        Args:
            filename: HDF5 file path
            start: Start index
            end: End index
            dataset_name: Name of dataset to load

        Returns:
            Partial numpy array
        """
        with self.h5py.File(filename, 'r') as f:
            data = f[dataset_name][start:end]

        return data


class SampleLogger:
    """
    High-level interface for logging large IQ sample datasets using HDF5.

    Supports async logging to avoid blocking data acquisition.
    """

    def __init__(self,
                 backend: str = 'hdf5',
                 compression: bool = True,
                 async_write: bool = True):
        """
        Initialize sample logging.

        Args:
            backend: 'hdf5' or 'auto' (both force HDF5)
            compression: Enable gzip compression for HDF5 datasets
            async_write: Write files asynchronously in background thread
        """
        if backend not in {'hdf5', 'auto'}:
            raise ValueError(
                f"Unknown backend: {backend}. Only 'hdf5' is supported.")

        self.async_write = async_write
        self.compression = compression
        self._write_threads = []

        # Always use HDF5 backend
        self.backend = HDF5Logger(
            compression='gzip' if compression else None,
            compression_opts=4
        )
        self.backend_name = 'hdf5'
        logging.info("Using HDF5 backend")

    def save(self, data: np.ndarray, filename: str,
             metadata: Optional[dict] = None,
             add_timestamp: bool = True) -> str:
        """
        Save IQ samples to disk.

        Args:
            data: Numpy array of IQ samples
            filename: Base filename or path (include channel ID in the name if needed)
            metadata: Optional metadata dictionary
            add_timestamp: Whether to append timestamp

        Returns:
            Path to saved file/directory
        """
        # Log data size
        size_mb = data.nbytes / (1024 * 1024)
        logging.info(f"Saving {size_mb:.2f} MB of IQ samples...")

        # Save data
        if self.async_write:
            # Async write in background thread
            thread = threading.Thread(
                target=self._async_save_worker,
                args=(data.copy(), filename, metadata, add_timestamp)
            )
            thread.daemon = False
            thread.start()
            self._write_threads.append(thread)
            logging.info(f"Started async write for {filename}")
            return filename
        else:
            # Synchronous write
            return self._do_save(data, filename, metadata, add_timestamp)

    def _async_save_worker(self, data, filename, metadata, add_timestamp):
        """Worker function for async writes."""
        try:
            self._do_save(data, filename, metadata, add_timestamp)
        except Exception as e:
            logging.error(f"Async write failed: {e}", exc_info=True)

    def _do_save(self, data, filename, metadata, add_timestamp):
        """Actual save implementation."""
        return self.backend.save(
            data,
            filename,
            add_timestamp=add_timestamp,
            metadata=metadata
        )

    def wait_for_writes(self):
        """Wait for all async write operations to complete."""
        if self._write_threads:
            logging.info(
                f"Waiting for {len(self._write_threads)} write operations...")
            for thread in self._write_threads:
                thread.join()
            self._write_threads.clear()
            logging.info("All writes completed")

    def load(self, path: str, dataset_name: str = 'iq_samples'):
        """
        Load IQ samples from disk.

        Args:
            path: File or directory path
            dataset_name: Dataset name (HDF5 only)

        Returns:
            Numpy array or tuple of (data, metadata) for HDF5
        """
        path_obj = Path(path)

        if path_obj.suffix != '.h5':
            raise ValueError(
                f"SampleLogger now only supports HDF5 files (.h5). Invalid path: {path}"
            )

        return HDF5Logger().load(path, dataset_name)


# Convenience function for backward compatibility
def save_to_file_chunked(data: np.ndarray, filename: str) -> str:
    """
    Convenience function to save large IQ samples using the HDF5 backend.

    Kept for backward compatibility with older code that expected chunked
    numpy output, but now always writes HDF5 files for better performance.

    Args:
        data: Numpy array to save
        filename: Base filename (without extension, include channel ID in name if needed)

    Returns:
        Path to saved file
    """
    logging = SampleLogger(backend='hdf5', async_write=False)
    return logging.save(data, filename)
