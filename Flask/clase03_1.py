from flask import Flask
from flask import render_template

from flask import Flask, url_for, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy

from flask_bootstrap import Bootstrap
import subprocess
import paramiko
import re
import time
from graphviz import Digraph


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost:3306/miRed'
bd = SQLAlchemy(app)
Bootstrap(app)
#Dispositivos analizar los dispositivos#########################################################################################################
class ValidaError(ValueError):
    pass
class Usuarios(bd.Model):
    __tablename__ = 'Usuarios'
    
    router = bd.Column(bd.String(120))
    usuario = bd.Column(bd.String(120))
    password = bd.Column(bd.String(120))
    identificador = bd.Column(bd.String(120), primary_key=True)
  
   
    def exporta_datos(usu):
        return {
            'router': usu.router,
            'usuario': usu.usuario,
            'password': usu.password,
            'identificador': usu.identificador
            
        }
    def importa_datos(usu, datos):
        try:
            
            usu.router=datos['router']
            usu.usuario=datos['usuario']
            usu.password=datos['password']
            usu.identificador=datos['identificador']
            
        except KeyError as e:
            raise ValidaError('Dispositivo invalido: caido ' + e.args[0])
        return usu

class Interfaces(bd.Model):
    __tablename__ = 'Interfaces'
    #numero = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(120))
    nombre_inte = bd.Column(bd.String(120))
    ip = bd.Column(bd.String(120), primary_key=True)
   # rol = bd.Column(bd.String(64))
    mascara = bd.Column(bd.String(120))
   
    def exporta_datos(inte):
        return {
            'hostname': inte.hostname,
            'ip': inte.ip,
            'nombre_inte': inte.nombre_inte,
            'mascara': inte.mascara
        }
    def importa_datos(inte, datos):
        try:
            
            inte.hostname= datos['hostname']
            inte.ip= datos['ip']
            inte.nombre_inte=datos['nombre_inte']
            inte.mascara= datos['mascara']
        except KeyError as e:
            raise ValidaError('Dispositivo invalido: caido ' + e.args[0])
        return inte



 

class Dispositivo(bd.Model):
    __tablename__ = 'dispositivos'
    numero = bd.Column(bd.Integer, primary_key=True)
    hostname = bd.Column(bd.String(64), unique=True)
    marca = bd.Column(bd.String(120))
    id_ip = bd.Column(bd.String(120), unique=True)
   # rol = bd.Column(bd.String(64))
    act_interfaces = bd.Column(bd.Integer)
    versionSO = bd.Column(bd.String(200))

    def dame_url(dis):
        return url_for('dame_dispositivo', id=dis.numero, _external=True)

    def exporta_datos(dis):
        return {
            'url': dis.dame_url(),
            'hostname': dis.hostname,
            'id_ip': dis.id_ip,
            'numero': dis.numero,
            'marca': dis.marca,
            'act_interfaces': dis.act_interfaces,
            'versionSO': dis.versionSO
        }

    def importa_datos(dis, datos):
        try:
            
            dis.hostname= datos['hostname']
            dis.id_ip= datos['id_ip']
            dis.numero=datos['numero']
            dis.marca= datos['marca']
            dis.act_interfaces= datos['act_interfaces']
            dis.versionSO= datos['versionSO']
        except KeyError as e:
            raise ValidaError('Dispositivo invalido: caido ' + e.args[0])
        return dis

#parte grafica del REST

#función para agregar usuarios ejecutar(ip_componente,["clear arp-cache\n","conf t\n","username loco privilege 15 password loco\n"])

#funcion add usuario
@app.route('/agregarusuario/<string:id>', methods=["POST"])
def agregar_usuario(id):
    print(request.form.get('usuario'))
    nombre=request.form.get("usuario")
    password=request.form.get("password")
    print("nombre", nombre)
    dispositivo=bd.session.query(Dispositivo). filter_by(hostname=id).first()
    ejecutar(dispositivo.id_ip,["clear arp-cache\n","conf t\n", "username "+nombre+" privilege 15 password "+password+"\n"])

    return "Agregado completo"

