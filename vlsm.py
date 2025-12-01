import math
import sys


class Block():
    def __init__(
            self, val=0, max_val=255, is_network=False, transition=False, id=None
                ) -> None:
        self.val:int = val; self.max_val:int = max_val
        self.is_network:bool = is_network; self.transition:bool = transition
        self.id = id
        self.jump_val = 0

    def __str__(self) -> str:
        return str(self.val)


    def safe_add(self, nums:int) -> None:
        if self.is_network:
            return

        elif self.transition:
            if (self.val + nums) > self.max_val:
                raise Exception(
                    f'\n-LIMIT REACHED: Too many hosts to subnet-\
                    \nSubnet requirement: {self.val + nums}\
                    \nMAX number of hosts: {self.max_val}'
                    )
            self.val += nums



class IP_Address():
    def __init__(self, num_list, extra=False) -> None:
        self.subnet = int(num_list[4])
        split_number = self.subnet % 8
        split_index = self.subnet // 8
        binary_split = int('1' * split_number + '0' * (8 - split_number), 2)

        block_list: list[Block] = []
        for i in range(4):
            if i < split_index:
                block_list.append(
                Block(val=num_list[i], max_val=num_list[i], is_network=True, id=i)
                )
            elif i == split_index:
                block_list.append(
                Block(val=num_list[i], max_val=((256-binary_split)+num_list[i]), transition=True, id=i)
                )
            else:
                block_list.append(Block(val=num_list[i], id=i))

        self.block_list = list(reversed(block_list))
        self.ip_list: list[str] = []
        self.info_list: list = []
        self.extra_info: bool = extra


    def add_numbers(self, nums:int) -> None:
        exp: int = math.ceil(math.log2(nums)); subnet_mask: int = 32-exp; number: int = 2**exp
        jump_value: int = 0
        binary: str = '1'*subnet_mask + '0'*(32-subnet_mask)
        sm_value: int = int(binary[24:],2)
        previous: str = f'\
{self.block_list[3]}.{self.block_list[2]}.{self.block_list[1]}.{self.block_list[0]}/{subnet_mask}, SM: {sm_value}, WM: {255-sm_value}'

        if self.extra_info:
            self.info_list.append(number - nums)

        for ip_Block in self.block_list:
            max_value = ip_Block.max_val + 1  
            if not ip_Block.is_network and not ip_Block.transition:
                ip_Block.val += number % max_value
                if ip_Block.val >= max_value:
                    ip_Block.val %= max_value
                    jump_value += 1

                jump_value += number // max_value
            #8bit case
            elif not ip_Block.is_network and ip_Block.transition and ip_Block.id == 3:
               ip_Block.safe_add(number % max_value)
            else:
                ip_Block.safe_add(jump_value)
                jump_value = ip_Block.jump_val

        self.ip_list.append(previous)


    def get_ips(self):
        return self.ip_list



def main() -> None:
    input_ipa: str = ''; requirements: list[str] = []
    extra: bool|str|None = None
    
    inpt_file = get_file()
    if inpt_file is not None:
        input_ipa, requirements, extra = read_requirements(inpt_file)
    else:
        input_ipa = input('Enter IPv4 Address: ')
        print('Enter requirement in format, Name|Number')
        while True:
            prompt = input('(x to stop): ')
            if prompt.lower() == 'x':
                break
            requirements.append(prompt)

    address_blocks, req_numbers_list, names_list = process_input(input_ipa, requirements)

    ip_address = IP_Address(address_blocks, extra)
    for i in req_numbers_list: ip_address.add_numbers(i)
    
    output_ipas(ip_address, names=names_list, filename='output.txt')


def read_requirements(filename:str) -> tuple[str, list[str], bool|str]:
    input_ip: str = ''; extra_info:bool | str = False
    with open(filename, 'r') as file:
        definition_line = file.readline()
        try:
            input_ip , extra_info = definition_line.split('|')
            statement = extra_info.lower().strip()
        except ValueError:
            input_ip = definition_line
        else:
            if statement == 'true':
                extra_info = True
            elif statement != 'false':
                raise Exception('Not a valid statement for extra info')
        finally:
            requirements: list[str] = file.readlines()
            requirements = [req.rstrip('\n') for req in requirements]

    return input_ip, requirements, extra_info


def process_input(input_ipa, requirements:list[str]) -> tuple[list[str], list[int], list[str]]:
    address_blocks = input_ipa.split('.')
    last_octate, mask = address_blocks.pop().split('/')
    address_blocks.append(last_octate); address_blocks.append(mask)

    address_blocks = [int(i) for i in address_blocks]

    numbers_list: list[int] = []; names_list: list[str] = []
    for entry in requirements:
        name, number = entry.split('|')
        names_list.append(name); numbers_list.append(int(number))

    return address_blocks, numbers_list, names_list


def get_file() -> str | None:
    arg: list[str] = sys.argv
    if len(arg) > 2:
        sys.exit('Give only maximum of 2 input files')

    elif len(arg) == 2:
        if arg[1].endswith('.txt') or arg[1].endswith('.text'):
            return arg[1]
        else:
            sys.exit('Enter a valid text file')

    else:
        return None
    

def output_ipas(ipa:IP_Address, names:list[str], filename:str) -> None:
    output = []
    for i, ip in enumerate(ipa.get_ips()):
        output.append(f'{ip}, {names[i]}')
        if ipa.extra_info:
            output.append(f' | Number of Wasted IPs: {ipa.info_list[i]}')
        else:
            output.append(' ')

    for i in range(len(output)): print(output[i])
    with open(f'{filename}', 'w') as file:
        for i in range(len(output)): file.write(f'{output[i]}\n')
    

if __name__ == '__main__':
    '''
    --Test inputs--
    '''
    # ip_test1 = '192.248.0.0/23'
    # req_test3 = [
    #     'Computing|9','HR|5',
    #     'Finance|5','Business|6',
    #     'NCUK|5', 'WAN1|4','WAN2|4'
    #     ]
    # ip_test2 = '192.192.128.0/19'
    # req_test2 = ['Computing|503','Business|203','Law|43',
    #              'HR|43','Marketing|43','Finance|43',
    #              'Maintenance|5','WAN1|4', 'WAN2|4'
    # ]
    # ip_test3 = '192.168.192.0/19'
    # req_test3 = ['Computing|253','Business|123','Law|53',
    #              'Marketing|23','Finance|7',
    #              'HR|7','Cyber|7', 'WAN|4'
    # ]

    main()