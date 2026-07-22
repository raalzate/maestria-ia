declare
% sum.oz - Autor: Raul A. Alzate
%
% La implementacion original (N + {Sum N-1}) NO es iterativa porque
% la operacion + queda suspendida en la pila semantica esperando
% el resultado de la llamada recursiva -> pila O(N).
%
% Version iterativa usando iterador de alto orden {FoldRange}:
%
%   Modelo de estados para FoldRange:
%   Estado S = (I, Acc)
%   S0       = (1, 0)
%   S_{i+1}  = (I+1, Acc+I)
%   S_final  = (N+1, N*(N+1)/2)
%   Invariante P(I, Acc): Acc = (I-1)*I/2  (suma de 1..I-1)
%   Progreso: I crece estrictamente -> se alcanza I=N+1 en N pasos.

% Iterador de alto orden: reduce el rango [Low..High] con F y acumulador Acc
fun {FoldRange Low High F Acc}
   if Low > High then Acc
   else {FoldRange Low+1 High F {F Acc Low}}
   end
end

fun {Sum N}
   if N < 0 then raise illegalArgument end
   else {FoldRange 1 N fun {$ Acc X} Acc+X end 0}
   end
end

{Browse {Sum 5}}   % Esperado: 15
{Browse {Sum 10}}  % Esperado: 55
{Browse {Sum 0}}   % Esperado: 0
