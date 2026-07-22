declare
% newton.oz - Autor: Raul A. Alzate
% Metodo de Newton Generico con representacion simbolica de formulas.
%
% Una formula es:
%   - Un flotante          (constante numerica)
%   - Un atomo             (variable simbolica)
%   - s(F G)               suma      F + G
%   - r(F G)               resta     F - G
%   - m(F G)               producto  F * G
%   - d(F G)               division  F / G
%   - e(F G)               potencia  F ^ G
%   - l(F)                 logaritmo natural ln(F)

% -------------------------------------------------------
% a) {Derivar F A} -> derivada de F respecto al atomo A
%    Aplica las 8 reglas del Cuadro 1 del enunciado.
% -------------------------------------------------------
fun {Derivar F A}
   if {IsFloat F} then 0.0                        % (1) constante -> 0
   elseif {IsAtom F} then
      if F == A then 1.0 else 0.0 end             % (2) variable->1, constante->0
   else
      case {Label F}
      of s then                                    % (3) (f+g)' = f'+g'
         s({Derivar F.1 A} {Derivar F.2 A})
      [] r then                                    % (4) (f-g)' = f'-g'
         r({Derivar F.1 A} {Derivar F.2 A})
      [] m then                                    % (5) (f*g)' = f'*g + f*g'
         s(m({Derivar F.1 A} F.2)
           m(F.1 {Derivar F.2 A}))
      [] d then                                    % (6) (f/g)' = (f'*g - f*g') / g^2
         d(r(m({Derivar F.1 A} F.2)
              m(F.1 {Derivar F.2 A}))
           e(F.2 2.0))
      [] l then                                    % (7) ln(f)' = f'/f
         d({Derivar F.1 A} F.1)
      [] e then                                    % (8) (f^g)' = f^g * (f'*g/f + g'*ln(f))
         m(e(F.1 F.2)
           s(d(m({Derivar F.1 A} F.2) F.1)
             m({Derivar F.2 A} l(F.1))))
      end
   end
end

% -------------------------------------------------------
% b) {Evaluar F A V} -> evaluacion numerica de F con A=V
% -------------------------------------------------------
fun {Evaluar F A V}
   if {IsFloat F} then F
   elseif {IsAtom F} then
      if F == A then V
      else raise undefinedVar(F) end
   else
      case {Label F}
      of s then {Evaluar F.1 A V} + {Evaluar F.2 A V}
      [] r then {Evaluar F.1 A V} - {Evaluar F.2 A V}
      [] m then {Evaluar F.1 A V} * {Evaluar F.2 A V}
      [] d then {Evaluar F.1 A V} / {Evaluar F.2 A V}
      [] e then {Float.pow {Evaluar F.1 A V} {Evaluar F.2 A V}}
      [] l then {Float.log {Evaluar F.1 A V}}
      end
   end
end

% -------------------------------------------------------
% c) {Limpiar F} -> simplifica ceros y unos innecesarios
% -------------------------------------------------------
fun {Limpiar F}
   if {IsFloat F} orelse {IsAtom F} then F
   else
      case {Label F}
      of s then
         local F1={Limpiar F.1} F2={Limpiar F.2} in
            if     F1==0.0 then F2
            elseif F2==0.0 then F1
            else s(F1 F2) end
         end
      [] r then
         local F1={Limpiar F.1} F2={Limpiar F.2} in
            if F2==0.0 then F1 else r(F1 F2) end
         end
      [] m then
         local F1={Limpiar F.1} F2={Limpiar F.2} in
            if     F1==0.0 orelse F2==0.0 then 0.0
            elseif F1==1.0 then F2
            elseif F2==1.0 then F1
            else m(F1 F2) end
         end
      [] d then
         local F1={Limpiar F.1} F2={Limpiar F.2} in
            if F1==0.0 then 0.0 else d(F1 F2) end
         end
      [] e then e({Limpiar F.1} {Limpiar F.2})
      [] l then l({Limpiar F.1})
      end
   end
end

% -------------------------------------------------------
% d) {Raiz F X0 BuenaAprox} -> raiz de F via Newton
%    BuenaAprox: fun {$ F1 V} -> bool
%    La variable de la formula se asume el atomo x.
% -------------------------------------------------------
fun {Raiz F X0 BuenaAprox}
   local A  = x
         DF = {Derivar F A}
   in
      fun {NewtonLoop Xn}
         if {BuenaAprox F Xn} then Xn
         else
            local FXn  = {Evaluar F  A Xn}
                  DFXn = {Evaluar DF A Xn}
            in
               {NewtonLoop Xn - FXn/DFXn}
            end
         end
      end
   in
      {NewtonLoop X0}
   end
end

% -------------------------------------------------------
% Registro que alberga procedimientos: FormulaOps
%
% Demuestra el concepto de embebimiento: un registro cuyos
% campos son funciones de primer orden sobre formulas.
% Permite tratar el conjunto de operaciones como una unidad
% y pasarla/almacenarla como cualquier otro valor de Oz.
% -------------------------------------------------------
local
   FormulaOps = ops(
      derivar: fun {$ F A}   {Derivar F A}   end
      evaluar: fun {$ F A V} {Evaluar F A V} end
      limpiar: fun {$ F}     {Limpiar F}     end
      raiz:    fun {$ F X0 BuenaAprox} {Raiz F X0 BuenaAprox} end
   )
in
   % Uso de FormulaOps: accede a las operaciones por nombre de campo
   local Deriv  = FormulaOps.derivar
         Eval   = FormulaOps.evaluar
         Clean  = FormulaOps.limpiar
         FindR  = FormulaOps.raiz
   in
      % Verificacion con Derivar
      {Browse {Deriv s(k m(3.0 x)) x}}
      % Esperado: s(0.0 s(m(0.0 x) m(1.0 3.0)))

      % Verificacion con Evaluar
      {Browse {Eval d(2.0 x) x 4.0}}
      % Esperado: 0.5

      % Verificacion con Limpiar
      {Browse {Clean s(0.0 s(m(0.0 x) m(3.0 1.0)))}}
      % Esperado: m(3.0 1.0) o 3.0

      % Verificacion con Raiz: f(x) = x^2 - 2.0  (sqrt(2) ~= 1.41421)
      local F         = r(e(x 2.0) 2.0)
            BuenaAprox = fun {$ F1 V}
                            {Float.abs {Eval F1 x V}} < 0.00001
                         end
      in
         {Browse {FindR F 1.0 BuenaAprox}}
      end
   end
end
