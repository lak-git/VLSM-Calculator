# Python VLSM Subnetting Tool

## Overview
This project is a fully automated **Variable Length Subnet Masking (VLSM)** calculator built in Python.  
It accepts a base network and a list of subnet requirements (defined in usable hosts), then:

- Calculates optimal subnet sizes  
- Allocates subnets in descending order (true VLSM)  
- Computes network/broadcast addresses, usable ranges, masks, and wildcard masks  
- Displays results in the CLI (simple line format)  
- Exports a clean, tabulated report to **output.txt** using `tabulate`  

It is designed for networking students, practitioners, and anyone needing dependable programmatic VLSM planning. I made this tool for my CS Degree's first year's networking assignment.

---

## Features
- ✔ **VLSM allocation** by sorting requirements from largest → smallest  
- ✔ **Automatic subnet size calculation** from usable host counts  
- ✔ Outputs:
  - Network address  
  - Broadcast address  
  - Usable host range  
  - Subnet mask  
  - Wildcard mask  
  - (Optional) wasted IPs  
- ✔ **CLI-friendly output** (simple pipe-separated format)  
- ✔ **Formatted table output** saved to `output.txt` (tabulate grid format)  
- ✔ Error handling for invalid networks and overlapping allocations  
- ✔ Uses Python’s built-in `ipaddress` module for reliable subnet math  

---

## Installation & Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/lak-git/VLSM-Calculator.git
   cd VLSM-Calculator
   ```
2. **Install required Python packages**
    ```bash
    pip install -r requirements.txt
    ```
3. **Run the script**
    ```bash
    python vlsm.py
    ```

---

## Usage
1. When prompted, enter the **base network** (CIDR format), e.g.:
```bash
192.168.1.0/24
```
2. Enter the number of subnets you want to create.
3. For each subnet, provide:
    - Name/label
    - Required number of usable hosts
    - The tool automatically determines the correct subnet size.
4. The program will:
    - Print each subnet in this format:
```bash
Name | Network | Broadcast | Usable Range | Subnet Mask | Wildcard Mask |
```
    - Save a grid-formatted table into output.txt
Example CLI output:
```bash
Sales | 192.168.1.0 | 192.168.1.63 | 192.168.1.1 - 192.168.1.62 | 255.255.255.192 | 0.0.0.63 |
IT | 192.168.1.64 | 192.168.1.95 | 192.168.1.65 - 192.168.1.94 | 255.255.255.224 | 0.0.0.31 |
```

---

## License
This project is licensed under the MIT License.
