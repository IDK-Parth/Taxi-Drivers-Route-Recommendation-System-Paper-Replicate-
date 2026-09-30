import numpy as np
from scipy import sparse
from pathlib import Path

DATA_DIR = Path("../data/sample_input")
OUTPUT_FILE = DATA_DIR / "sample_input.npy"

CHANNEL_FILES = [
    "sample_last_dim_0.npz",
    "sample_last_dim_1.npz",
    "sample_last_dim_2.npz",
]


def reconstruct_sample_input():
    print("=" * 60)
    print("Preparing sample input")
    print("=" * 60)

    if OUTPUT_FILE.exists():
        print(f"\nAlready exists:")
        print(f"  {OUTPUT_FILE}")
        return

    matrices = []

    for filename in CHANNEL_FILES:
        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        print(f"\nLoading: {filename}")

        matrix = sparse.load_npz(path)

        print(f"  Shape : {matrix.shape}")
        print(f"  Dtype : {matrix.dtype}")
        print(f"  NNZ   : {matrix.nnz}")

        matrices.append(matrix)

    # Verify dimensions
    shapes = [matrix.shape for matrix in matrices]

    if len(set(shapes)) != 1:
        raise ValueError(f"Channel dimensions do not match: {shapes}")

    rows, columns = shapes[0]
    channels = len(matrices)

    print("\nCreating combined array...")
    print(f"  Rows     : {rows}")
    print(f"  Columns  : {columns}")
    print(f"  Channels : {channels}")

    # Create memory-mapped NumPy array
    data = np.lib.format.open_memmap(
        OUTPUT_FILE,
        mode="w+",
        dtype=np.float64,
        shape=(rows, columns, channels),
    )

    # Convert one channel at a time
    for channel, matrix in enumerate(matrices):

        print(f"\nProcessing channel {channel + 1}/{channels}")

        for start in range(0, rows, 8):
            end = min(start + 8, rows)

            data[start:end, :, channel] = (
                matrix[start:end].toarray()
            )

            print(
                f"  Rows {start:3d} - {end:3d}",
                end="\r",
            )

        data.flush()
        print(f"\n  Channel {channel} complete.")

    del data

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(f"Created: {OUTPUT_FILE}")

    # Verify
    result = np.load(OUTPUT_FILE, mmap_mode="r")

    print(f"Shape : {result.shape}")
    print(f"Dtype : {result.dtype}")
    print("=" * 60)


if __name__ == "__main__":
    reconstruct_sample_input()