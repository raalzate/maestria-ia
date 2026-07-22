# Análisis de un Lenguaje de Programación: Python

**Raúl Andrés Alzate Gómez**

Universidad del Valle

Modelos y Paradigmas de Programación

---

## Resumen

Los modelos y paradigmas de programación constituyen el marco conceptual fundamental para comprender cómo los lenguajes de programación abordan la resolución de problemas computacionales. Analizar un lenguaje desde esta perspectiva permite evaluar su expresividad y determinar qué tipo de abstracciones ofrece al programador. En este artículo se analiza el lenguaje de programación Python desde los modelos de programación: **declarativo**, **concurrente declarativo**, **con estado explícito**, **concurrente por paso de mensajes**, **orientado a objetos** y **relacional**, tomando como referencia los conceptos presentados por Van-Roy y Haridi [1]. El análisis revela que Python es un lenguaje fuertemente orientado al modelo con estado y al paradigma orientado a objetos, con soporte para concurrencia por paso de mensajes a través de procesos, pero sin soporte explícito para los modelos declarativo, concurrente declarativo ni relacional.

**Palabras clave:** modelos de programación, paradigmas de programación, Python.

---

## 1. Introducción

Python es un lenguaje de programación interpretado, de tipado dinámico y multiparadigma, creado por Guido van Rossum y publicado por primera vez en 1991 [2]. Su filosofía de diseño enfatiza la legibilidad del código y una sintaxis que favorece la claridad sobre la complejidad. Python soporta programación imperativa, orientada a objetos y funcional, y en la actualidad es uno de los lenguajes más utilizados en campos como la ciencia de datos, el desarrollo web y la inteligencia artificial.

En Python, todo valor es un objeto: los enteros, las cadenas, las listas, las funciones e incluso las clases son objetos que heredan de la clase base `object`. Esta característica es central para entender cómo Python implementa los diferentes modelos de programación.

El presente documento analiza Python a la luz de los modelos y paradigmas vistos en el curso de Modelos y Paradigmas de Programación, siguiendo la taxonomía propuesta en [1]. En las siguientes secciones se examinará cada modelo, evaluando si Python lo soporta, de qué manera, y en caso de no soportarlo, se justificará la razón desde los conceptos nucleares del curso. El Cuadro 1 resume los hallazgos.

| Modelo | ¿Soportado por Python? |
|---|---|
| Programación Declarativa | No explícitamente |
| Programación Concurrente Declarativa | No |
| Programación con Estado Explícito | Sí |
| Programación Concurrente por Paso de Mensajes | Sí |
| Programación Orientada a Objetos | Sí |
| Programación Relacional | No |

*Cuadro 1. Resumen de paradigmas implementados en Python.*

---

## 2. Modelo de programación declarativo

El modelo declarativo [1] se basa en el concepto de **variable declarativa**: una variable que es solamente una abreviación para un valor, que puede estar inicialmente sin ligar, puede contener valores parciales, y que solo puede ser asignada una vez (ligadura única). Este modelo garantiza la **transparencia referencial**: una expresión siempre produce el mismo resultado dado el mismo contexto.

### 2.1 Variables en Python

Una variable declarativa tiene un identificador (lo que el programador digita) y una variable del almacén (lo que el sistema usa para calcular). Las variables declarativas no pueden ser asignadas más de una vez [1].

En Python, las variables no son variables declarativas. Son **etiquetas** (nombres) que apuntan a objetos en memoria y pueden ser reasignadas libremente:

```python
x = 10
print(x)   # 10
x = "hola"
print(x)   # hola
x = [1, 2, 3]
print(x)   # [1, 2, 3]
```

Este comportamiento corresponde al concepto de **celda** [1]. Una celda es un contenedor de un valor que se puede crear, acceder al valor que contiene y modificarlo. Es importante notar que **las celdas no son variables** [1]: pertenecen al modelo con estado, no al declarativo. En Python, las variables se comportan como celdas desde el inicio: no existe restricción alguna de ligadura única, no existe el concepto de variable sin ligar (acceder a una variable no definida produce `NameError`), y no existen valores parciales. Por lo tanto, **las variables en Python no son declarativas sino con estado**.

