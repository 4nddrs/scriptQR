import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import pyqrcode
import colorama
from colorama import Fore, Style
from termcolor import colored
import os
import qrcode
from datetime import datetime
from tabulate import tabulate

# Inicializar colores
colorama.init()

# Cargar credenciales de Firebase
cred = credentials.Certificate("key.json")  # Asegúrate de que el archivo esté en la misma carpeta
firebase_admin.initialize_app(cred)
db = firestore.client()

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print(colored("""
    
████████╗██╗ █████╗ ██╗  ██╗███████╗████████╗   ██████╗ ██████╗
╚══██╔══╝██║██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝  ██╔═══██╗██╔══██╗
   ██║   ██║██║  ╚═╝█████═╝ █████╗     ██║     ██║██╗██║██████╔╝
   ██    ██║██║  ██╗██╔═██╗ ██╔══╝     ██║     ╚██████╔╝██╔══██╗
   ██║   ██║╚█████╔╝██║ ╚██╗███████╗   ██║      ╚═██╔═╝ ██║  ██║
   ╚═╝   ╚═╝ ╚════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝        ╚═╝   ╚═╝  ╚═╝
    
    Sistema de Gestión Empresarial
    """, "cyan"))

def menu():
    #print(colored("\n[1] Agregar Usuario", "yellow"))
    print(colored("[1] Agregar Evento", "yellow"))
    print(colored("[2] Generar Entrada y QR", "yellow"))
    print(colored("[3] Consultar/Editar Datos", "yellow"))
    #print(colored("[5] Editar Datos", "yellow"))
    print(colored("[4] Salir", "red"))

def agregar_usuario():
    name = input(Fore.GREEN + "Nombre: " + Style.RESET_ALL) 
    lastName = input(Fore.GREEN + "Apellido: " + Style.RESET_ALL)
    user_id = str(uuid.uuid4())
    usuario_data = {
        "name": name,
        "lastName": lastName
    }
    db.collection("User").document(user_id).set(usuario_data)
    print(colored("Usuario agregado con éxito!", "green"))


def agregar_evento():
    try:
        name = input(Fore.GREEN + "Nombre del Evento: " + Style.RESET_ALL)
        date = input(Fore.GREEN + "Fecha (YYYY-MM-DD): " + Style.RESET_ALL)
        ubi = input(Fore.GREEN + "Ubicación: " + Style.RESET_ALL)
        stock = int(input(Fore.GREEN + "Capacidad: " + Style.RESET_ALL))
        
        # Genera un ID único para el evento
        event_id = str(uuid.uuid4())
        
        # Datos del evento
        evento_data = {
            "name": name,
            "date": date,
            "ubi": ubi,
            "stock": stock,
            "avaStock": stock,
        }
        
        # Agrega el evento a Firestore
        db.collection("Event").document(event_id).set(evento_data)
        print(colored("Evento agregado con éxito!", "green"))
        
        # Crea la colección de tickets asociada al evento
        tickets_ref = db.collection(f"Ticket_{name}")

        # Agregar los tickets a la colección de tickets (con capacidad inicial)
        for i in range(stock):  # El número de tickets es igual a la capacidad
            ticket_data = {
                'state': 'valido',  # Estado por defecto
                'modDate': datetime.now(),  # Fecha actual
                'eventID': event_id,  # ID del evento al que pertenece
            }
            tickets_ref.add(ticket_data)
            print(f"Ticket {i + 1} agregado a la colección Ticket_{name}")
        
        # Actualiza el evento para que contenga una referencia a la colección de tickets
        db.collection("Event").document(event_id).update({
            'tickets_collection': f"Ticket_{name}"  # Referencia a la colección de tickets
        })
    except KeyboardInterrupt:
        salir_programa(None, None)

