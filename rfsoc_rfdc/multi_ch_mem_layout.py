import numpy as np
from abc import ABC, abstractmethod


class MCHMemLayout(ABC):

    def __init__(self, channel_count, dp_vect_dim):
        self.channel_count = channel_count
        self.dp_vect_dim = dp_vect_dim

    @abstractmethod
    def gen_layout(self, mch_i_samples, mch_q_samples):
        """Generate memory layout given I/Q samples for each DAC channels"""
        pass

    @abstractmethod
    def dec_layout(self, raw_mch_data):
        """Decode I/Q samples for each ADC channels given interleaved memory layout"""
        pass


class MchIq2RLayout(MCHMemLayout):
    """For multi-channel IQ-to-real memory layout generator (Tx)"""

    def __init__(self, channel_count, dp_vect_dim):
        super().__init__(channel_count, dp_vect_dim)

    def mch_duplication(self, data):
        """Duplicate the data across multiple channels"""
        return np.tile(data, (1, self.channel_count))

    def gen_layout(self, mch_data):
        # Ensure input mch_data is channel_count x waveform_length
        assert len(
            mch_data.shape) == 2 and mch_data.shape[0] == self.channel_count, f"Wrong dimension for mch_data"

        rows, cols = mch_data.shape

        # Pad zeros
        remains = cols % self.dp_vect_dim
        if remains != 0:
            pad_size = self.dp_vect_dim - remains
            mch_data = np.pad(mch_data, ((0, 0), (0, pad_size)),
                              mode='constant', constant_values=0)

        mch_layout = []
        for col_start in range(0, cols, self.dp_vect_dim):
            for row in range(rows):
                for col in range(col_start, col_start + self.dp_vect_dim):
                    mch_layout.append(int(mch_data[row, col].real))
                    mch_layout.append(int(mch_data[row, col].imag))
        return np.array(mch_layout)

    def dec_layout(self, raw_mch_data):
        raise RuntimeError(f"dec_layout is not available.")