### 2.2 Datos estructurados y reconocimiento de patrones

En el modelo declarativo, las listas son estructuras enlazadas con patrón cabeza|cola (H|T), y el reconocimiento de patrones permite descomponer estructuras de datos [1]. Python ofrece listas como arreglos dinámicos y, desde la versión 3.10, incorpora **reconocimiento de patrones** estructural con `match/case`:

```python
def procesar(dato):
    match dato:
        case [cabeza, *cola]:
            print(f"Cabeza: {cabeza}, Cola: {cola}")
        case {"nombre": n, "edad": e}:
            print(f"{n} tiene {e} años")
        case _:
            print("Patrón no reconocido")

procesar([1, 2, 3])                      # Cabeza: 1, Cola: [2, 3]
procesar({"nombre": "Ana", "edad": 25})  # Ana tiene 25 años
```

Este mecanismo es análogo a la instrucción `case` del modelo declarativo, permitiendo descomponer estructuras de datos según patrones. Sin embargo, en el modelo declarativo el pattern matching opera sobre variables declarativas y puede ligarlas, mientras que en Python solo asigna valores a nombres mutables.

### 2.3 Funciones y programación de alto orden

Python ofrece características del paradigma funcional. Las funciones son **ciudadanos de primera clase**: pueden asignarse a variables, pasarse como argumentos y retornarse desde otras funciones. La capacidad de pasar funciones como argumentos se conoce como **programación de alto orden**, y ayuda a construir **abstracciones genéricas** [1].

```python
def aplicar(f, x):
    return f(x)

cuadrado = lambda x: x ** 2
print(aplicar(cuadrado, 5))  # 25
```

Python soporta **clausuras léxicas** (closures), donde una función interna captura variables de su ambiente:

```python
def crear_sumador(n):
    def sumador(x):
        return x + n
    return sumador

sumar5 = crear_sumador(5)
print(sumar5(10))  # 15
```

Esto corresponde al concepto de **valores procedimiento con ambiente contextual** [1]. Además, la programación de alto orden permite crear versiones genéricas de funciones, pasando la operación como argumento:

```python
def pascal_generico(op, n):
    if n == 1:
        return [1]
    fila_ant = pascal_generico(op, n - 1)
    return [fila_ant[i] if i == 0
            else (op(fila_ant[i-1], fila_ant[i])
                  if i < len(fila_ant)
                  else fila_ant[i-1])
            for i in range(len(fila_ant) + 1)]

suma = lambda a, b: a + b
xor = lambda a, b: 0 if a == b else 1
print(pascal_generico(suma, 5))  # Triángulo de Pascal clásico
print(pascal_generico(xor, 5))   # Variación con XOR
```

### 2.4 Recursión

Python soporta funciones recursivas e iterativas con acumulador:

```python
# Recursivo
def factorial_r(n):
    if n == 0:
        return 1
    return n * factorial_r(n - 1)

# Iterativo con acumulador
def factorial_i(n, acc=1):
    if n == 0:
        return acc
    return factorial_i(n - 1, acc * n)

print(factorial_r(5))  # 120
print(factorial_i(5))  # 120
```

Sin embargo, Python **no optimiza la recursión de cola** (tail call optimization), lo que limita la profundidad recursiva a aproximadamente 1000 llamadas por defecto [2].

### 2.5 Evaluación perezosa

En el modelo declarativo, la evaluación perezosa permite que un cálculo solo se realice cuando su resultado se necesita, habilitando la representación de estructuras de datos infinitas [1]. Python ofrece **generadores** con un mecanismo análogo:

```python
def enteros(n):
    while True:
        yield n
        n += 1

gen = enteros(1)
print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3
```

