import subprocess
import paramiko
import re
import time
def sendCommand(hostname,commands):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.connect(hostname=hostname,username='admin',password='admin',timeout=0.5)
    shell = ssh.invoke_shell()
    for command in commands:
        shell.send(command)
        time.sleep(0.25)
    ssh.close()
    return

def get_gateway():
    p = subprocess.Popen(["ip r"], stdout=subprocess.PIPE, shell=True)
    output = str(p.stdout.read())
    ips = re.findall(IP_REGEX,output)
    return ips[0]

router = ["conf t\n","ip route 10.0.5.0 255.255.255.0 10.0.2.253\n"]


routerRIP = ["conf t\n","router rip\n","version 2\n","network 10.0.0.0\n","redistribute ospf 1\n","default-information originate\n"]



routerOSPF = ["conf t\n","router ospf 1\n","redistribute static subnets\n","redistribute rip subnets\n","network 10.0.4.0 0.0.0.255 area 0\n","default-information originate\n"]

IP_REGEX = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"

gateway =  get_gateway()


#devices = {'R1':'prompt': 'R1#','ip':gateway}

def main():
    username = input('Usuario: ')
    password = input('Pass: ')

    sendCommand(gateway, router)
    print('Conf Static')
    print(gateway)

    sendCommand(gateway, routerRIP)
    print('Conf RIP')
    print(gateway)

    sendCommand(gateway, routerOSPF)
    print('Conf ospf')
    print(gateway)



if  __name__ =='__main__':
    main()
