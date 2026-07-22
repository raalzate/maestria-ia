% Ejercicio 3: Suma de numeros impares usando pipeline concurrente
% sum_impares.oz
%
% Pipeline: Productor -> Filtro (impares) -> Consumidor (suma)
% Cada etapa corre en su propio hilo.

% Productor: genera flujo de enteros 0, 1, 2, ..., Max
fun {Produce I Max}
   if I > Max then nil
   else I | {Produce I+1 Max}
   end
end

% Filtro: retiene solo los numeros impares del flujo
fun {FilterOdd Xs}
   case Xs
   of nil then nil
   [] X|Xr then
      if X mod 2 \= 0 then X | {FilterOdd Xr}
      else {FilterOdd Xr}
      end
   end
end

% Consumidor: suma los elementos del flujo acumulando en Acc
fun {Sum Xs Acc}
   case Xs
   of nil then Acc
   [] X|Xr then {Sum Xr Acc+X}
   end
end

local Xs Ys Result in
   thread Xs = {Produce 0 9999} end
   thread Ys = {FilterOdd Xs} end
   thread Result = {Sum Ys 0} end
   {Browse Result}
end
