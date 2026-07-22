declare
% convolucion.oz - Autor: Raul A. Alzate
% Convolucion SIMBOLICA con recursion de cola.
% {Convolucion [x1..xn] [y1..yn]} = [x1#yn  x2#yn-1  ...  xn#y1]
%
% El operador # de Oz crea pares simbolicos: x1#yn es la tupla '#'(x1 yn).
% La funcion realiza exactamente N invocaciones recursivas (N = longitud de las listas).
%
% Estrategia: invertir L2 para poder recorrer ambas listas de izquierda a derecha
% emparejando xi con y_{n-i+1} directamente.

fun {Reverse L}
   fun {RevAcc L Acc}
      case L of nil then Acc
      [] H|T then {RevAcc T H|Acc}
      end
   end
in {RevAcc L nil} end

fun {Convolucion L1 L2}
   fun {ConvAcc L1 RevL2 Acc}
      case L1#RevL2
      of nil#_ then {Reverse Acc}
      [] (H1|T1)#(H2|T2) then
         {ConvAcc T1 T2 (H1#H2)|Acc}
      end
   end
in
   {ConvAcc L1 {Reverse L2} nil}
end

{Browse {Convolucion [x1 x2 x3] [y1 y2 y3]}}
% Esperado: [x1#y3  x2#y2  x3#y1]
