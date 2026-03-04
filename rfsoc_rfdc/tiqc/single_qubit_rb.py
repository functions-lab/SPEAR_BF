"""
Single-Qubit Randomized Benchmarking (RB) Module

This module provides the SingleQubitRB class for generating and decomposing
single-qubit Clifford sequences for randomized benchmarking experiments.
"""

import numpy as np
from collections import deque
from typing import List, Tuple, Optional


def wrap_2pi(phi: float) -> float:
    """Wrap phase angle to [-π, π) range."""
    return (phi + np.pi) % (2*np.pi) - np.pi


def R_axis_angle(axis: str, angle_deg: int) -> np.ndarray:
    """
    Ideal single-qubit rotation matrix for axis ∈ {x,y,z} and angle in degrees.

    Parameters
    ----------
    axis : str
        Rotation axis ('x', 'y', or 'z')
    angle_deg : int
        Rotation angle in degrees

    Returns
    -------
    np.ndarray
        2x2 unitary rotation matrix
    """
    theta = np.deg2rad(angle_deg)
    c = np.cos(theta/2)
    s = np.sin(theta/2)
    if axis == 'x':
        return np.array([[c, -1j*s], [-1j*s, c]], dtype=np.complex128)
    elif axis == 'y':
        return np.array([[c, -s], [s, c]], dtype=np.complex128)
    elif axis == 'z':
        return np.array([[np.exp(-1j*theta/2), 0],
                         [0, np.exp(+1j*theta/2)]], dtype=np.complex128)
    else:
        raise ValueError(f"Invalid axis: {axis}")


def canonical_key(U: np.ndarray) -> tuple:
    """
    Stable canonicalization of a 2x2 unitary up to global phase and ± sign.

    Steps:
    1) Remove global phase using tr(U) when available, else a deterministic entry fallback.
    2) Enforce a unique sign via a fixed real-part rule.
    3) Round to suppress float jitter.

    Parameters
    ----------
    U : np.ndarray
        2x2 unitary matrix

    Returns
    -------
    tuple
        Flattened canonical representation of the matrix
    """
    U = np.asarray(U, dtype=np.complex128)
    tr = np.trace(U)
    if np.abs(tr) > 1e-14:
        phi = np.angle(tr)
    else:
        order = [(0, 0), (0, 1), (1, 0), (1, 1)]
        phi = 0.0
        for (i, j) in order:
            if np.abs(U[i, j]) > 1e-14:
                phi = np.angle(U[i, j])
                break
    U0 = U * np.exp(-1j*phi)

    def needs_flip(M):
        if M[0, 0].real < -1e-12:
            return True
        if np.isclose(M[0, 0].real, 0.0, atol=1e-12) and M[0, 1].real < -1e-12:
            return True
        if (np.isclose(M[0, 0].real, 0.0, atol=1e-12) and
            np.isclose(M[0, 1].real, 0.0, atol=1e-12) and
                M[1, 0].real < -1e-12):
            return True
        return False

    if needs_flip(U0):
        U0 = -U0

    U0 = np.round(U0.real, 14) + 1j*np.round(U0.imag, 14)
    return tuple(U0.flatten())


