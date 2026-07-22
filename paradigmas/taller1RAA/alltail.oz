declare
% alltail.oz - Autor: Raul A. Alzate
% {ForAllTail Xs P} aplica el procedimiento P a cada sublista no vacia de Xs.
%
% Para Xs = [X1 X2 ... Xn] la secuencia de aplicaciones es:
%   {P [X1 X2 ... Xn]}
%   {P [X2 ... Xn]}
%   ...
%   {P [Xn]}
%
% Es recursion de cola: la llamada recursiva es la ultima instruccion evaluada.

proc {ForAllTail Xs P}
   case Xs of nil then skip
   [] _|T then
      {P Xs}
      {ForAllTail T P}
   end
end

% Ejemplo de uso
{ForAllTail [a b c] proc {$ L} {Browse L} end}
% Muestra: [a b c], luego [b c], luego [c]
