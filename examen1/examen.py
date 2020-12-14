from utils import Router,get_gateway,IP_REGEX
from graphviz import Graph
import time

MI_DIAGRAMA = Graph('Mi topoligía',engine='sfdp')
USERNAME = "admin"
PASSWORD = "admin"


def main():
    # Obtenemos gateway
    gateway = get_gateway()
    nodos = [gateway] # Empezamos con el gateway
    visited_nodes = []
    connections = {}
    ip_to_hostname = {}
    t = time.time()
    while nodos:
        print("Nodo actual: ",nodos[0])
        router = Router(nodos[0],USERNAME,PASSWORD)
        # VALIDACION
        if not router.is_connected:
            print("Error al iniciar SSH en el nodo: ",nodos[0])
            nodos.pop(0) # ES POSIBLEMENTE UNA PC
            continue
        # CREAMOS NUEVO USUARIO SSH
        router.create_user("pirata","pirata")
        
        # OBTENEMOS A DONDE IR
        visited_nodes,nodos = router.get_jump_connections(visited_nodes,nodos)
        # IP A HOSTNAME
        ip_to_hostname.update(router.interfaces_ip)
        #CONEXIONES QUE TIENE EL ROUTER -> IP
        connections[router.hostname] = router.connections

    print("Tiempo de ejecución: ",time.time()-t)

    topologia = Graph("Mi topología")
    for nodo in connections:
        topologia.node(nodo)
        for ip in connections[nodo]:
            try:
                topologia.edge(nodo,ip_to_hostname[ip])
            except: pass
    topologia.render("topologia")

if __name__ == '__main__':
    main()