#función eliminar de la bd
@app.route('/eliminarusuario/<string:id>', methods=["GET"])
def elimina_usuario(id):
    print(id)
    usuario = bd.session.query(Usuarios).filter_by(identificador=id).first()
    hostname=usuario.router
    nombre=usuario.usuario
    print(hostname,nombre)
    bd.session.delete(usuario)
    bd.session.commit()
    comando=["clear arp-cache\n","conf t\n","no username "+nombre+"\n"]
    print(comando)
    interfaz=bd.session.query(Dispositivo). filter_by(hostname=hostname).first()
    print(interfaz.id_ip)
    ejecutar(interfaz.id_ip,comando)
    return "Eliminado completo"


#funcion insertar la bd usuarios


def inserta_usuarios(info, hostname):
    datos=info.split("\n")
    array_json=[]
    
    while len(datos)>1:
        print("usuarios", datos)
        linea=datos[0].split(" ")
        usu=linea[1]
        iden=hostname+"-"+usu
        passw=linea[6]
        try:
            usuario= Usuarios(router = hostname, usuario = usu, password=passw, identificador= iden)
            bd.session.add(usuario)
            bd.session.commit()
            bd.Session.commit()
            array_json.append(usuario.exporta_datos())
        except Exception as e:
            print(e)
            print("Ya esta agregado este usuario en la base de datos")
            bd.session.rollback()
            usu= bd.session.query(Usuarios).filter_by(identificador=iden).first()
            array_json.append(usu.exporta_datos())
        datos.pop(0)
    return array_json

#mostrar usuarios
@app.route('/usuarios/<string:ip>', methods=['GET'])
def muestra_usuarios(ip):
    
    comando=["show running-config | i user"]
    hostname=ejecutar(ip,["show run | i hostname"])
    hostname=hostname[9:-1].replace("\r","")
    info=ejecutar(ip,comando)
    info=inserta_usuarios(info, hostname)
    print("info", info)
    return render_template('usuarios.html', info=info)

#update usuarios
@app.route('/usuarios/<string:id>', methods=['POST'])
def edita_usuario(id):
    print(id)
    usuario = bd.session.query(Usuarios).filter_by(identificador=id).first()
    print("variable x ", usuario)
    json= {"router": usuario.router, "usuario": request.form.get("usuario"), "identificador": usuario.identificador, "password": request.form.get("password")};
    print("json:", json)
    usuario.importa_datos(json)
    bd.session.add(usuario)
    bd.session.commit()
    return "Modificado completo"


#funcion insertar la bd interfaces
def inserta_interface(info, hostname):
    datos=info.split("\n")
    array_json=[]
    info=info.split("\n")
    while len(datos)>1:
        print("datos", datos)
        interface=hostname
        interfaceName=datos[0].split(" ")
        interface=interface+" "+interfaceName[1]
        if " no ip address" in datos[1]:
	    #dis= Interfaces(hostname = hostname, ip = "Sin ip", mascara= "sin mascara", nombre_inte= interface)
            #bd.session.add(dis)
            #bd.session.commit()
            #Session.commit()
            info.append("sin ip")
            datos.pop(0)
            datos.pop(0)
            continue
        ip_mask=datos[1].split(" ")
        print("ip y mascara:",ip_mask)
        ipin=ip_mask[3]
        info.append(ipin) 
        mask=ip_mask[4]
        try:
            interfaz= Interfaces(hostname = hostname, ip = ipin, mascara= mask, nombre_inte= interface)
            bd.session.add(interfaz)
            bd.session.commit()
            Session.commit()
            array_json.append(interfaz.exporta_datos())
        except Exception as e:
            print(e)
            print("Ya esta agregada esta interfaz en la base de datos")
            bd.session.rollback()
            inter= bd.session.query(Interfaces).filter_by(nombre_inte=interface).first()
            array_json.append(inter.exporta_datos())
        datos.pop(0)
        datos.pop(0)
    return array_json
