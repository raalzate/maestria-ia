declare
%%% 1. Generador de Naturales (Usando ByNeed para pereza manual)
%%% ByNeed crea un 'futuro': el cálculo solo ocurre cuando alguien "necesita" el valor.
fun {Nats N}
   N | {ByNeed fun {$} {Nats N+1} end}
end

%%% 2. Función Take (Consumidor)
%%% Esta función es la que "fuerza" la evaluación al pedir los elementos de la lista.
fun {Take N Xs}
   if N == 0 then nil
   else
      case Xs of X|Xr then
         X | {Take N-1 Xr}
      end
   end
end

%%% 3. Generador de Pares (Usando la palabra clave 'lazy')
%%% 'lazy' es azúcar sintáctica que hace lo mismo que ByNeed automáticamente.
fun lazy {Even N}
   if N mod 2 == 0 then
      N | {Even N+1}
   else
      {Even N+1}
   end
end

%%% 4. Ejecución y Pruebas
% Definimos las variables
NatsFrom1 = {Nats 1}
EvensList = {Even 0}

% Mostramos los resultados en el Browser de Oz
{Browse 'Primeros 5 naturales:'}
{Browse {Take 5 NatsFrom1}} % Debería mostrar [1 2 3 4 5]

{Browse 'Primeros 3 pares:'}
{Browse {Take 3 EvensList}} % Debería mostrar [0 2 4]