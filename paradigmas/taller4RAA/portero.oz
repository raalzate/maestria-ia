%% portero.oz
%% Punto 4a: Portero de concierto usando NuevoObjetoPuerto
%% Objeto puerto que cuenta personas en un concierto

functor
import
   Browser(browse:Browse)
define
   fun {NuevoObjetoPuerto Comp Inic}
      Sin
      proc {MsgLoop S1 Estado}
         case S1 of Msg|S2 then
            {MsgLoop S2 {Comp Msg Estado}}
         [] nil then skip
         end
      end
   in
      thread {MsgLoop Sin Inic} end
      {NewPort Sin}
   end

   %% Funcion Comp del Portero: procesa los mensajes y retorna nuevo estado
   fun {PorteroComp Msg Estado}
      case Msg
      of getIn(N) then Estado + N
      [] getOut(N) then Estado - N
      [] getCount(N) then
         N = Estado
         Estado
      end
   end

   %% Crear el Portero
   fun {Portero}
      {NuevoObjetoPuerto PorteroComp 0}
   end

   %% ===== Pruebas =====
   local P N1 N2 N3 in
      P = {Portero}

      %% Entran 5 personas
      {Send P getIn(5)}

      %% Entran 3 personas mas
      {Send P getIn(3)}

      %% Consultar: deben haber 8
      {Send P getCount(N1)}
      {Browse N1}    % Debe mostrar 8

      %% Salen 2 personas
      {Send P getOut(2)}

      %% Consultar: deben haber 6
      {Send P getCount(N2)}
      {Browse N2}    % Debe mostrar 6

      %% Entran 4 mas
      {Send P getIn(4)}

      %% Consultar: deben haber 10
      {Send P getCount(N3)}
      {Browse N3}    % Debe mostrar 10
   end
end