#update interfaz
@app.route('/interfaz/<string:ipn>', methods=['POST'])
def edita_interfaz(ipn):
    print(ipn)
    interfaz = bd.session.query(Interfaces).filter_by(ip=ipn).first()
    print("variable x ", interfaz)
    #interfaz = Dispositivo.query.get_or_404(ip)
   # print(dispositivo.hostname, "formulario: ",request.form)
    json= {"hostname": interfaz.hostname, "mascara": request.form.get("mascara"), "nombre_inte": interfaz.nombre_inte, "ip": request.form.get("ip")};
    print("json:", json)
    interfaz.importa_datos(json)
    bd.session.add(interfaz)
    bd.session.commit()
    json=interfaz.exporta_datos()
    json["hostname"]
    #json=interfaz.query.get_or_404(id).exporta_datos()
    return "Modificado completo"



#mostrar las interfaces
@app.route('/interfaz/<string:ip>', methods=['GET'])
def muestra_interfaces(ip):
    
    comando=["show run | inc interface | ip address"]
    hostname=ejecutar(ip,["show run | i hostname"])
    hostname=hostname[9:-1].replace("\r","")
    info=ejecutar(ip,comando)
    info=inserta_interface(info, hostname)
    print("info", info)
    return render_template('interfaces.html', info=info)





@app.route('/dispositivos/', methods=['GET'])
def dame_dispositivos():
    return jsonify({'dispositivo': [dispositivo.dame_url() 
                               for dispositivo in Dispositivo.query.all()]})

@app.route('/dispositivos/<int:id>', methods=['GET'])
def dame_dispositivo(id):
    #id_n=id[1:]
    json=Dispositivo.query.get_or_404(id).exporta_datos()
    print("json ",json)
    return render_template('dispositivos.html', json=json)

@app.route('/dispositivos/', methods=['POST'])
def nuevo_dispositivo():
    dispositivo = Dispositivo()
    dispositivo.importa_datos(request.json)
    bd.session.add(dispositivo)
    bd.session.commit()
    return jsonify({}), 201, {'Locacion': dispositivo.dame_url()}

@app.route('/dispositivos/<int:id>', methods=['POST'])
def edita_dispositivos(id):
    dispositivo = Dispositivo.query.get_or_404(id)
    print(dispositivo.hostname, "numero entrante:",request.form)
    json= {"hostname": request.form.get("hostname"), "marca": request.form.get("marca"), "id_ip": request.form.get("id_ip"), "act_interfaces": dispositivo.act_interfaces, "versionSO": request.form.get("versionSO"), "numero": dispositivo.numero};
    print("json:", json)
    dispositivo.importa_datos(json)
    bd.session.add(dispositivo)
    bd.session.commit()
    json=Dispositivo.query.get_or_404(id).exporta_datos()
    return render_template('dispositivos.html', json=json)

#ruta para editar


################################################################################################################################################

#ANALIZAR LA TOPOLOGIA PARA DIBUJARLA Y CREAR LOS USUARIOS SSH
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
            print("enviando el comando: ", commando)
            shell.send(commando)
            time.sleep(0.30)
        ssh.close()
        return
    else:
        stdin,stdout,stderr = ssh.exec_command(comandos[0])
        data = stdout.read().decode()
        ssh.close()
    return data


def get_gateway():
    p = subprocess.Popen(["ip r"], stdout=subprocess.PIPE, shell=True)
    output = str(p.stdout.read())
    ips = re.findall(IP_REGEX,output)
    return ips[0]


def obtenmax_ip(ip):
    datos=ejecutar(ip,["show ip ospf interface"])
    datos=datos.split("\n")
    interfaz=datos[2]
    print("ip mas alta: ",interfaz)
    interfaz=interfaz.split(" ")
    ip=interfaz[4]
    mascara=ip[len(ip)-4:]
    ip=ip.replace(mascara,"")
    print("ip mas alta: ",mascara+" "+ip)
    return ip

