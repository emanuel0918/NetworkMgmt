import subprocess
import re
import paramiko
import time
from graphviz import Digraph

def ejecutar(ip,comandos):
    usuario = "admin"
    contrasenia = "admin"
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(hostname=ip,username=usuario,password=contrasenia,timeout=0.5)
    except Exception as e:
        #
        return None
    if len(comandos)>1:
        shell = ssh.invoke_shell()
        for commando in comandos:
            shell.send(commando)
            time.sleep(0.30)
        ssh.close()
        return
    else:
        stdin,stdout,stderr = ssh.exec_command(comandos[0])
        data = stdout.read().decode()
        ssh.close()
    return data
def main():
    rangosIp = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
    p = subprocess.Popen(["ip r"], stdout=subprocess.PIPE, shell=True)
    output = str(p.stdout.read())
    ips = re.findall(rangosIp,output)
    print("\n IP's en la topología:")
    for i in ips:
        print(i,"\n");
    #Nuestro gateway es la dirección más baja     
    gateway = ips[0]
    
    
    ip_examinada = []
    go = [gateway]
    t = time.time()
    nodos = {}
    identificadores = {}
    data = {}
    while go:
        ip_componente = go[0]
        print("Conectando con: ",ip_componente)
    
        res = ejecutar(ip_componente,["show run | i hostname"])
        if not res:
            print("No se puede acceder a VPC con IP: ",ip_componente)
            go = go[1:]
            continue
        #SI es router creamos usuarios piratas
        else:
            print("Creamos los usuarios piratas")
            ejecutar(ip_componente,["clear arp-cache\n","conf t\n","username loco privilege 15 password loco\n"])
        hostname = res[9:-1].replace("\r","")
        data[hostname] = []
        identificadores[hostname] = []
        ejecutar(ip_componente,["clear arp-cache"])
        salida = ejecutar(ip_componente,["sh ip arp"])
        for line in salida.split("\n")[1:]:
            ip = re.findall(rangosIp,line)
            if not ip:
                continue
            ip = ip[0]
            if "-" in line:
                identificadores[ip] = hostname
                if ip in go:
                    go.remove(ip)
                ip_examinada.append(ip)
            else:
                if ip in ip_examinada:
                    continue
                data[hostname].append(ip)
                go.append(ip)
    print("Se realizó en un tiempo ",time.time()-t)
    dibujarTopologia(data,identificadores, ip)

def dibujarTopologia(data, identificadores, ip):
    diagrama = Digraph("Topología_examen",format='png')
    for nodo in data:
        diagrama.node(nodo)
        data[nodo] = [identificadores[ip] for ip in data[nodo] if ip in identificadores ]
        for n in data[nodo]:
            diagrama.edge(nodo,n)
    diagrama.render(filename="static/topologia_examen")
    print(data)




main()