La palabra reservada `yield` suspende la ejecución y retorna un valor bajo demanda, equivalente a la evaluación perezosa explícita descrita en [1]. Los generadores permiten definir secuencias potencialmente infinitas que se evalúan solo cuando se consumen.

### 2.6 Conclusión sobre el modelo declarativo

Python **no implementa explícitamente el modelo declarativo** porque sus variables no cumplen con la propiedad de ligadura única (son celdas, no variables declarativas), no existen valores parciales, y no se garantiza la transparencia referencial de forma nativa. Sin embargo, el programador puede adoptar un estilo declarativo al evitar la reasignación y utilizar las características funcionales del lenguaje (alto orden, clausuras, generadores). Esto es una decisión del programador, no una restricción del lenguaje.

---

## 3. Modelo de programación concurrente declarativo

El modelo concurrente declarativo [1] extiende el modelo declarativo con el concepto de **hilo** y de **variable de flujo de datos** (dataflow variable). Un hilo es simplemente un programa secuencial en ejecución. Lo fundamental de este modelo es que si una operación trata de usar una variable que no está ligada aún, entonces **espera** [1]. Esto permite que la comunicación entre hilos sea implícita y que el no-determinismo sea **no observable**: el resultado del programa es el mismo sin importar el orden de ejecución.

### 3.1 Hilos en Python

Python ofrece hilos a través del módulo `threading`:

```python
import threading

def tarea(nombre):
    print(f"Hilo {nombre} ejecutándose")

t1 = threading.Thread(target=tarea, args=("A",))
t2 = threading.Thread(target=tarea, args=("B",))
t1.start()
t2.start()
t1.join()
t2.join()
```

Estos hilos están limitados por el **Global Interpreter Lock (GIL)**, que impide que múltiples hilos ejecuten bytecode de Python simultáneamente [3]. Además, como las variables en Python son celdas (mutables), al combinar concurrencia con estado se produce **no-determinismo observable**: el mismo programa puede dar resultados diferentes entre ejecuciones, exactamente como se muestra en el concepto de intercalación del curso [1].

### 3.2 Ausencia de variables de flujo de datos

El concepto fundamental que falta en Python es la **variable de flujo de datos**. Estas variables permiten la ejecución dirigida por datos: los cálculos son "pacientes", no señalan errores sino que simplemente esperan [1]. En Python:

- Las variables no pueden estar **sin ligar**: toda variable debe ser asignada antes de ser leída (`NameError`).
- No existe un mecanismo de **suspensión automática** que espere la ligadura de una variable.
- La comunicación entre hilos requiere mecanismos explícitos con estado (locks, queues).

```python
# En el modelo concurrente declarativo, leer una variable
# sin ligar suspendería el hilo. En Python produce un error:
print(x)  # NameError: name 'x' is not defined
```

### 3.3 Conclusión sobre el modelo concurrente declarativo

Python **no soporta el modelo concurrente declarativo** porque carece de variables de flujo de datos y del mecanismo de suspensión automática. Además, la concurrencia en Python con hilos introduce **no-determinismo observable** (el programa puede dar diferentes resultados según la intercalación), lo cual contradice la propiedad fundamental de este modelo donde los cálculos funcionan correctamente independientemente de cómo se han repartido entre los hilos [1].

---

## 4. Modelo de programación con estado explícito

El modelo con estado [1] introduce el concepto de **celda** para dotar a las funciones de memoria interna. ¿Cómo podemos lograr que una función aprenda de su pasado? La memoria se necesita en funciones que pueden cambiar su comportamiento. Este tipo de memoria se llama **estado explícito**, y el concepto más sencillo para implementarlo es una **celda**: un contenedor de un valor que se puede crear, acceder y modificar. Es importante enfatizar que **las celdas no son variables** [1].

### 4.1 Variables como celdas

Las variables en Python tienen desde el inicio el comportamiento de celdas. Pueden almacenar cualquier valor y modificarlo:

