%% contador.oz
%% Punto 3: Contador con multiples clientes usando puertos y flujos
%% Servidor que cuenta ocurrencias de caracteres enviados por multiples clientes

functor
import
   Browser(browse:Browse)
define
   %% Incrementa el conteo de un caracter en la lista de pares
   fun {IncChar Char Estado}
      case Estado
      of nil then [Char#1]
      [] (C#N)|Rest then
         if C == Char then (C#(N+1))|Rest
         else (C#N)|{IncChar Char Rest}
         end
      end
   end

   %% Servidor contador: recibe caracteres por un puerto y produce flujo de salida
   fun {ContadorServidor}
      Sin
      P = {NewPort Sin}

      fun {Procesar S Estado}
         case S of Msg|Sr then
            NuevoEstado = {IncChar Msg Estado}
         in
            NuevoEstado|{Procesar Sr NuevoEstado}
         [] nil then nil
         end
      end

      Salida
   in
      thread Salida = {Procesar Sin nil} end
      puerto(enviar:proc {$ X} {Send P X} end salida:Salida)
   end

   %% Cliente: envia una lista de caracteres al servidor
   proc {Cliente Servidor Chars}
      case Chars of C|Cr then
         {Servidor.enviar C}
         {Cliente Servidor Cr}
      [] nil then skip
      end
   end

   %% ===== Pruebas =====
   local Servidor in
      Servidor = {ContadorServidor}

      %% 3 clientes concurrentes
      thread {Cliente Servidor [a c]} end       % Cliente 1
      thread {Cliente Servidor [b c]} end       % Cliente 2
      thread {Cliente Servidor [a]} end          % Cliente 3

      %% Mostrar el flujo de salida
      {Browse Servidor.salida}
   end

   %% NOTA sobre las posibles salidas:
   %% La salida mostrada en el enunciado [a#1]|[a#1 b#1]|[a#2 b#1]|[a#2 b#1 c#1]|[a#2 b#1 c#2]|...
   %% NO es la unica posible porque el planificador de hilos (scheduler) puede intercalar
   %% los mensajes de los 3 clientes en cualquier orden. El orden de llegada al puerto
   %% depende del no-determinismo del scheduling de hilos concurrentes.
   %%
   %% Otras posibles salidas para las mismas entradas (Cliente1: a,c  Cliente2: b,c  Cliente3: a):
   %%   - [b#1]|[b#1 a#1]|[b#1 a#1 c#1]|[b#1 a#2 c#1]|[b#1 a#2 c#2]|...
   %%     (si Cliente2 envia primero, luego Cliente1, luego Cliente3, etc.)
   %%   - [a#1]|[a#1 c#1]|[a#1 b#1 c#1]|[a#1 b#1 c#2]|[a#2 b#1 c#2]|...
   %%     (si Cliente1 envia ambos antes que los demas)
   %%   - [a#1]|[a#2]|[a#2 b#1]|[a#2 b#1 c#1]|[a#2 b#1 c#2]|...
   %%     (si Cliente3 envia inmediatamente despues de Cliente1)
   %%
   %% Lo unico garantizado es que dentro de cada cliente el orden relativo se mantiene:
   %% 'a' de Cliente1 siempre llega antes que 'c' de Cliente1,
   %% 'b' de Cliente2 siempre llega antes que 'c' de Cliente2.
   %% Pero entre clientes distintos no hay garantia de orden.
end
