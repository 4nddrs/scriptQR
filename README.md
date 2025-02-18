# 🖥️ MIS - Sistema de Gestión de Entradas en Terminal 🎟️

Bienvenido al **MIS (Management Information System) para la gestión de entradas de eventos**. Este sistema basado en terminal permite a los organizadores **registrar eventos, administrar entradas y generar códigos QR** para el acceso digital. 🚀  

## 🔥 Características Principales

✅ **Registro de Eventos** 📅  
Crea eventos personalizados con todos los detalles necesarios, incluyendo nombre, fecha, ubicación y capacidad.  

✅ **Gestión de Entradas** 🎫  
Genera entradas únicas con un estado específico, ID y fecha de modificación.  

✅ **Almacenamiento en Firebase** 🔥  
Toda la información de las entradas se guarda en una colección de **Firebase**, asegurando que los datos estén disponibles en cualquier momento.  

✅ **Generación de Códigos QR** 📷  
Convierte cada entrada en un **QR Code** para facilitar su escaneo y verificación digital.  

✅ **Edición y Control de Entradas** ✏️  
Consulta y modifica la información de las entradas en cualquier momento a través de la terminal.  

✅ **Exportación para Impresión** 🖨️  
Guarda las entradas en un formato listo para impresión, permitiendo su distribución física.  

## 🏗️ Arquitectura del Sistema

📌 **Interfaz:** Línea de comandos (CLI).  
📌 **Base de Datos:** Firebase Firestore.  
📌 **Formato de Entradas:** ID único, estado y fecha de modificación.  
📌 **Tecnología QR:** Generación de códigos QR para cada entrada.  

## 🛠️ Stack Tecnológico

| Componente      | Tecnología Utilizada |
|----------------|---------------------|
| Lenguaje de programación | Python 🐍 |
| Base de Datos | Firebase Firestore 🔥 |
| Generación de QR | `qrcode` 📸 |
| Interfaz de usuario | Terminal (CLI) 🖥️ |

## 🔗 Integraciones  

🌍 **App Móvil:** Los usuarios pueden almacenar sus entradas digitalmente y escanear otras entradas para control de acceso.  
🌍 **Landing Page:** Promociona el servicio y ofrece información detallada sobre su uso.  

## 🚀 ¿Cómo Funciona?  

1️⃣ **Crea un evento**: Registra el evento en el sistema con los detalles clave.  
2️⃣ **Genera entradas**: Define la cantidad de entradas