```python
c = 0       # crear celda con valor 0
c = c + 1   # modificar el contenido
print(c)    # acceder al valor: 1
```

### 4.2 Estado global vs. estado encapsulado

El curso distingue entre estado global y **estado encapsulado**: la memoria local a una función [1]. Python soporta ambos:

```python
# Estado global
contador_global = 0
def incrementar():
    global contador_global
    contador_global += 1

# Estado encapsulado
def crear_pascal_con_memoria():
    invocaciones = [0]  # celda encapsulada
    def pascal(n):
        invocaciones[0] += 1
        return invocaciones[0]
    return pascal

mi_pascal = crear_pascal_con_memoria()
print(mi_pascal(5))  # 1
print(mi_pascal(5))  # 2
```

El segundo ejemplo muestra estado encapsulado: la celda `invocaciones` es invisible desde el exterior, exactamente como se espera al encapsular estado dentro de una función [1].

### 4.3 Principio de abstracción

Python cumple con las cuatro propiedades del principio de abstracción [1]:

- **Encapsulación**: alcance léxico en funciones y clases. Las variables internas son invisibles desde fuera, tal como la celda queda completamente invisible desde el exterior. Separar la interfaz de la implementación es la esencia de la abstracción de datos [1].
- **Composicionalidad**: las funciones y clases pueden componerse libremente.
- **Instanciación**: se pueden crear múltiples instancias independientes de una abstracción.
- **Extensionalidad**: el estado explícito permite extender el comportamiento de una abstracción de forma independiente a su creación.

### 4.4 Conclusión sobre el modelo con estado

Python **soporta plenamente el modelo con estado explícito**. Las variables actúan como celdas desde su definición, soporta tanto estado global como encapsulado, y cumple con el principio de abstracción. Este es el modelo natural de programación en Python.

---

## 5. Modelo de programación concurrente por paso de mensajes

El modelo concurrente por paso de mensajes [1] se basa en el concepto de **puerto** (port): un canal de comunicación a través del cual los hilos envían mensajes. Un **objeto puerto** es un hilo que lee mensajes de su puerto y los procesa secuencialmente, manteniendo un estado interno.

### 5.1 Módulo multiprocessing y Queue como puertos

Python implementa este modelo a través del módulo `multiprocessing`, que crea procesos independientes del sistema operativo (evitando el GIL). La comunicación se realiza mediante `Queue`, que funciona como un **puerto**:

```python
from multiprocessing import Process, Queue

def productor(q):
    q.put("mensaje 1")
    q.put("mensaje 2")
    q.put("FIN")

def consumidor(q):
    while True:
        msg = q.get()  # se suspende si no hay mensajes
        if msg == "FIN":
            break
        print(f"Recibido: {msg}")

q = Queue()
p1 = Process(target=productor, args=(q,))
p2 = Process(target=consumidor, args=(q,))
p1.start()
p2.start()
p1.join()
p2.join()
```

La operación `q.get()` **suspende** el proceso consumidor si no hay mensajes, de manera análoga a cómo un objeto puerto espera mensajes en su flujo (stream) [1].

### 5.2 Objeto puerto

Es posible modelar el concepto de **objeto puerto** [1], creando un proceso que encapsula un estado interno y procesa mensajes secuencialmente:

```python
from multiprocessing import Process, Queue

def objeto_puerto(q):
    estado = {}
    while True:
        msg = q.get()
        if msg[0] == "guardar":
            _, clave, valor = msg
            estado[clave] = valor
        elif msg[0] == "obtener":
            _, clave, respuesta_q = msg
            respuesta_q.put(estado.get(clave))
        elif msg[0] == "fin":
            break

q = Queue()
resp = Queue()
p = Process(target=objeto_puerto, args=(q,))
p.start()

q.put(("guardar", "nombre", "Python"))
q.put(("obtener", "nombre", resp))
print(resp.get())  # Python
q.put(("fin",))
p.join()
```