class MchR2RLayout(MCHMemLayout):
    """For multi-channel real-to-real memory layout generator and decoding (Tx and Rx)"""

    def __init__(self, channel_count, dp_vect_dim):
        super().__init__(channel_count, dp_vect_dim)

    def gen_layout(self, data):
        # Reshape according to the dp_vect_dim count
        vect_dim = np.reshape(data, (-1, self.dp_vect_dim))
        # Duplicate data for multi-channel
        mch_dim = np.tile(vect_dim, (1, self.channel_count))
        # Flatten matrices
        mch = mch_dim.flatten()
        # Interleaved IQ
        return mch

    def dec_layout(self, raw_mch_data):
        arr_size_per_ch = len(raw_mch_data) // self.channel_count
        mch = np.zeros(
            (self.channel_count, arr_size_per_ch), dtype=np.complex128)

        step_size = self.channel_count * self.dp_vect_dim
        for ch in range(self.channel_count):
            if self.dp_vect_dim != 1:
                vect_dimension = np.zeros(
                    (self.dp_vect_dim, arr_size_per_ch // self.dp_vect_dim), dtype=np.complex128)
                for vect in range(self.dp_vect_dim):
                    vect_dimension[vect] = raw_mch_data[self.dp_vect_dim *
                                                        ch + vect::step_size]
                mch[ch] = np.stack(vect_dimension).T.reshape(-1)
            else:  # dp_vect_dim = 1
                iq = raw_mch_data[ch::step_size]
                mch[ch] = iq
        return mch


class MchR2IqLayout(MCHMemLayout):
    """For multi-channel real-to-IQ memory layout decoding (Rx)"""

    def __init__(self, channel_count, dp_vect_dim):
        super().__init__(channel_count, dp_vect_dim)

    def gen_layout(self, iq):
        raise RuntimeError(f"gen_layout function is not available.")

    def dec_layout(self, raw_mch_data):
        arr_size_per_ch = len(raw_mch_data) // self.channel_count
        mch_iq = np.zeros(
            (self.channel_count, arr_size_per_ch), dtype=np.complex128)

        step_size = self.channel_count * self.dp_vect_dim
        for ch in range(self.channel_count):
            if self.dp_vect_dim != 1:
                vect_dimension = np.zeros(
                    (self.dp_vect_dim, arr_size_per_ch // self.dp_vect_dim), dtype=np.complex128)
                for vect in range(self.dp_vect_dim):
                    vect_dimension[vect] = raw_mch_data[self.dp_vect_dim *
                                                        ch + vect::step_size]
                interleaved = np.stack(vect_dimension).T.reshape(-1)
                mch_iq[ch] = interleaved
            else:  # dp_vect_dim = 1
                iq = raw_mch_data[ch::step_size]
                mch_iq[ch] = iq
        return mch_iq


def TestMchIq2RLayout():
    print("Testing MchIq2RLayout")
    # Generate complex data: [0+0j, 1+1j, ..., 31+31j]
    raw = np.arange(32) + 1j * np.arange(32)

    # Test 1: channel_count=2, dp_vect_dim=2, shape (2, 16)
    mch_data1 = raw.reshape(2, 16)
    layout1 = MchIq2RLayout(channel_count=2, dp_vect_dim=2)
    result1 = layout1.gen_layout(mch_data1)
    expected1 = np.array([
        0,  0,  1,  1, 16, 16, 17, 17,
        2,  2,  3,  3, 18, 18, 19, 19,
        4,  4,  5,  5, 20, 20, 21, 21,
        6,  6,  7,  7, 22, 22, 23, 23,
        8,  8,  9,  9, 24, 24, 25, 25,
        10, 10, 11, 11, 26, 26, 27, 27,
        12, 12, 13, 13, 28, 28, 29, 29,
        14, 14, 15, 15, 30, 30, 31, 31
    ])
    assert np.allclose(result1, expected1), "Test (2,2) failed"
    print("Test (2,2) passed. \nResult: ", result1)

    # Test 2: channel_count=4, dp_vect_dim=1, shape (4, 8)
    mch_data2 = raw.reshape(4, 8)
    layout2 = MchIq2RLayout(channel_count=4, dp_vect_dim=1)
    result2 = layout2.gen_layout(mch_data2)
    expected2 = np.array([
        0, 0, 8, 8, 16, 16, 24, 24,
        1, 1, 9, 9, 17, 17, 25, 25,
        2, 2, 10, 10, 18, 18, 26, 26,
        3, 3, 11, 11, 19, 19, 27, 27,
        4, 4, 12, 12, 20, 20, 28, 28,
        5, 5, 13, 13, 21, 21, 29, 29,
        6, 6, 14, 14, 22, 22, 30, 30,
        7, 7, 15, 15, 23, 23, 31, 31
    ])
    assert np.allclose(result2, expected2), "Test (4,1) failed"
    print("Test (4,1) passed. \nResult: ", result2)


def TestMchR2IqLayout():
    print("Testing MchR2IqLayout")
    # Generate complex data: [0+0j, 1+1j, ..., 31+31j]
    raw = np.arange(32) + 1j * np.arange(32)

    # Test 1: channel_count=2, dp_vect_dim=2
    mch_data1 = raw
    layout1 = MchR2IqLayout(channel_count=2, dp_vect_dim=2)
    result1 = layout1.dec_layout(mch_data1)
    expected1 = np.array([
        [0. + 0.j,  1. + 1.j,  4. + 4.j,  5. + 5.j,  8. + 8.j,  9. + 9.j, 12.+12.j, 13.+13.j,
         16.+16.j, 17.+17.j, 20.+20.j, 21.+21.j, 24.+24.j, 25.+25.j, 28.+28.j, 29.+29.j],
        [2. + 2.j,  3. + 3.j,  6. + 6.j,  7. + 7.j, 10.+10.j, 11.+11.j, 14.+14.j, 15.+15.j,
         18.+18.j, 19.+19.j, 22.+22.j, 23.+23.j, 26.+26.j, 27.+27.j, 30.+30.j, 31.+31.j]
    ])
    assert np.allclose(result1, expected1), "Test (2,2) failed"
    print("Test (2,2) passed. \nResult: ", result1)

    # Test 2: channel_count=4, dp_vect_dim=1
    mch_data2 = raw
    layout2 = MchR2IqLayout(channel_count=4, dp_vect_dim=1)
    result2 = layout2.dec_layout(mch_data2)
    expected2 = np.array([
        [0. + 0.j,  4. + 4.j,  8. + 8.j, 12.+12.j,
            16.+16.j, 20.+20.j, 24.+24.j, 28.+28.j],
        [1. + 1.j,  5. + 5.j,  9. + 9.j, 13.+13.j,
            17.+17.j, 21.+21.j, 25.+25.j, 29.+29.j],
        [2. + 2.j,  6. + 6.j, 10.+10.j, 14.+14.j,
            18.+18.j, 22.+22.j, 26.+26.j, 30.+30.j],
        [3. + 3.j,  7. + 7.j, 11.+11.j, 15.+15.j,
            19.+19.j, 23.+23.j, 27.+27.j, 31.+31.j]
    ])
    assert np.allclose(result2, expected2), "Test (4,1) failed"
    print("Test (4,1) passed.\nResult: ", result2)


if __name__ == "__main__":
    TestMchIq2RLayout()
    TestMchR2IqLayout()