@app.route('/topologia')
def analizar_top():
    rangosIp = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
    p = subprocess.Popen(["ip r"], stdout=subprocess.PIPE, shell=True)
    output = str(p.stdout.read())
    ips = re.findall(rangosIp,output)
    print("\n IP's en la topología:")
    for i in ips:
        print(i,"\n");
    #Nuestro gateway es la dirección más baja     
    gateway = ips[0]
    
#esto nos da la info relevante de la tabla de enrutamiento del router 1
    ip_info=ejecutar(gateway,["show ip route\n"])
    ip_info=ip_info.split("\n")[1:]
    sh_route=[]
    for i in ip_info:
        if '.' not in i:
                continue
        else:
                i.replace("\r","")
                sh_route.append(i)
    #sh_route.append(ip_info.pop(len(ip_info)-1))
    #print(ip_info)
    id_router=1
    datos_insertar=[]
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
            print("Agregamos ip, datos router a los datos de la bd")
            datos_insertar.append(id_router)        
            datos_insertar.append(obtenmax_ip(ip_componente))
            so=ejecutar(ip_componente,["sh version"])
            marca=so.split(" ")
            datos_insertar.append(marca[7])
            datos_insertar.append(marca[0])
            print("marca: ",marca[0])
            activas=0
            interfaces=ejecutar(ip_componente,["sh interface | i up"]) 
            interfaces=interfaces.split("\n")
            #print("int: ", interfaces)
            for active in interfaces:
                #print("linea: ", " up " in active)
                if " up " in active:
                    activas+=1
            print("interfaces activas: ", activas)
            datos_insertar.append(activas)
		

        hostname = res[9:-1].replace("\r","")
        datos_insertar.append(hostname)
        print("hst: ",res)
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
        id_router+=1
        dis= Dispositivo(hostname = datos_insertar[5], marca = datos_insertar[3], id_ip = datos_insertar[1], act_interfaces = datos_insertar[4], versionSO = datos_insertar[2])
        bd.session.add(dis)
        bd.session.commit()
        print("Datos a insertar: ", datos_insertar)  
        datos_insertar.clear()
              

    print("Se realizó en un tiempo ",time.time()-t)
    print("Datos a insertar: ", datos_insertar)
    dibujarTopologia(data,identificadores, ip)
    return render_template('base.html', ip_info=sh_route)

def dibujarTopologia(data, identificadores, ip):
    diagrama = Digraph("Topología_examen",format='png')
    for nodo in data:
        diagrama.node(nodo)
        for ip in data[nodo]:
            try:
                diagrama.edge(nodo,identificadores[ip])
            except:
                print(ip)

            
        #data[nodo] = [identificadores[ip] for ip in data[nodo] if ip in identificadores ]
        #for n in data[nodo]:
         #   diagrama.edge(nodo,n)
    diagrama.render(filename="static/topologia_examen")
    print(data)

@app.route('/')
def hello_networkers():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

#CREATE TABLE `miRed`.`dispositivos` ( `numero` INT NOT NULL AUTO_INCREMENT , `hostname` VARCHAR(64) NOT NULL , `marca` VARCHAR(120) NOT NULL , `id_ip` VARCHAR(120) NOT NULL , `act_interfaces` INT NOT NULL , `versionSO` VARCHAR(200) NOT NULL , PRIMARY KEY (`numero`)) ENGINE = InnoDB; 

#CREATE TABLE `miRed`.`Interfaces` ( `hostname` VARCHAR(120) NOT NULL , `nombre_inte` VARCHAR(200) NOT NULL , `mascara` VARCHAR(120) NOT NULL , `ip` VARCHAR(120) NOT NULL , PRIMARY KEY (`nombre_inte`)) ENGINE = InnoDB; 

#CREATE TABLE `miRed`.`Usuarios` ( `identificador` VARCHAR(120) NOT NULL , `router` VARCHAR(120) NOT NULL , `usuario` VARCHAR(120) NOT NULL , `password` VARCHAR(120) NOT NULL , PRIMARY KEY (`identificador`)) ENGINE = InnoDB;