El proceso `objeto_puerto` encapsula estado (diccionario `estado`), recibe mensajes a través de una `Queue` y responde a través de otra. Este patrón es equivalente al concepto de objeto puerto del modelo concurrente por paso de mensajes [1].

### 5.3 Conclusión sobre el modelo concurrente por paso de mensajes

Python **soporta el modelo concurrente por paso de mensajes** mediante `multiprocessing` con `Queue`. Los procesos son independientes, no comparten memoria y se comunican exclusivamente mediante mensajes. El concepto de objeto puerto se implementa de forma natural.

---

## 6. Modelo de programación orientado a objetos

Según [1], el camino hacia la POO parte del estado explícito: una **función con memoria interna se llama objeto**. Los objetos tienen operaciones (su **interfaz**), y la celda queda encapsulada. Si necesitamos más de un objeto, creamos una "fábrica" que pueda fabricar tantos como necesitemos: tal fábrica se llama **clase**. La clase se implementa con programación de alto orden. Finalmente, **POO = PBO (Programación Basada en Objetos) + herencia**. La herencia consiste en definir una clase nueva en términos de clases ya existentes [1].

### 6.1 De objetos a clases

En Python podemos ver esta progresión. Primero, un **objeto** como función con memoria interna:

```python
def crear_contador():
    cuenta = [0]  # celda encapsulada
    def incr():
        cuenta[0] += 1
        return cuenta[0]
    def leer():
        return cuenta[0]
    return {"incr": incr, "leer": leer}

c = crear_contador()
print(c["incr"]())  # 1
print(c["incr"]())  # 2
print(c["leer"]())  # 2
```

Este es un objeto en el sentido de [1]: tiene memoria interna (la celda `cuenta`) e interfaz (`incr` y `leer`). La celda está encapsulada e invisible desde el exterior.

Sin embargo, Python provee **sintaxis especial** para objetos a través de clases, que actúan como fábricas:

```python
class Contador:
    def __init__(self):
        self.__cuenta = 0  # celda encapsulada

    def incr(self):
        self.__cuenta += 1
        return self.__cuenta

    def leer(self):
        return self.__cuenta

c1 = Contador()  # fabricar un contador
c2 = Contador()  # fabricar otro
print(c1.incr())  # 1
print(c1.incr())  # 2
print(c2.leer())  # 0  (independiente de c1)
```

La clase `Contador` es una **fábrica de objetos**: puede crear tantos contadores como necesitemos, cada uno con su propia memoria interna por separado.

### 6.2 Herencia

Python soporta **herencia simple y múltiple**. La herencia permite definir una clase nueva en términos de clases ya existentes [1]. Es un concepto delicado de usar correctamente, y para que sea fácil de usar, los lenguajes orientados a objetos agregan sintaxis especial [1]:

```python
class Animal:
    def __init__(self, nombre):
        self.nombre = nombre
    def hablar(self):
        raise NotImplementedError

class Perro(Animal):
    def hablar(self):
        return f"{self.nombre} dice: ¡Guau!"

class Gato(Animal):
    def hablar(self):
        return f"{self.nombre} dice: ¡Miau!"

# Herencia múltiple
class Mascota:
    def es_mascota(self):
        return True

class PerroMascota(Perro, Mascota):
    pass

p = PerroMascota("Rex")
print(p.hablar())       # Rex dice: ¡Guau!
print(p.es_mascota())   # True
```

Python resuelve conflictos de herencia múltiple mediante el **Method Resolution Order (MRO)**, que utiliza el algoritmo C3 de linealización [2].

### 6.3 Encapsulación

Python utiliza convenciones para la encapsulación: `_atributo` indica acceso desalentado, y `__atributo` aplica **name mangling** (renombra a `_Clase__atributo`). A diferencia del modelo presentado en [1], donde los atributos de clase son estrictamente privados, en Python la encapsulación es por convención. Sin embargo, el name mangling proporciona un nivel razonable de protección.

