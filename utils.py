import paramiko
import subprocess
import re
import time

IP_REGEX = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"

class Router():
    def __init__(self,ip,user,password):
        self.ip = ip
        self.user = user
        self.password = password
        self.is_connected = True
        try:
            self.hostname = self.get_hostname()
        except:
            self.is_connected = False
    def make_connection(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            ssh.connect(hostname = self.ip,username=self.user,password=self.password,timeout=0.5,allow_agent=False,look_for_keys=False)
            return ssh
        except Exception as e:
            print(e)
            return None
    def execute_command(self,command):

        if not self.is_connected:
            raise Exception("No se ha establecido conexión")

        ssh = self.make_connection()
        _,stdout,stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        ssh.close()

        if error:
            raise Exception(error)
        return output.replace("\r","")
    
    def execute_fast_commands(self,commands):
        if not self.is_connected:
            raise Exception("No se ha establecido conexión")
        ssh = self.make_connection()
        shell = ssh.invoke_shell()
        for command in commands:
            shell.send(command)
            time.sleep(0.25)
        ssh.close()
        return

    def get_hostname(self):
        output = self.execute_command("show run | i hostname")
        return output[9:-1]
    def get_jump_connections(self,visited,for_visit):

        output = self.execute_command("sh ip arp")

        self.interfaces_ip = {}
        self.connections = []

        for line in output.split("\n")[1:]:
            ip = re.findall(IP_REGEX,line)
            if not ip:
                continue
            ip = ip[0]

            if "-" in line:
                self.interfaces_ip[ip] = self.hostname
                try: for_visit.remove(ip) 
                except: pass
                visited.append(ip)
            else:
                if ip in visited: continue
                self.connections.append(ip)
                for_visit.append(ip)
        return visited,for_visit
    def create_user(self,username,password):
        # LIMPIAMOS EL CACHE
        print("Creando usuario....")
        self.execute_fast_commands(["clear arp-cache\n","conf t\n",f"username {username} privilege 15 password {password}\n"])




def get_gateway():
    p = subprocess.Popen(["ip r"], stdout=subprocess.PIPE, shell=True)
    output = str(p.stdout.read())
    ips = re.findall(IP_REGEX,output)
    return ips[0]
