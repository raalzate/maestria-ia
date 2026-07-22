%% contador2.oz
%% Punto 4b: Contador usando NuevoObjetoPuerto con flujo de salida
%% Reimplementacion del servidor Contador que retorna un flujo de listas
%% con la cantidad de caracteres contados en cada momento

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

   %% Incrementa el conteo de un caracter en la lista de pares
   fun {IncChar Char Estado}
      case Estado
      of nil then [Char#1]
      [] (C#N)|Rest then
         if C == Char then (C#(N+1))|Rest
         else (C#N)|{IncChar Char Rest}
         end
      end
   end

   %% Funcion Counter: crea un contador con objeto puerto
   %% Output es el flujo de salida (flujo de otro puerto)
   fun {Counter Output}
      SalidaSin
      PSalida = {NewPort SalidaSin}

      fun {ContadorComp Msg Estado}
         NuevoEstado = {IncChar Msg Estado}
      in
         {Send PSalida NuevoEstado}
         NuevoEstado
      end
   in
      Output = SalidaSin
      {NuevoObjetoPuerto ContadorComp nil}
   end

   %% Cliente: envia una lista de caracteres al servidor
   proc {Cliente Servidor Chars}
      case Chars of C|Cr then
         {Send Servidor C}
         {Cliente Servidor Cr}
      [] nil then skip
      end
   end

   %% ===== Pruebas =====
   local Output Servidor in
      Servidor = {Counter Output}

      %% 3 clientes concurrentes
      thread {Cliente Servidor [a c]} end       % Cliente 1
      thread {Cliente Servidor [b c]} end       % Cliente 2
      thread {Cliente Servidor [a]} end          % Cliente 3

      %% Mostrar el flujo de salida
      {Browse Output}
      %% Output mostrara algo como:
      %% [a#1] | [a#1 b#1] | [a#2 b#1] | [a#2 b#1 c#1] | [a#2 b#1 c#2] | ...
      %% (el orden exacto depende del scheduling de hilos)
   end
end