def generar_qr():
    try:
        print("\n📌 Eventos disponibles:")
        eventos = db.collection("Event").stream()
        eventos_lista = []
    
        for event in eventos:
            event_data = event.to_dict()
            event_data["id"] = event.id
            eventos_lista.append(event_data)
    
        if not eventos_lista:
            print(colored("⚠ No hay eventos disponibles.", "red"))
            return
    
        headers = ["ID", "Nombre"]
        tabla = [[e["id"], e["name"]] for e in eventos_lista]
        print(tabulate(tabla, headers=headers, tablefmt="fancy_grid", stralign="center"))
    
        # Seleccionar evento
        evento_id = input(Fore.GREEN + "\nIngresa el ID del evento a consultar: " + Style.RESET_ALL)
        evento_ref = db.collection("Event").document(evento_id).get()
    
        if not evento_ref.exists:
            print(colored("❌ Evento no encontrado.", "red"))
            return
    
        evento_data = evento_ref.to_dict()
        print("\n📄 Detalles del evento:")
        print(tabulate([[k, v] for k, v in evento_data.items()], tablefmt="fancy_grid", stralign="center"))
    
        # Obtener la colección de tickets asociada al evento
        tickets_collection = evento_data.get('tickets_collection')
        if not tickets_collection:
            print(colored("⚠ No se encuentra la colección de tickets asociada a este evento.", "red"))
            return
    
        # Confirmar generación de QRs
        generar = input(Fore.CYAN + "\n¿Deseas generar QRs para todos los tickets de este evento? (s/n): " + Style.RESET_ALL).strip().lower()
        if generar != "s":
            print(colored("❌ Operación cancelada.", "red"))
            return
    
        # Crear carpeta con el nombre del evento si no existe
        evento_nombre = evento_data.get("name")
        carpeta_evento = f"QRs_{evento_nombre}"
    
        if not os.path.exists(carpeta_evento):
            os.makedirs(carpeta_evento)
            print(colored(f"📂 Carpeta '{carpeta_evento}' creada.", "green"))

        # Acceder a los tickets en la colección asociada al evento
        tickets = db.collection(tickets_collection).stream()

        tickets_lista = list(tickets)  # Convertir a lista de DocumentSnapshots

        if not tickets_lista:
            print(colored("⚠ No hay tickets para este evento.", "red"))
            return

        cont = 0 
        for ticket in tickets_lista:
            ticket_document_id = ticket.id  # ✅ Obtener el ID del documento
            ticket_data = ticket.to_dict()  # ✅ Convertir el contenido a diccionario

            qr_data = f"Ticket ID: {ticket_document_id}\nEstado: {ticket_data['state']}\nEventID: {ticket_data['eventID']}"
            qr = qrcode.make(qr_data)
            cont += 1
            qrName = f"{cont}-{evento_nombre}.png"
            qr_path = os.path.join(carpeta_evento, qrName)  # ✅ No necesitas ".png" dos veces

            qr.save(qr_path)
            print(colored(f"✅ QR generado para ticket {ticket_document_id} y guardado en '{qr_path}'", "green"))

        print(colored("\n🎉 ¡Todos los QRs han sido generados con éxito!", "green"))

    except KeyboardInterrupt:
        salir_programa(None, None)


    COLUMNAS_PERSONALIZADAS = {
    "User": {
        "name": "Nombre",
        "lastName": "Apellido",
    },
    "Event": {
        "name": "Nombre",
        "stock": "Stock",
        "avaStock": "Stock Disponible",
        "ubi": "Ubicación",
        "date": "Fecha"
    },
    "Ticket": {
        "id": "ID Ticket",
        "eventID": "Evento",
        "state": "Estado",
        "modDate": "Fecha de Modificación"
    }
}

def obtener_nombre_evento(eventoId):
    """Consulta el nombre del evento basado en su ID."""
    evento_doc = db.collection("Event").document(eventoId).get()
    return evento_doc.to_dict().get("name", "Desconocido") if evento_doc.exists else "Desconocido"

def salir_programa(sig, frame):
    print(colored("\n👋 El programa se ha cerrado.", "blue"))
    exit(0)

