%% CeldasConPuertos.oz
%% Punto 2: Implementacion de celdas usando objetos puerto
%% Las celdas son contenedores de valores que cambian en el tiempo

functor
import
   Browser(browse:Browse)
define
   proc {NuevaCelda X C}
      Sin
      proc {MsgLoop S1 Estado}
         case S1 of Msg|S2 then
            case Msg
            of acceder(R) then
               R = Estado
               {MsgLoop S2 Estado}
            [] asignar(NuevoVal) then
               {MsgLoop S2 NuevoVal}
            end
         [] nil then skip
         end
      end
   in
      {NewPort Sin C}
      thread {MsgLoop Sin X} end
   end

   proc {Acceder X C}
      {Send C acceder(X)}
   end

   proc {Asignar X C}
      {Send C asignar(X)}
   end

   %% ===== Pruebas =====
   local C V1 V2 in
      {NuevaCelda 10 C}

      %% Leer valor inicial
      {Acceder V1 C}
      {Browse V1}     % Debe mostrar 10

      %% Asignar nuevo valor
      {Asignar 25 C}

      %% Leer nuevo valor
      {Acceder V2 C}
      {Browse V2}     % Debe mostrar 25
   end
end
