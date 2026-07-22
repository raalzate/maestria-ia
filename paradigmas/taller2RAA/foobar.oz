% Ejercicio 5: Foo y Bar - Productor/Consumidor con buffer limitado
% foobar.oz
%
% Bar (Productor): sirve 1 cerveza cada 3s durante 1 hora (3600s)
% Foo (Consumidor): bebe 1 cerveza cada 12s
% Buffer maximo: 5 cervezas en la mesa al mismo tiempo
%
% Por que es necesario buffer limitado:
%   Bar es 4 veces mas rapido que Foo (3s vs 12s). Sin limite, Bar
%   acumularia cervezas que se calentarian. El buffer de 5 unidades
%   hace que Bar espere (bloquee en la ligadura de la variable) cuando
%   hay 5 cervezas sin consumir, evitando que la cerveza se enfrie/caliente.
%
% Implementacion: se modela el buffer con una diferencia entre un flujo
% "producido" y un flujo "consumido". Se usa un contador de tokens para
% controlar que Bar no avance mas de N posiciones adelante de Foo.

% BarLoop: sirve cervezas cada 3s hasta completar 1 hora (simulado con
% MaxCervezas para pruebas rapidas)
proc {BarLoop Buffer T MaxT End}
   if T >= MaxT then End = nil
   else
      {Delay 3000}
      local Rest in
         Buffer = cerveza|Rest
         {BarLoop Rest T+3000 MaxT End}
      end
   end
end

% Foo: bebe cada 12s hasta que el flujo termine
proc {Foo Buffer}
   case Buffer
   of nil then {Browse fooTermino}
   [] cerveza|Rest then
      {Delay 12000}
      {Browse bebe}
      {Foo Rest}
   end
end

% Buffer limitado: permite maximo N elementos entre productor y consumidor.
% Se implementa usando diferencia de flujos con un contador.
% BufProd es lo que Bar escribe; BufCons es lo que Foo lee.
% Se mantiene que BufProd este como maximo N pasos adelante de BufCons.

fun {MakeBuffer N}
   % Retorna un par Prod#Cons donde Prod es la cola de escritura
   % y Cons es la cabeza de lectura. El limite N se implementa
   % haciendo que el productor espere tokens del consumidor.
   % Usamos la tecnica de diferencia de listas con contador:
   % el productor tiene N tokens iniciales; por cada cerveza servida
   % consume un token; por cada cerveza bebida, Foo devuelve un token.
   local Prod Cons in
      Prod#Cons
   end
end

% Version simplificada: modela el buffer como flujo con limite implicito
% via sincronizacion por variables. En Oz puro declarativo, el limite
% se impone haciendo que Bar espere que Foo "devuelva" un token antes
% de servir la siguiente cerveza cuando el buffer esta lleno.

% Implementacion con contador de tokens (semaforo declarativo)
% Tokens: flujo de permisos. Bar consume un token antes de servir.
% Foo produce un token despues de beber.

proc {BarConBuffer Buf Tokens T MaxT End}
   if T >= MaxT then End = nil
   else
      % Esperar token disponible (si buffer lleno, Tokens estara bloqueado)
      case Tokens
      of _|TokensRest then
         {Delay 3000}
         local BufRest in
            Buf = cerveza|BufRest
            {BarConBuffer BufRest TokensRest T+3000 MaxT End}
         end
      end
   end
end

proc {FooConBuffer Buf DevTokens}
   case Buf
   of nil then DevTokens = nil
   [] cerveza|BufRest then
      {Delay 12000}
      {Browse bebe}
      local DevRest in
         DevTokens = token|DevRest
         {FooConBuffer BufRest DevRest}
      end
   end
end

% Genera N tokens iniciales
fun {GenTokens N}
   if N =< 0 then nil
   else token|{GenTokens N-1}
   end
end

% Combina tokens iniciales con tokens devueltos por Foo
fun {CombineTokens Ini Dev}
   case Ini
   of nil then Dev
   [] T|Ir then T|{CombineTokens Ir Dev}
   end
end

% Ejecucion principal (MaxT en ms; 3600000 = 1 hora real)
% Para pruebas usamos MaxT = 60000 (1 minuto simulado)
local Buf BufEnd Tokens DevTokens TokIni in
   TokIni = {GenTokens 5}               % 5 tokens = buffer de 5
   Tokens = {CombineTokens TokIni DevTokens}

   thread {BarConBuffer Buf Tokens 0 60000 BufEnd} end
   thread {FooConBuffer Buf DevTokens} end

   {Browse empezando}
end