def truncar_texto(texto, ancho_max=15):
    """Trunca el texto si supera un límite de caracteres"""
    return (texto[:ancho_max] + "...") if len(str(texto)) > ancho_max else str(texto)

# Función para consultar datos
def consultar_datos():
    try:
        print("\n📂 Colecciones disponibles:")

        # Obtener todas las colecciones disponibles
        colecciones = db.collections()
        colecciones_lista = [coleccion.id for coleccion in colecciones]

        if not colecciones_lista:
            print(colored("⚠ No hay colecciones disponibles.", "red"))
            return

        # Mostrar las colecciones disponibles
        headers = ["ID", "Colección"]
        tabla = [[i + 1, coleccion] for i, coleccion in enumerate(colecciones_lista)]
        print(tabulate(tabla, headers=headers, tablefmt="fancy_grid", stralign="center"))

        # Seleccionar una colección
        coleccion_seleccionada = None
        while coleccion_seleccionada is None:
            try:
                coleccion_seleccionada = int(input(Fore.GREEN + "\nIngresa el número de la colección que deseas consultar: " + Style.RESET_ALL))
                if coleccion_seleccionada < 1 or coleccion_seleccionada > len(colecciones_lista):
                    print(colored("❌ Selección inválida. Intenta de nuevo.", "red"))
                    coleccion_seleccionada = None
            except ValueError:
                print(colored("❌ Entrada inválida. Debes ingresar un número. Intenta de nuevo.", "red"))

        coleccion_nombre = colecciones_lista[coleccion_seleccionada - 1]
        print(colored(f"\n📂 Colección seleccionada: {coleccion_nombre}", "cyan"))
        # Obtener todos los documentos de la colección seleccionada
        documentos = db.collection(coleccion_nombre).stream()

        if not documentos:
            print(colored("⚠ No hay documentos en esta colección.", "red"))
            return

        # Mostrar los documentos
        documentos_lista = []
        # Convertimos los documentos en una lista de diccionarios
        for doc in documentos:
            documentos_lista.append({"ID": doc.id, **doc.to_dict()})

        # Definimos los encabezados de la tabla
        headers_doc = ["ID"] + [key for key in documentos_lista[0].keys() if key != "ID"]

        # Diccionario de colores según el estado
        colores_estado = {
            "leido": Fore.RED,
            "valido": Fore.GREEN,
            "nulo": Fore.YELLOW
        }

        # Construimos la tabla con los colores aplicados
        tabla_doc = []
        for doc in documentos_lista:
            fila = [doc["ID"]]
            for key, value in doc.items():
                if key != "ID":
                    # Si la clave es "state", aplicamos el color correspondiente
                    if key == "state":
                        color = colores_estado.get(value, "")  # Si no está en el diccionario, deja el valor sin color
                        value = f"{color}{value}{Style.RESET_ALL}"
                    fila.append(value)
            tabla_doc.append(fila)

# Aplicamos truncado si es necesario
        tabla_doc_truncada = [[truncar_texto(str(value), 15) for value in row] for row in tabla_doc]

# Imprimimos la tabla
        print("\n📄 Documentos disponibles:")
        print(tabulate(tabla_doc_truncada, headers=headers_doc, tablefmt="fancy_grid", stralign="center")) 
        # Seleccionar un documento para editar
        documento_seleccionado = None
        while documento_seleccionado is None:
            try:
                documento_seleccionado = int(input(Fore.GREEN + "\nIngresa el número del documento que deseas editar: " + Style.RESET_ALL))
                if documento_seleccionado < 1 or documento_seleccionado > len(documentos_lista):
                    print(colored("❌ Selección inválida. Intenta de nuevo.", "red"))
                    documento_seleccionado = None
            except ValueError:
                print(colored("❌ Entrada inválida. Debes ingresar un número. Intenta de nuevo.", "red"))

        documento_id = documentos_lista[documento_seleccionado - 1]["ID"]

        # Obtener los datos del documento seleccionado
        doc_ref = db.collection(coleccion_nombre).document(documento_id)
        documento = doc_ref.get()

        if not documento.exists:
            print(colored("❌ El documento no se encuentra.", "red"))
            return

        documento_data = documento.to_dict()
        
        qr = False

        tabla_documento = []
        for key, value in documento_data.items():
            value = str(value)  # Convertimos a string por seguridad
            
            if key == "state":
                qr = True
                color = colores_estado.get(value, Style.RESET_ALL)  # Color según el estado
                value = f"{color}{value}{Style.RESET_ALL}"  # Aplicamos el color
            
            tabla_documento.append([key, value])

