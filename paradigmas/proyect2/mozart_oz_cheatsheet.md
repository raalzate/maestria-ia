# Cheatsheet de Mozart/Oz

Mozart/Oz es un lenguaje de programación multiparadigma que integra programación lógica, funcional, orientada a objetos, concurrente y distribuida. Se basa en el **Cálculo de Espacio de Restricciones (CCR)**.

---

## 1. Conceptos Fundamentales

*   **Variables (Single-Assignment)**: Una variable se asigna una única vez. Una vez ligada a un valor, no puede cambiarse.
    ```oz
    declare X     % X es una variable libre
    X = 10        % X se liga al valor 10
    X = 20        % ¡Error! X ya está ligada
    ```
*   **Procedimientos/Funciones**: Bloques de código que pueden ligar variables a un valor (función) o realizar una acción (procedimiento).
    ```oz
    % Función (regresa un valor al ligar el último argumento)
    fun {Suma A B}
       A+B
    end

    % Procedimiento (realiza una acción, no necesariamente regresa un valor)
    proc {Imprime X}
       {Show X} % Muestra el valor de X en el navegador (entorno Oz)
    end
    ```
*   **Espacios de Restricciones (Constraint Spaces)**: Fundamento de la programación lógica concurrente. Las variables pueden ser ligadas o restringidas por un *store* o *espacio de restricciones*.

---

## 2. Tipos de Datos Básicos

*   **Números**: Enteros y flotantes.
    ```oz
    X = 10
    Y = 3.14
    ```
*   **Átomos**: Símbolos constantes.
    ```oz
    Color = red
    Estado = ok
    ```
*   **Literales Booleanos**: `true` y `false`.
    ```oz
    EsActivo = true
    ```
*   **Tuplas**: Colecciones inmutables de elementos, similares a registros o estructuras.
    ```oz
    Persona = persona(nombre:"Ana" edad:30)
    Punto = punto(x:10 y:20)

    % Acceso a elementos
    {Show Persona.nombre} % Muestra "Ana"
    ```
*   **Listas**: Estructuras de datos recursivas compuestas por una `cabeza` y una `cola`.
    ```oz
    L = [1 2 3 4]
    L2 = [a b c]
    L3 = [Head|Tail] % Head es el primer elemento, Tail el resto de la lista
    ```
*   **Registros**: Como tuplas, pero los campos tienen nombres explícitos.
    ```oz
    Rect = rect(x:0 y:0 width:100 height:50)
    ```

---

## 3. Estructuras de Control

*   **Condicional (if-then-else)**:
    ```oz
    declare X Y
    X = 10
    if X > 5 then
       Y = 'mayor'
    else
       Y = 'menor_o_igual'
    end
    {Show Y} % Muestra 'mayor'
    ```
*   **Case (pattern matching)**: Permite la descomposición de estructuras de datos.
    ```oz
    declare L
    L = [1 2 3]

    case L of [H|T] then
       {Show H} % Muestra 1
       {Show T} % Muestra [2 3]
    else
       {Show 'Lista vacia'}
    end

    declare P
    P = persona(nombre:"Pedro" edad:25)
    case P of persona(nombre:N edad:E) then
       {Show N} % Muestra "Pedro"
       {Show E} % Muestra 25
    end
    ```
*   **Loop (recursión)**: La iteración se implementa principalmente a través de la recursión de procedimientos o funciones.

    ```oz
    % Ejemplo: Sumar elementos de una lista recursivamente
    fun {SumList L}
       case L of nil then 0
       [] [H|T] then H + {SumList T}
       end
    end

    {Show {SumList [1 2 3 4]}} % Muestra 10
    ```

---

## 4. Concurrencia y Paso de Mensajes

Mozart/Oz tiene soporte incorporado para concurrencia y distribución.

*   **Threads (hilos)**: Permite ejecutar código en paralelo.
    ```oz
    thread
       {Show 'Hola desde el hilo 1'}
    end
    thread
       {Show 'Hola desde el hilo 2'}
    end
    ```
*   **Mensajes (Stream)**: La comunicación entre threads a menudo se realiza a través de **streams** (listas concurrentes).
    ```oz
    declare S
    thread
       S = 1|2|3|nil % El hilo 'publica' los valores en el stream
    end
    thread
       {For S proc {$ X} {Show X} end} % El hilo 'consume' los valores
    end
    % El hilo consumidor imprimirá 1, 2, 3 a medida que el productor los publica.
    ```
*   **Ports (Puertos)**: Un mecanismo más avanzado para enviar mensajes a procesos específicos.

---

## 5. Ejemplos Prácticos

### Ejemplo 1: Factorial Recursivo

```oz
fun {Factorial N}
   if N == 0 then 1
   else N * {Factorial N-1}
   end
end

{Show {Factorial 5}} % Muestra 120
```

### Ejemplo 2: Generador de Números Fibonacci (concurrente)

Este ejemplo muestra cómo se puede pensar en términos de concurrencia y el *store*.

```oz
declare Fib
proc {GenFib N Prev Curr}
   if N > 0 then
      Fib = Curr | {GenFib N-1 Curr (Prev+Curr)}
   else
      Fib = nil
   end
end

% Se ejecuta en un thread para no bloquear el entorno
thread {GenFib 10 0 1} end

% Otro thread para consumir y mostrar los números de Fibonacci
thread
   {For Fib proc {$ X} {Show X} end}
end
```

### Ejemplo 3: Diccionario Simple (usando Registros y Procs)

```oz
declare Diccionario

proc {CrearDiccionario}
   Diccionario = nil % Inicialmente vacío
end

proc {AgregarEntrada Diccionario Key Value}
   Diccionario = entrada(key:Key value:Value)|Diccionario
end

proc {BuscarEntrada Diccionario Key ?Value}
   case Diccionario of nil then
      Value = 'No encontrado'
   [] entrada(key:K value:V)|Resto then
      if K == Key then
         Value = V
      else
         {BuscarEntrada Resto Key ?Value}
      end
   end
end

% Uso
{CrearDiccionario}
{AgregarEntrada Diccionario 'manzana' 'apple'}
{AgregarEntrada Diccionario 'casa' 'house'}

declare Resultado
{BuscarEntrada Diccionario 'manzana' ?Resultado}
{Show Resultado} % Muestra 'apple'

{BuscarEntrada Diccionario 'perro' ?Resultado}
{Show Resultado} % Muestra 'No encontrado'
```