%% PuertosConCeldas.oz
%% Punto 1: Implementacion de puertos usando celdas
%% Se construye un TAD con estado, empaquetado y seguro (procedimiento de despacho)

functor
import
   Browser(browse:Browse)
define
   proc {NuevoPuerto S P}
      C = {NewCell S}
   in
      proc {P Msg}
         Old New
      in
         {Exchange C Old New}
         Old = Msg|New
      end
   end

   %% Procedimiento Enviar: envia un mensaje por el puerto
   proc {Enviar P X}
      {P X}
   end

   %% ===== Pruebas =====
   local S P in
      {NuevoPuerto S P}

      %% Enviar mensajes
      {Enviar P a}
      {Enviar P b}
      {Enviar P c}

      %% Verificar el flujo
      {Browse S}      % Debe mostrar a|b|c|_
      {Browse S.1}    % a
      {Browse S.2.1}  % b
      {Browse S.2.2.1} % c
   end
end
