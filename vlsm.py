#!/usr/bin/env python3
"""
New vlsm.py

Rewritten VLSM tool using Python's ipaddress module and tabulate for output.
"""

from __future__ import annotations
import sys
import ipaddress
from typing import List, Tuple, Optional
from tabulate import tabulate


def main() -> None:
    # parse args (simple: optional single input file)
    args = sys.argv[1:]
    if len(args) > 1:
        sys.exit("Usage: vlsm.py <optional_input_file.txt>")

    if len(args) == 1:
        infile = args[0]
        if not (infile.endswith(".txt") or infile.endswith(".text")):
            sys.exit("Input file must be a .txt or .text file")
        base_str, requirements, extra_info = read_requirements_from_file(infile)
    else:
        base_str, requirements, extra_info = interactive_input()

    # Validate base network
    try:
        base_network = ipaddress.IPv4Network(base_str.strip(), strict=False)
    except Exception as e:
        sys.exit(f"Invalid base network: {e}")

    if not requirements:
        sys.exit("No requirements provided. Exiting.")

    # Validate requirement entries
    for name, num in requirements:
        if num < 1:
            sys.exit(f"Requirement for '{name}' must be >= 1 usable host.")

    # Allocate
    try:
        allocations = allocate_vlsm(base_network, requirements)
    except ValueError as e:
        sys.exit(f"Allocation error: {e}")

    # Prepare table headers
    headers = ["Name", "Network", "Broadcast", "Usable Range", "Subnet Mask", "Wildcard Mask"]
    if extra_info:
        headers.append("Wasted IPs")

    # Prepare rows in the order allocated (descending-by-size)
    rows = []
    for name, required, net, wasted in allocations:
        rows.append(format_allocation_row(name, required, net, wasted, extra_info))

    # Tabulate using grid style
    table_text = tabulate(rows, headers=headers, tablefmt="grid")

    # Print to CLI
    print(table_text)

    # Also write the table text to output.txt
    with open("output.txt", "w") as out_f:
        out_f.write(table_text + "\n")

    # Exit normally
    return


def prefix_for_usable(required_usable: int) -> int:
    """
    Given required usable hosts, return the smallest prefix length that
    provides >= required_usable usable hosts.

    Uses typical usable-host calculation: usable = 2^host_bits - 2 (so /30 => 2 usable).
    We avoid /31 and /32 as usable-host subnets (they have 0 usable hosts under the
    traditional allocation approach).
    """
    if required_usable <= 0:
        raise ValueError("Required usable hosts must be >= 1")

    # host_bits ranges from 2 (for /30) up to 30 (for /2)
    for host_bits in range(2, 31):  # host_bits = 32 - prefixlen
        usable = (1 << host_bits) - 2
        if usable >= required_usable:
            return 32 - host_bits

    raise ValueError("Requirement too large to fit in IPv4")


def read_requirements_from_file(filename: str) -> Tuple[str, List[Tuple[str, int]], bool]:
    """
    Read file input. Expected format:
      - First line: <base_network> or <base_network>|True|False  (extra info boolean optional)
      - Following lines: Name|Number  (Number is usable hosts)

    Returns:
      (base_network_str, [(name, usable_hosts), ...], extra_info_flag)
    """
    extra_info = False
    requirements: List[Tuple[str, int]] = []

    with open(filename, "r") as fh:
        first = fh.readline().strip()
        if "|" in first:
            parts = first.split("|", 1)
            base = parts[0].strip()
            statement = parts[1].strip().lower()
            if statement == "true":
                extra_info = True
            elif statement == "false" or statement == "":
                extra_info = False
            else:
                raise ValueError("Invalid extra-info flag in file (use True or False)")
        else:
            base = first

        # read the rest
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if "|" not in line:
                raise ValueError(f"Invalid requirement line (expected 'Name|Number'): {line}")
            name, num = line.split("|", 1)
            requirements.append((name.strip(), int(num.strip())))

    return base, requirements, extra_info


def interactive_input() -> Tuple[str, List[Tuple[str, int]], bool]:
    """
    Prompt the user for base network and requirements interactively.
    """
    base = input("Enter IPv4 network (e.g., 192.168.1.0/24): ").strip()
    print("Enter requirements in format: Name|Number (Number = usable hosts). Enter 'x' to stop.")
    reqs: List[Tuple[str, int]] = []
    while True:
        line = input("(x to stop): ").strip()
        if line.lower() == "x":
            break
        if "|" not in line:
            print("Invalid format. Use Name|Number.")
            continue
        name, num = line.split("|", 1)
        try:
            reqs.append((name.strip(), int(num.strip())))
        except ValueError:
            print("Number must be an integer.")
    return base, reqs, False