### 6.4 Conclusión sobre el modelo orientado a objetos

Python **soporta plenamente la POO**. Ofrece clases (fábricas de objetos), objetos (funciones con memoria interna), herencia (simple y múltiple), polimorfismo (vía duck typing) y encapsulación. En Python todo es un objeto, cumpliendo con la definición de POO = PBO + herencia [1].

---

## 7. Modelo de programación relacional

El modelo relacional [1] se basa en la **escogencia no-determinista** (choice): la capacidad de explorar múltiples alternativas de ejecución y encontrar soluciones que satisfagan restricciones. Requiere las operaciones `choice` y `fail`, junto con un mecanismo de **búsqueda** (search).

### 7.1 Ausencia de escogencia no-determinista

Python **no implementa** escogencia no-determinista en su núcleo. No existe un mecanismo nativo para:

1. Definir alternativas que se exploren automáticamente.
2. Propagar fallos hacia atrás (backtracking automático).
3. Explorar sistemáticamente un espacio de búsqueda.

Aunque se puede implementar **backtracking manual** con recursión, esto no equivale al modelo relacional donde la escogencia y búsqueda son abstracciones del lenguaje:

```python
# Backtracking manual - NO es programación relacional
def resolver(tablero, fila=0):
    if fila == len(tablero):
        return True
    for col in range(len(tablero)):
        if es_seguro(tablero, fila, col):
            tablero[fila] = col
            if resolver(tablero, fila + 1):
                return True
    return False
```

En el modelo relacional, el motor de búsqueda exploraría las alternativas automáticamente. En Python, el programador debe implementar la lógica de búsqueda explícitamente.

### 7.2 Conclusión sobre el modelo relacional

Python **no soporta el modelo relacional** porque carece del concepto de escogencia no-determinista y de un mecanismo de búsqueda integrado.

---

## 8. Conclusiones

- **El modelo con estado explícito y el orientado a objetos son los paradigmas dominantes en Python.** Las variables actúan como celdas (no como variables declarativas) desde su creación, y la filosofía de "todo es un objeto" hace que la POO sea el modelo más natural. Como se definió en el curso, un objeto es una función con memoria interna, y una clase es una fábrica de objetos [1]; Python soporta ambos conceptos nativamente.

- **Python soporta la concurrencia por paso de mensajes** a través de `multiprocessing` con `Queue` (equivalente a puertos), permitiendo construir objetos puerto con estado encapsulado.

- **El modelo declarativo no está soportado explícitamente** porque las variables no cumplen con ligadura única. Sin embargo, Python ofrece herramientas funcionales (alto orden, clausuras, generadores, pattern matching) que permiten un estilo declarativo por decisión del programador.

- **El modelo concurrente declarativo no está soportado** debido a la ausencia de variables de flujo de datos. Al combinar concurrencia con estado (celdas) se produce **no-determinismo observable**, contrario a la propiedad fundamental de este modelo [1].

- **El modelo relacional no está soportado** por la ausencia de escogencia no-determinista.

En síntesis, Python centra su poder en el modelo con estado, la orientación a objetos y la concurrencia por paso de mensajes. Su incapacidad para soportar los modelos declarativo, concurrente declarativo y relacional se debe fundamentalmente a que sus variables son celdas mutables (no variables declarativas de ligadura única) y a la ausencia de variables de flujo de datos y escogencia no-determinista.

---

## Referencias

[1] Van-Roy, P., & Haridi, S. (2004). *Concepts, Techniques, and Models of Computer Programming*. MIT Press.

[2] Python Software Foundation. *Python Documentation*. https://docs.python.org/3/

[3] Python Wiki. *GlobalInterpreterLock*. https://wiki.python.org/moin/GlobalInterpreterLock

[4] Beazley, D. (2010). *Understanding the Python GIL*. PyCon 2010.

[5] Van Rossum, G. (2009). *The History of Python*. https://python-history.blogspot.com/