# Imprimir la tabla con colores aplicados solo en "state"
        print("\n📄 Datos del documento seleccionado:")
        print(tabulate(tabla_documento, tablefmt="fancy_grid", stralign="center"))

        if qr:
            # Generar QR para el documento seleccionado
            qr_data = f"Ticket ID: {documento_id}\nEstado: {documento_data['state']}\nEventID: {documento_data['eventID']}"
            
            

            qrPrint = qrcode.QRCode(version=1, box_size=1, border=1)
            qrPrint.add_data(qr_data)
            qrPrint.make(fit=True)

# Generar el código QR en ASCII
            qr_ascii = qrPrint.print_ascii()



        # Edición de documento
        print(Fore.CYAN + "\n¿Quieres editar este documento? (s/n): " + Style.RESET_ALL)
        editar = input().strip().lower()
        valor = 0
        state = False
        if editar == "s":
            for key in documento_data.keys():
                nuevo_valor = None
                while nuevo_valor is None:


                    nuevo_valor = input(Fore.YELLOW + f"Ingrese nuevo valor para '{key}' (deje en blanco para no cambiar): " + Style.RESET_ALL).strip()
                if key == "state":
                    state = True
                    print(Fore.CYAN + "Estado del ticket: \n[1]Valido\n[2]Leido\n[3]Nulo\n[4]No Editar" + Style.RESET_ALL)
                    resp = input()
                    if resp == "1":
                        nuevo_valor = "valido"
                        documento_data["modDate"] = datetime.now()
                        valor = 1
                    elif resp == "2":
                        nuevo_valor = "leido"
                        documento_data["modDate"] = datetime.now()
                        valor = -1
                    elif resp == "3":
                        nuevo_valor = "nulo"
                        documento_data["modDate"] = datetime.now()
                        valor = -1
                    else:
                        nuevo_valor = ""
                # Si está vacío, no cambia el valor
                if nuevo_valor != "":
                    documento_data[key] = nuevo_valor
            # Actualizar el documento con los nuevos datos
            doc_ref.update(documento_data)

            # Actualizar numero de entradas disponibles
            if state == True:
                doc_ref1 = db.collection("Event").document(documento_data.get("eventID"))
                documento1 = doc_ref1.get()
                documento_data1 = documento1.to_dict()
                doc_ref1.update({"avaStock": documento_data1.get("avaStock") + valor})


            print(colored("✅ Documento actualizado con éxito.", "green"))
        else:
            print(colored("❌ No se realizó ningún cambio.", "red"))

    except KeyboardInterrupt:            
        salir_programa(None, None)

def main():

    try:
        
        while True:
            limpiar_pantalla()
            banner()
            menu()
            opcion = input(Fore.CYAN + "\nSelecciona una opción: " + Style.RESET_ALL)
            #if opcion == "1":
            #    agregar_usuario()
            if opcion == "1":
                agregar_evento()
            elif opcion == "2":
                generar_qr()
            elif opcion == "3":
                consultar_datos()
            #elif opcion == "5":
            #   editar_datos()
            elif opcion == "4":
                print(colored("Saliendo...", "red"))
                break
            input("Presiona Enter para continuar...")

    except KeyboardInterrupt:
        salir_programa(None, None)

if __name__ == "__main__":
    main()