def next_aligned_network_start(current_int: int, prefixlen: int) -> int:
    """
    For a candidate current address (as int) and desired prefixlen,
    return the integer of the next network address that is aligned to that prefix
    and is >= current_int.

    Example:
      - prefixlen = 26 -> host_bits = 6 -> block_size = 64
      - If current_int falls in the middle of a /26 block, this will return the start of the next /26 block.
    """
    host_bits = 32 - prefixlen
    block_size = 1 << host_bits
    # aligned base for the current_int
    aligned = current_int & (~(block_size - 1))
    if aligned < current_int:
        aligned += block_size
    return aligned


def allocate_vlsm(base_network: ipaddress.IPv4Network,
                  requirements: List[Tuple[str, int]]) -> List[Tuple[str, int, ipaddress.IPv4Network, int]]:
    """
    Allocate subnets for requirements using VLSM.

    Returns a list of tuples:
      (name, required_usable, allocated_network, wasted_ips)
    where wasted_ips = allocated_usable - required_usable
    """
    # Attach original index so we can output in allocation order (we'll present sorted order allocations)
    reqs_with_index = [(name, required, idx) for idx, (name, required) in enumerate(requirements)]

    # Sort descending by required hosts (Option B)
    reqs_with_index.sort(key=lambda t: t[1], reverse=True)

    allocations = []
    current_int = int(base_network.network_address)

    for name, required_usable, orig_idx in reqs_with_index:
        prefixlen = prefix_for_usable(required_usable)
        # Find the next aligned network at this prefix >= current_int
        net_start_int = next_aligned_network_start(current_int, prefixlen)

        # Create the network object
        net = ipaddress.IPv4Network((net_start_int, prefixlen))
        # Ensure the allocated net fits inside the base network
        if net.network_address < base_network.network_address or net.broadcast_address > base_network.broadcast_address:
            raise ValueError(f"Not enough address space in base network to allocate '{name}' ({required_usable} hosts).")

        # compute allocated usable hosts for this net (special-case /31,/32)
        host_bits = 32 - net.prefixlen
        if host_bits >= 2:
            allocated_usable = (1 << host_bits) - 2
        else:
            allocated_usable = 0

        wasted = allocated_usable - required_usable if allocated_usable >= required_usable else 0

        allocations.append((name, required_usable, net, wasted))

        # move current_int to next IP after this allocated network
        current_int = int(net.broadcast_address) + 1
        # If we've run out of addresses for further allocations, further iterations will fail above.

    return allocations


def wildcard_from_netmask(netmask: ipaddress.IPv4Address) -> ipaddress.IPv4Address:
    """
    Compute wildcard mask (host bits set to 1), which is bitwise NOT of netmask.
    """
    nm_int = int(netmask)
    wild_int = (~nm_int) & 0xFFFFFFFF
    return ipaddress.IPv4Address(wild_int)


def format_allocation_row(name: str, required: int, net: ipaddress.IPv4Network, wasted: int, extra_info: bool) -> List[str]:
    """
    Prepare a display row for the tabular output. Columns:
      - Name
      - Network (with prefix)
      - Broadcast
      - Usable Host Range
      - Subnet Mask (dotted)
      - Wildcard Mask (dotted)
      - Wasted IPs (optional)
    """
    network_str = f"{net.network_address}/{net.prefixlen}"
    broadcast_str = str(net.broadcast_address)

    # usable host range:
    host_bits = 32 - net.prefixlen
    if host_bits >= 2:
        first_usable = ipaddress.IPv4Address(int(net.network_address) + 1)
        last_usable = ipaddress.IPv4Address(int(net.broadcast_address) - 1)
        usable_range = f"{first_usable} - {last_usable}"
    else:
        # /31 and /32: no usable hosts under classic approach
        usable_range = "N/A"

    subnet_mask = str(net.netmask)
    wildcard = str(wildcard_from_netmask(net.netmask))

    row = [name, network_str, broadcast_str, usable_range, subnet_mask, wildcard]
    if extra_info:
        row.append(str(wasted))
    return row


if __name__ == "__main__":
    main()