class SingleQubitRB:
    """
    Single-Qubit Randomized Benchmarking Class

    - Builds the 24 single-qubit Cliffords via BFS minimizing physical pulses (Z cost 0).
    - Decomposes a random Clifford sequence to native gates.
    - Recovery default: exact inverse of the *expanded* gate list (so final frame = 0).
    - Compiles to fixed-length arrays (phases, periods, angles) + valid_len + residual 
      (derived from the global frame).
    - Phase convention: +X=0, +Y=-π/2 via y_sign=-1 (set y_sign=+1 if your IQ wiring flips).

    Parameters
    ----------
    carrier_729_pitime : float
        Duration of a π pulse on the carrier transition (in seconds)
    allow_pi_gates : bool, optional
        Whether to allow π (180°) gates in addition to π/2 gates (default: True)
    max_m_for_padding : int, optional
        Maximum sequence length for pre-allocating fixed-size arrays (default: None)
    rng_seed : int, optional
        Random seed for reproducible sequence generation (default: None)
    y_sign : int, optional
        Sign convention for Y-axis phase: -1 for +Y=-π/2, +1 for +Y=+π/2 (default: -1)
    recovery_mode : str, optional
        Recovery gate method: 'exact_inverse' or 'clifford_inverse' (default: 'exact_inverse')
    """

    def __init__(self,
                 carrier_729_pitime: float,
                 allow_pi_gates: bool = True,
                 max_m_for_padding: Optional[int] = None,
                 rng_seed: Optional[int] = None,
                 y_sign: int = -1,
                 recovery_mode: str = "exact_inverse"):
        self.carrier_729_pitime = float(carrier_729_pitime)
        self.allow_pi_gates = bool(allow_pi_gates)
        self.y_sign = -1 if y_sign < 0 else 1
        self.randomized_benchmark_global_phase = 0.0
        self.rng = np.random.default_rng(rng_seed)
        self.recovery_mode = recovery_mode

        # Padded buffer sizing: conservative capacity per Clifford
        self.max_pulses_per_clifford = 2 if self.allow_pi_gates else 3
        self.fixed_total_slots = (None if max_m_for_padding is None
                                  # +1 for recovery
                                  else int(self.max_pulses_per_clifford * (max_m_for_padding + 1)))

        # Build 24 Cliffords and a key-index map
        self._cliffords, self._clifford_seq, self._key_to_idx = self._build_single_qubit_cliffords()

    def generate_Clifford_sequence(self, sequence_length: int) -> List[int]:
        """
        Generate a random sequence of Clifford gate indices.

        Parameters
        ----------
        sequence_length : int
            Number of Clifford gates in the sequence

        Returns
        -------
        List[int]
            List of random Clifford indices in range [0, 23]
        """
        return list(self.rng.integers(0, 24, size=int(sequence_length)))

    def decomposite_Clifford_sequence_into_gate_sequence(
        self, Cliffords_sequence: List[int]
    ) -> List[Tuple[str, int]]:
        """
        Expand the Clifford indices into a native gate list (with virtual Zs),
        then append the recovery gate(s).

        Parameters
        ----------
        Cliffords_sequence : List[int]
            Sequence of Clifford indices to decompose

        Returns
        -------
        List[Tuple[str, int]]
            List of (axis, angle_deg) tuples representing native gates

        Notes
        -----
        Recovery modes:
        - exact_inverse: Literal inverse of the expanded native list (reverse order, invert angles)
        - clifford_inverse: Use the inverse Clifford unitary (may leave a residual phase at end)
        """
        expanded: List[Tuple[str, int]] = []
        for idx in Cliffords_sequence:
            expanded += self._clifford_seq[idx]

        if self.recovery_mode == "exact_inverse":
            recovery: List[Tuple[str, int]] = []
            for (axis, ang) in reversed(expanded):
                if ang in (180, -180):
                    recovery.append((axis, 180))     # self-inverse
                else:
                    recovery.append((axis, -ang))
            return expanded + recovery
        elif self.recovery_mode == "clifford_inverse":
            # Old path: inverse Clifford unitary (not guaranteed to zero final frame)
            U_total = np.eye(2, dtype=np.complex128)
            for idx in Cliffords_sequence:
                U_total = self._cliffords[idx] @ U_total
            inv_idx = self._lookup_clifford_index(U_total.conj().T)
            return expanded + self._clifford_seq[inv_idx]
        else:
            raise ValueError(f"Unknown recovery mode: {self.recovery_mode}")

    def generate_pulse_phase_period_angle_sequence(
        self, gate_sequence: List[Tuple[str, int]]
    ) -> Tuple[List[float], List[float], List[float], int, float]:
        """
        Convert the gate list (with Z virtual) into pulses (X/Y only).

        Parameters
        ----------
        gate_sequence : List[Tuple[str, int]]
            List of (axis, angle_deg) tuples

        Returns
        -------
        phases : List[float]
            Pulse phases in radians
        periods : List[float]
            Pulse durations in seconds
        angles : List[float]
            Pulse rotation angles in radians
        valid_len : int
            Number of actual pulses (excluding padding)
        residual : float
            Residual Z-frame phase in radians (should be ~0 for exact_inverse)
        """
        phases: List[float] = []
        periods: List[float] = []
        angles: List[float] = []

        # Reset frame at the start of compilation
        self.randomized_benchmark_global_phase = 0.0

        for (axis, angle_deg) in gate_sequence:
            axis = axis.lower()
            if axis == 'z':
                # Virtual Z: update the global frame directly (no emitted pulse)
                self.randomized_benchmark_global_phase = wrap_2pi(
                    self.randomized_benchmark_global_phase +
                    (np.pi/2) * (angle_deg // 90)
                )
                continue

            # Physical X/Y pulse: use current frame for the phase
            phase, period = self.insert_Ri_gate(axis, angle_deg)
            if period > 0.0:
                phases.append(wrap_2pi(phase))
                periods.append(float(period))
                angles.append(np.pi/2 if abs(angle_deg) == 90 else np.pi)

        valid_len = len(periods)

        # The residual is whatever the global frame ended up being; 0 if exact reverse
        residual = wrap_2pi(self.randomized_benchmark_global_phase)

        if self.fixed_total_slots is None:
            return phases, periods, angles, valid_len, residual

        if valid_len > self.fixed_total_slots:
            raise ValueError(
                f"Pulse count {valid_len} exceeds fixed_total_slots {self.fixed_total_slots}")

        pad = self.fixed_total_slots - valid_len
        phases_out = phases + [0.0]*pad
        periods_out = periods + [0.0]*pad
        angles_out = angles + [0.0]*pad
        return phases_out, periods_out, angles_out, valid_len, residual

    def insert_Ri_gate(self, gate_axis: str, gate_angle: int) -> Tuple[float, float]:
        """
        Translate one X/Y/Z gate into a physical pulse (X/Y) or virtual Z (phase frame update).

        Parameters
        ----------
        gate_axis : str
            Gate axis ('x', 'y', or 'z')
        gate_angle : int
            Gate angle in degrees (±90 or 180)

        Returns
        -------
        phase : float
            Pulse phase in radians
        period : float
            Pulse duration in seconds (0 for virtual Z gates)
        """
        axis = gate_axis.lower()
        if axis not in ('x', 'y', 'z'):
            raise ValueError(f"Unknown axis: {gate_axis}")
        if axis == 'z':
            return 0.0, 0.0   # virtual (no pulse)

        if gate_angle % 90 != 0 or abs(gate_angle) not in (90, 180):
            raise ValueError(f"Unsupported angle: {gate_angle}")

        # normalize 180 to +180 (self-inverse)
        if abs(gate_angle) == 180:
            gate_angle = 180

        period = self.carrier_729_pitime if gate_angle == 180 else self.carrier_729_pitime / 2.0
        phase = self.randomized_benchmark_global_phase  # use current global frame

        if axis == 'x':
            if gate_angle == +90:
                phase += 0.0
            elif gate_angle == -90:
                phase += np.pi
            elif gate_angle == 180:
                phase += 0.0
        elif axis == 'y':
            if gate_angle == +90:
                phase += self.y_sign*(+np.pi/2)
            elif gate_angle == -90:
                phase += self.y_sign*(-np.pi/2)
            elif gate_angle == 180:
                phase += self.y_sign*(+np.pi/2)

        return wrap_2pi(phase), period

    def _build_single_qubit_cliffords(self):
        """
        Build the 24 single-qubit Clifford gates using BFS with Z cost 0.

        Returns
        -------
        cliffords : List[np.ndarray]
            List of 24 Clifford unitary matrices
        clifford_seq : List[List[Tuple[str, int]]]
            Decomposition of each Clifford into native gates
        key_to_idx : dict
            Mapping from canonical key to Clifford index
        """
        I = np.eye(2, dtype=np.complex128)
        # Physical pulses
        gens_phys = [('x', +90), ('x', -90), ('y', +90), ('y', -90)]
        if self.allow_pi_gates:
            gens_phys += [('x', 180), ('y', 180)]
        # Virtual Zs
        gens_virt = [('z', +90), ('z', -90), ('z', 180)]

        U_g = {g: R_axis_angle(*g) for g in (gens_phys + gens_virt)}

        unitary = {canonical_key(I): I}
        seqs = {canonical_key(I): []}
        cost = {canonical_key(I): 0}   # count physical pulses only
        q = deque([canonical_key(I)])

        while q and len(unitary) < 24:
            k = q.popleft()
            U = unitary[k]
            seq = seqs[k]
            base = cost[k]
            # try Z first (cost 0), then physical (cost 1)
            for g in gens_virt + gens_phys:
                U2 = U_g[g] @ U
                k2 = canonical_key(U2)
                c2 = base + (0 if g in gens_virt else 1)
                if k2 not in unitary or c2 < cost[k2]:
                    unitary[k2] = U2
                    seqs[k2] = seq + [g]
                    cost[k2] = c2
                    q.append(k2)
                if len(unitary) >= 24:
                    break

        # Compress consecutive Zs
        def compress(seq):
            out = []
            zsum = 0

            def flush():
                nonlocal zsum
                zsum = ((zsum + 180) % 360) - 180
                if zsum != 0:
                    out.append(('z', int(zsum)))
                zsum = 0
            for a, ang in seq:
                if a == 'z':
                    zsum += ang
                else:
                    flush()
                    out.append((a, ang))
            flush()
            return out

        items = []
        for k, U in unitary.items():
            items.append((k, U, compress(seqs[k])))

        # Prefer fewest physical pulses, then shorter total length
        items.sort(key=lambda x: (sum(1 for a, _ in x[2] if a in ('x', 'y')),
                                  len(x[2])))
        items = items[:24]

        cliffords = [it[1] for it in items]
        clifford_seq = [it[2] for it in items]
        key_to_idx = {canonical_key(U): i for i, U in enumerate(cliffords)}
        return cliffords, clifford_seq, key_to_idx

    def _lookup_clifford_index(self, U: np.ndarray) -> int:
        """
        Look up the index of a Clifford unitary matrix.

        Parameters
        ----------
        U : np.ndarray
            2x2 unitary matrix

        Returns
        -------
        int
            Index of the matching Clifford (0-23)
        """
        k = canonical_key(U)
        if k in self._key_to_idx:
            return self._key_to_idx[k]
        # conservative fallback (should almost never happen)
        best_i, best_err = 0, float('inf')
        for i, Uref in enumerate(self._cliffords):
            err = np.linalg.norm(np.array(k) - np.array(canonical_key(Uref)))
            if err < best_err:
                best_err, best_i = err, i
        return best_i

    def __repr__(self):
        return (f"SingleQubitRB(carrier_729_pitime={self.carrier_729_pitime:.2e}s, "
                f"allow_pi_gates={self.allow_pi_gates}, "
                f"recovery_mode='{self.recovery_mode}', "
                f"y_sign={self.y_sign})")
