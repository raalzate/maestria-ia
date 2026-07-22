# Mozart/Oz Cheatsheet y Ejemplos

Este repositorio contiene un cheatsheet y varios ejemplos de código para el lenguaje de programación Mozart/Oz.

## ¿Qué es Mozart/Oz?

Mozart/Oz es un lenguaje de programación multiparadigma desarrollado por el consorcio Mozart. Integra programación lógica, funcional, orientada a objetos, concurrente y distribuida, y se basa en el Cálculo de Espacio de Restricciones (CCR).

## Contenido

*   `mozart_oz_cheatsheet.md`: Un resumen conciso de los conceptos clave y la sintaxis de Mozart/Oz.
*   Archivos `.oz`: Varios ejemplos de código que ilustran diferentes características del lenguaje, como variables, funciones, concurrencia, estructuras de control, etc.

## Cómo Ejecutar los Ejemplos `.oz`

Para ejecutar los archivos `.oz`, necesitas tener el sistema Mozart/Oz instalado en tu máquina.

### 1. Instalar Mozart/Oz

Puedes encontrar instrucciones detalladas para la instalación en el sitio web oficial de Mozart/Oz:

*   [Mozart/Oz System Website](http://mozart.github.io/)

La instalación típica involucra descargar el binario para tu sistema operativo y seguir las instrucciones específicas. Una vez instalado, deberías tener acceso a comandos como `oz` o `ozc` en tu terminal.

### 2. Ejecutar un Archivo `.oz`

Una vez que Mozart/Oz esté instalado, puedes ejecutar los archivos `.oz` desde tu terminal de la siguiente manera:

1.  Navega al directorio donde guardaste los archivos `.oz`:

    ```bash
    cd /Users/raul.alzate/Documents/maestria/code/proyect2
    ```

2.  Usa el comando `oz` seguido del nombre del archivo `.oz` que deseas ejecutar. Por ejemplo, para ejecutar el archivo `example_factorial.oz`:

    ```bash
    oz example_factorial.oz
    ```

    Esto ejecutará el script y mostrará la salida en tu terminal (si el script usa `{Show ...}` o mecanismos de salida estándar).

#### Ejemplo:

Para el archivo `example_factorial.oz`, la salida esperada sería:

```
120
```

---