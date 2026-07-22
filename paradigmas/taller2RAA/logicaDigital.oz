% Ejercicio 6: Simulacion de logica digital
% logicaDigital.oz
%
% Una compuerta logica es una funcion concurrente que toma flujos de
% valores binarios (0 o 1) y retorna el flujo resultado.

% -------------------------------------------------------
% a) CompuertaNot
% -------------------------------------------------------

% Not auxiliar: niega un bit
fun {Not1 X}
   if X == 1 then 0 else 1 end
end

% CompuertaNot: niega cada elemento del flujo
fun {CompuertaNot Xs}
   case Xs
   of nil then nil
   [] X|Xr then {Not1 X} | {CompuertaNot Xr}
   end
end

% -------------------------------------------------------
% b) CompuertaAnd y CompuertaOr
% -------------------------------------------------------

% CompuertaAnd: AND elemento a elemento de dos flujos
fun {CompuertaAnd Xs Ys}
   case Xs#Ys
   of nil#_ then nil
   [] _#nil then nil
   [] (X|Xr)#(Y|Yr) then
      (X*Y) | {CompuertaAnd Xr Yr}
   end
end

% CompuertaOr: OR elemento a elemento de dos flujos
fun {CompuertaOr Xs Ys}
   case Xs#Ys
   of nil#_ then nil
   [] _#nil then nil
   [] (X|Xr)#(Y|Yr) then
      (if X == 1 orelse Y == 1 then 1 else 0 end) | {CompuertaOr Xr Yr}
   end
end

% -------------------------------------------------------
% c) Simulate: interpreta registros gate(value:Op ...)
%
% Gramatica de circuitos:
%   G ::= input(K)              -- flujo de entrada con clave K
%       | gate(value:'not' G1)  -- compuerta NOT
%       | gate(value:'and' G1 G2) -- compuerta AND
%       | gate(value:'or'  G1 G2) -- compuerta OR
%
% Ss es un registro de flujos de entrada: input(x:Xs y:Ys z:Zs ...)
% -------------------------------------------------------

fun {Simulate G Ss}
   case G
   of input(K) then Ss.K
   [] gate(value:'not' G1) then
      {CompuertaNot {Simulate G1 Ss}}
   [] gate(value:'and' G1 G2) then
      {CompuertaAnd {Simulate G1 Ss} {Simulate G2 Ss}}
   [] gate(value:'or' G1 G2) then
      {CompuertaOr {Simulate G1 Ss} {Simulate G2 Ss}}
   end
end

% -------------------------------------------------------
% d) Sumador completo (Full Adder) - seccion 4.3.5.1 CTM
%
% Entradas: A, B, Cin (flujos de bits)
% Salidas:  Sum, Cout (flujos de bits)
%
% Sum  = A xor B xor Cin
% Cout = (A and B) or (Cin and (A xor B))
%
% XOR = (A or B) and (not (A and B))
% -------------------------------------------------------

fun {CompuertaXor Xs Ys}
   {CompuertaAnd
      {CompuertaOr Xs Ys}
      {CompuertaNot {CompuertaAnd Xs Ys}}}
end

% FullAdder retorna Sum#Cout como par de flujos
fun {FullAdder A B Cin}
   local AxorB Sum Cout in
      AxorB = {CompuertaXor A B}
      Sum   = {CompuertaXor AxorB Cin}
      Cout  = {CompuertaOr
                  {CompuertaAnd A B}
                  {CompuertaAnd Cin AxorB}}
      Sum#Cout
   end
end

% -------------------------------------------------------
% Pruebas
% -------------------------------------------------------

% Prueba de CompuertaNot
{Browse not:{CompuertaNot [1 0 1 0]}}

% Prueba de CompuertaAnd
{Browse and:{CompuertaAnd [1 0 1 0] [1 1 0 0]}}

% Prueba de CompuertaOr
{Browse or:{CompuertaOr [1 0 1 0] [0 0 0 1]}}

% Prueba de Simulate con el ejemplo del enunciado:
% G = (x AND y) OR (NOT z)
% Entrada: x=1|0|1|0 y=0|1|0|1 z=1|1|0|0
% Esperado: 0|0|1|1
local G Resultado in
   G = gate(value:'or'
         gate(value:'and'
            input(x)
            input(y))
         gate(value:'not'
            input(z)))
   Resultado = {Simulate G
      input(x: 1|0|1|0|nil
            y: 0|1|0|1|nil
            z: 1|1|0|0|nil)}
   {Browse simulate:Resultado}
end

% Prueba del sumador completo
% A=1, B=1, Cin=0 -> Sum=0, Cout=1
local S C in
   S#C = {FullAdder [1] [1] [0]}
   {Browse fullAdder:S#C}
end
