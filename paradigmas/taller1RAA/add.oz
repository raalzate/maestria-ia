declare
% add.oz - Autor: Raul A. Alzate
% {Add B1 B2} suma dos numeros binarios representados como listas.
% El digito mas significativo (MSB) es el primer elemento de la lista.
% Ejemplo: {Add [1 1 0 1 1 0] [0 1 0 1 1 1]} -> [1 0 0 1 1 0 1]
%
% Estrategia: invertir ambas listas para procesar de LSB a MSB,
% propagando el carry hacia la izquierda. Al construir el resultado
% con | (prepend) durante el recorrido LSB->MSB, el acumulador queda
% en orden MSB primero sin necesidad de inversion final.

fun {Reverse L}
   fun {RevAcc L Acc}
      case L of nil then Acc
      [] H|T then {RevAcc T H|Acc}
      end
   end
in {RevAcc L nil} end

fun {Add B1 B2}
   fun {AddAcc R1 R2 Carry Acc}
      case R1#R2
      of nil#nil then
         if Carry == 0 then Acc
         else Carry|Acc end
      [] (H1|T1)#(H2|T2) then
         local Sum = H1 + H2 + Carry in
            {AddAcc T1 T2 Sum div 2 (Sum mod 2)|Acc}
         end
      end
   end
in
   {AddAcc {Reverse B1} {Reverse B2} 0 nil}
end

{Browse {Add [1 1 0 1 1 0] [0 1 0 1 1 1]}}
% 110110 (54) + 010111 (23) = 1001101 (77)
% Esperado: [1 0 0 1 1 0 1]
