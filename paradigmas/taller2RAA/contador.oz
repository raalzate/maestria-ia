% Ejercicio 4: Contador de ocurrencias de caracteres en flujo
% contador.oz
%
% Counter es un proceso concurrente que recibe un flujo de caracteres
% y produce un flujo de listas de tuplas C#N con conteos acumulados.
%
% Ejemplo de uso basico:
%   local InS in
%     {Browse {Counter InS}}
%     InS = a|b|a|c|_
%   end
% Deberia aparecer: [a#1]|[a#1 b#1]|[a#2 b#1]|[a#2 b#1 c#1]|_
%
% Para multiples clientes se usa Merge para intercalar flujos.
% Limitacion: el Merge es deterministico; si un cliente deja de enviar,
% el merge queda bloqueado esperando ese flujo.

% Actualiza la lista de conteos insertando o incrementando el caracter C
fun {Update Cs C}
   case Cs
   of nil then [C#1]
   [] (X#N)|Cr then
      if X == C then (X#(N+1))|Cr
      else (X#N)|{Update Cr C}
      end
   end
end

% Auxiliar del contador: recorre el flujo acumulando conteos
fun {CounterAux InS Acc}
   case InS
   of nil then nil
   [] C|Cr then
      local NewAcc in
         NewAcc = {Update Acc C}
         NewAcc | {CounterAux Cr NewAcc}
      end
   end
end

% Counter: proceso concurrente principal
fun {Counter InS}
   {CounterAux InS nil}
end

% Merge: intercala dos flujos de forma deterministica (alternando)
% Limitacion: si S1 se detiene (cola infinita sin ligar), bloquea.
fun {Merge S1 S2}
   case S1
   of nil then S2
   [] X|S1r then X | {Merge S2 S1r}
   end
end

% ---- Prueba basica ----
local InS in
   {Browse {Counter InS}}
   InS = a|b|a|c|_
end

% ---- Prueba con 2 clientes usando Merge ----
% Cliente 1 envia: a c a
% Cliente 2 envia: b c
% El Merge intercala: a b c c a (aprox)
local S1 S2 Merged in
   thread S1 = a|c|a|nil end
   thread S2 = b|c|nil end
   Merged = {Merge S1 S2}
   {Browse {Counter Merged}}
end
