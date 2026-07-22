declare
% factList.oz - Autor: Raul A. Alzate
% {FactList N} recibe un entero N y retorna [1! 2! ... N!]
% Computacion recursiva con acumulador

fun {Reverse L}
   fun {RevAcc L Acc}
      case L of nil then Acc
      [] H|T then {RevAcc T H|Acc}
      end
   end
in {RevAcc L nil} end

fun {FactList N}
   % FactLoop acumula la lista en orden inverso; Reverse la corrige al final
   fun {FactLoop I CurrFact Acc}
      if I > N then {Reverse Acc}
      else
         local NextFact = CurrFact * I in
            {FactLoop I+1 NextFact NextFact|Acc}
         end
      end
   end
in
   if N < 1 then raise illegalArgument end
   else {FactLoop 1 1 nil}
   end
end

{Browse {FactList 4}}  % Esperado: [1 2 6 24]
{Browse {FactList 1}}  % Esperado: [1]
{Browse {FactList 5}}  % Esperado: [1 2 6 24 120]
