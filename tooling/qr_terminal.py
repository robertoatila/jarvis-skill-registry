#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pure Python 3.12 Standard Library QR Code Generator (Zero External Dependencies)
Encodes URLs and text into ISO/IEC 18004 compliant QR Code matrices (Versions 1-6).
Renders to Unicode terminal half-blocks, ASCII, or SVG.
"""

from __future__ import annotations
import sys
from typing import List, Tuple, Optional

# Galois Field GF(2^8) math with primitive polynomial 0x11D (285)
GF_EXP = [0] * 512
GF_LOG = [0] * 256

def _init_gf():
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_EXP[i + 255] = x
        GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    GF_LOG[0] = 0

_init_gf()

def gf_mul(x: int, y: int) -> int:
    if x == 0 or y == 0:
        return 0
    return GF_EXP[GF_LOG[x] + GF_LOG[y]]

def rs_generator_poly(ec_len: int) -> List[int]:
    g = [1]
    for i in range(ec_len):
        # Multiply g by (x - 2^i)
        root = GF_EXP[i]
        next_g = [0] * (len(g) + 1)
        for j in range(len(g)):
            next_g[j] ^= gf_mul(g[j], root)
            next_g[j + 1] ^= g[j]
        g = next_g
    return g

def rs_encode(data: List[int], ec_len: int) -> List[int]:
    gen = rs_generator_poly(ec_len)
    # Pad data with ec_len zeros
    msg = list(data) + [0] * ec_len
    for i in range(len(data)):
        lead = msg[i]
        if lead != 0:
            for j in range(len(gen)):
                msg[i + j] ^= gf_mul(gen[j], lead)
    return msg[len(data):]

# Version capacities for Byte mode with Medium ECC:
# Format: (version, total_codewords, ec_codewords_per_block, num_blocks_g1, data_cw_g1, num_blocks_g2, data_cw_g2)
# We support Version 1 to 6 (sufficient for URLs up to 134 bytes)
QR_SPECS_M = {
    1: (1, 26, 10, 1, 16, 0, 0),
    2: (2, 44, 16, 1, 28, 0, 0),
    3: (3, 70, 26, 1, 44, 0, 0),
    4: (4, 100, 18, 2, 32, 0, 0),  # 2 blocks of 32 data, 18 ec = 64 data bytes
    5: (5, 134, 24, 2, 43, 0, 0),  # 2 blocks of 43 data, 24 ec = 86 data bytes
    6: (6, 172, 16, 4, 27, 0, 0),  # 4 blocks of 27 data, 16 ec = 108 data bytes
}

# Alignment pattern centers per version
ALIGNMENT_CENTERS = {
    1: [],
    2: [6, 18],
    3: [6, 22],
    4: [6, 26],
    5: [6, 30],
    6: [6, 34],
}

# Format info for Medium ECC (mask pattern 0: (row + col) % 2 == 0)
# ECC level M = 00 binary. Mask 000 = 000.
# 15-bit format string for M, mask 0: 0b101010000010010 XOR 0b101010000010010 = 0
FORMAT_BITS_M_MASK0 = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]
# Precomputed format info with mask 101010000010010 applied for mask 0
FORMAT_INFO_M_MASK0 = 0x5412 ^ 0x5412  # = 0x0000, wait, BCH code:
# For ECC M (00) and Mask 0 (000) -> 00 000 = 0
# Generator poly for format info: 10100110111
# Format bits (unmasked) = 00000 0000000000
# Mask pattern 101010000010010 -> Final bits = 101010000010010 (0x5412)
FORMAT_MASK_BITS = 0x5412

def get_format_bits(ec_level_bits: int, mask: int) -> int:
    data = (ec_level_bits << 3) | mask
    rem = data << 10
    gen = 0x537
    for i in range(14, 9, -1):
        if rem & (1 << i):
            rem ^= gen << (i - 10)
    bits = (data << 10) | rem
    return bits ^ FORMAT_MASK_BITS


class QRCode:
    def __init__(self, data: str):
        self.raw_data = data.encode('utf-8')
        self.version = self._select_version(len(self.raw_data))
        self.size = 17 + 4 * self.version
        self.matrix = [[None for _ in range(self.size)] for _ in range(self.size)]
        self._build()

    def _select_version(self, data_len: int) -> int:
        for v in range(1, 7):
            spec = QR_SPECS_M[v]
            total_data_cw = (spec[3] * spec[4]) + (spec[5] * spec[6])
            # Byte mode header: 4 bits mode + 8 bits length (v1-9) = 12 bits = 1.5 bytes
            max_bytes = total_data_cw - 2
            if data_len <= max_bytes:
                return v
        raise ValueError(f"Data length {data_len} exceeds max supported (108 bytes)")

    def _build(self):
        self._add_finders()
        self._add_alignment()
        self._add_timing()
        self._reserve_format_areas()
        self._place_data()
        self._apply_mask_and_format()

    def _set_module(self, r: int, c: int, val: int):
        if 0 <= r < self.size and 0 <= c < self.size:
            self.matrix[r][c] = 1 if val else 0

    def _add_finders(self):
        corners = [(0, 0), (0, self.size - 7), (self.size - 7, 0)]
        for top, left in corners:
            for r in range(7):
                for c in range(7):
                    if r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4):
                        self.matrix[top + r][left + c] = 1
                    else:
                        self.matrix[top + r][left + c] = 0
            # Separators
            for i in range(8):
                if top == 0 and left == 0:
                    self._set_module(7, i, 0)
                    self._set_module(i, 7, 0)
                elif top == 0:
                    self._set_module(7, left - 1 + i, 0)
                    self._set_module(i, left - 1, 0)
                else:
                    self._set_module(top - 1, i, 0)
                    self._set_module(top - 1 + i, 7, 0)

    def _add_alignment(self):
        centers = ALIGNMENT_CENTERS[self.version]
        for r_c in centers:
            for c_c in centers:
                # Don't place over finders
                if (r_c <= 8 and c_c <= 8) or (r_c <= 8 and c_c >= self.size - 8) or (r_c >= self.size - 8 and c_c <= 8):
                    continue
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                            self.matrix[r_c + dr][c_c + dc] = 1
                        else:
                            self.matrix[r_c + dr][c_c + dc] = 0

    def _add_timing(self):
        for i in range(8, self.size - 8):
            val = 1 if (i % 2 == 0) else 0
            if self.matrix[6][i] is None:
                self.matrix[6][i] = val
            if self.matrix[i][6] is None:
                self.matrix[i][6] = val
        # Dark module
        self.matrix[4 * self.version + 9][8] = 1

    def _reserve_format_areas(self):
        for i in range(9):
            if self.matrix[8][i] is None:
                self.matrix[8][i] = 0
            if self.matrix[i][8] is None:
                self.matrix[i][8] = 0
        for i in range(8):
            if self.matrix[8][self.size - 1 - i] is None:
                self.matrix[8][self.size - 1 - i] = 0
            if self.matrix[self.size - 1 - i][8] is None:
                self.matrix[self.size - 1 - i][8] = 0

    def _encode_data_bits(self) -> List[int]:
        spec = QR_SPECS_M[self.version]
        total_data_cw = (spec[3] * spec[4]) + (spec[5] * spec[6])

        # Bit stream
        bits = []
        # Mode indicator: Byte = 0100
        bits.extend([0, 1, 0, 0])
        # Character count: 8 bits for Byte mode v1-9
        data_len = len(self.raw_data)
        for b in range(7, -1, -1):
            bits.append((data_len >> b) & 1)
        # Data bytes
        for byte in self.raw_data:
            for b in range(7, -1, -1):
                bits.append((byte >> b) & 1)

        # Terminator: up to 4 zero bits
        rem_cap_bits = total_data_cw * 8 - len(bits)
        term_bits = min(4, rem_cap_bits)
        bits.extend([0] * term_bits)

        # Pad to byte boundary
        while len(bits) % 8 != 0:
            bits.append(0)

        # Convert to codewords
        codewords = []
        for i in range(0, len(bits), 8):
            cw = 0
            for bit in bits[i:i+8]:
                cw = (cw << 1) | bit
            codewords.append(cw)

        # Pad bytes 0xEC and 0x11
        pad_bytes = [0xEC, 0x11]
        pad_idx = 0
        while len(codewords) < total_data_cw:
            codewords.append(pad_bytes[pad_idx % 2])
            pad_idx += 1

        # Break into blocks and compute RS error correction
        ec_per_block = spec[2]
        num_blocks_g1 = spec[3]
        data_cw_g1 = spec[4]
        num_blocks_g2 = spec[5]
        data_cw_g2 = spec[6]

        blocks_data = []
        blocks_ec = []
        offset = 0

        for _ in range(num_blocks_g1):
            blk = codewords[offset:offset + data_cw_g1]
            blocks_data.append(blk)
            blocks_ec.append(rs_encode(blk, ec_per_block))
            offset += data_cw_g1

        for _ in range(num_blocks_g2):
            blk = codewords[offset:offset + data_cw_g2]
            blocks_data.append(blk)
            blocks_ec.append(rs_encode(blk, ec_per_block))
            offset += data_cw_g2

        # Interleave data codewords
        final_cw = []
        max_data_len = max(data_cw_g1, data_cw_g2 if num_blocks_g2 else 0)
        for i in range(max_data_len):
            for blk in blocks_data:
                if i < len(blk):
                    final_cw.append(blk[i])

        # Interleave EC codewords
        for i in range(ec_per_block):
            for blk in blocks_ec:
                final_cw.append(blk[i])

        # Convert back to bit array
        final_bits = []
        for cw in final_cw:
            for b in range(7, -1, -1):
                final_bits.append((cw >> b) & 1)

        # Add remainder bits if any
        remainder_bits_by_version = {1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7}
        final_bits.extend([0] * remainder_bits_by_version.get(self.version, 0))
        return final_bits

    def _place_data(self):
        bits = self._encode_data_bits()
        bit_idx = 0
        row = self.size - 1
        col = self.size - 1
        upward = True

        while col > 0:
            if col == 6:  # Skip vertical timing column
                col -= 1
            for _ in range(self.size):
                for dc in (0, -1):
                    c = col + dc
                    r = row
                    if self.matrix[r][c] is None:
                        val = bits[bit_idx] if bit_idx < len(bits) else 0
                        self.matrix[r][c] = val
                        bit_idx += 1
                row = row - 1 if upward else row + 1
            row = 0 if upward else self.size - 1
            upward = not upward
            col -= 2

    def _apply_mask_and_format(self):
        # Mask 0: (row + col) % 2 == 0
        # We apply mask 0 to all data modules
        # Format for ECC M (00) and Mask 0 (000)
        format_val = get_format_bits(0, 0)
        fmt_bits = [(format_val >> (14 - i)) & 1 for i in range(15)]

        # Apply mask 0 to data cells
        # Data cells are those not in finders, timing, alignment, or format areas
        # We know format areas and patterns:
        for r in range(self.size):
            for c in range(self.size):
                # Check if it's a data cell
                if self._is_data_cell(r, c):
                    if (r + c) % 2 == 0:
                        self.matrix[r][c] ^= 1

        # Place format info
        # Around top-left
        self.matrix[8][0] = fmt_bits[0]
        self.matrix[8][1] = fmt_bits[1]
        self.matrix[8][2] = fmt_bits[2]
        self.matrix[8][3] = fmt_bits[3]
        self.matrix[8][4] = fmt_bits[4]
        self.matrix[8][5] = fmt_bits[5]
        self.matrix[8][7] = fmt_bits[6]
        self.matrix[8][8] = fmt_bits[7]
        self.matrix[7][8] = fmt_bits[8]
        self.matrix[5][8] = fmt_bits[9]
        self.matrix[4][8] = fmt_bits[10]
        self.matrix[3][8] = fmt_bits[11]
        self.matrix[2][8] = fmt_bits[12]
        self.matrix[1][8] = fmt_bits[13]
        self.matrix[0][8] = fmt_bits[14]

        # Split format bits around other finders
        for i in range(8):
            self.matrix[8][self.size - 1 - i] = fmt_bits[i]
        for i in range(7):
            self.matrix[self.size - 7 + i][8] = fmt_bits[8 + i]

    def _is_data_cell(self, r: int, c: int) -> bool:
        # Top-left finder & separator
        if r <= 8 and c <= 8:
            return False
        # Top-right finder & separator
        if r <= 8 and c >= self.size - 8:
            return False
        # Bottom-left finder & separator
        if r >= self.size - 8 and c <= 8:
            return False
        # Timing patterns
        if r == 6 or c == 6:
            return False
        # Alignment patterns
        centers = ALIGNMENT_CENTERS[self.version]
        for r_c in centers:
            for c_c in centers:
                if (r_c <= 8 and c_c <= 8) or (r_c <= 8 and c_c >= self.size - 8) or (r_c >= self.size - 8 and c_c <= 8):
                    continue
                if abs(r - r_c) <= 2 and abs(c - c_c) <= 2:
                    return False
        return True

    def to_ascii(self, border: int = 2) -> str:
        """Render the QR code using standard ASCII characters (## and space) for cp1252/legacy consoles."""
        total_size = self.size + 2 * border
        padded = [[0 for _ in range(total_size)] for _ in range(total_size)]
        for r in range(self.size):
            for c in range(self.size):
                padded[r + border][c + border] = self.matrix[r][c]

        lines = []
        for r in range(total_size):
            line = []
            for c in range(total_size):
                line.append('##' if padded[r][c] else '  ')
            lines.append(''.join(line))
        return '\n'.join(lines)

    def to_terminal(self, border: int = 2) -> str:
        """Render the QR code using Unicode half-block characters (2 pixels per line)."""
        total_size = self.size + 2 * border
        padded = [[0 for _ in range(total_size)] for _ in range(total_size)]
        for r in range(self.size):
            for c in range(self.size):
                padded[r + border][c + border] = self.matrix[r][c]

        lines = []
        for r in range(0, total_size, 2):
            row_top = padded[r]
            row_bot = padded[r + 1] if (r + 1 < total_size) else [0] * total_size
            line = []
            for c in range(total_size):
                top = row_top[c]
                bot = row_bot[c]
                if top and bot:
                    line.append('█')
                elif top and not bot:
                    line.append('▀')
                elif not top and bot:
                    line.append('▄')
                else:
                    line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)

    def to_svg(self, box_size: int = 10, border: int = 4) -> str:
        """Render to an SVG string."""
        total_dim = (self.size + 2 * border) * box_size
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_dim} {total_dim}" width="{total_dim}" height="{total_dim}">',
            f'<rect width="100%" height="100%" fill="#ffffff"/>',
            f'<path d="'
        ]
        path_parts = []
        for r in range(self.size):
            for c in range(self.size):
                if self.matrix[r][c]:
                    x = (c + border) * box_size
                    y = (r + border) * box_size
                    path_parts.append(f"M{x},{y}h{box_size}v{box_size}h-{box_size}z")
        svg.append(' '.join(path_parts))
        svg.append('" fill="#000000"/>')
        svg.append('</svg>')
        return '\n'.join(svg)


def generate_qr_terminal(text: str) -> str:
    """Generate a Unicode QR Code string, falling back to ASCII if encoding fails."""
    qr = QRCode(text)
    try:
        return qr.to_terminal()
    except Exception:
        return qr.to_ascii()

def generate_qr_ascii(text: str) -> str:
    qr = QRCode(text)
    return qr.to_ascii()

def generate_qr_svg(text: str) -> str:
    """Generate SVG XML string of the QR Code."""
    qr = QRCode(text)
    return qr.to_svg()


def print_qr(text: str, stream=None):
    if stream is None:
        stream = sys.stdout
    if hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass
    qr = QRCode(text)
    try:
        stream.write(qr.to_terminal() + '\n')
        if hasattr(stream, 'flush'):
            stream.flush()
    except (UnicodeEncodeError, Exception):
        stream.write(qr.to_ascii() + '\n')
        if hasattr(stream, 'flush'):
            stream.flush()


if __name__ == '__main__':
    demo_url = "http://192.168.1.50:8899/?token=fedcba9876543210"
    print("Testing QRCode generation for:", demo_url)
    print_qr(demo_url)

