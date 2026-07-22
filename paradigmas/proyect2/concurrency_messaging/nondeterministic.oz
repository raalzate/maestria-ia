declare
  % Un "selector" que espera el primer evento de múltiples fuentes
  proc {NonDeterministicSelector Event1 Event2}
    io:format("Selector: Esperando Event1 o Event2...~n", [])
    case {WaitOr Event1 Event2} % Esto no existe directamente en Oz, pero se puede simular
    % de forma más robusta con ports, unificando messages en una lista, o con el módulo Search.
    % Aquí se simula la idea.
    of event1 then
      io:format("Selector: Event1 ocurrió!~n", [])
    of event2 then
      io:format("Selector: Event2 ocurrió!~n", [])
    end
  end

  % Una simulación más idiomática de espera en múltiples fuentes (ports)
  % Este ejemplo es más conceptual que un fragmento de código Oz directamente ejecutable
  % con WaitOr, pero muestra la idea:
  proc {MultiPortWaiter PortA PortB}
    io:format("MultiPortWaiter: Esperando mensajes de PortA o PortB...~n", [])
    % En Oz, normalmente se usaría un tercer port para canalizar todos los eventos
    % o un hilo dedicado a escuchar ambos y luego decidir.
    % Aquí, ilustramos el concepto de esperar "el primero que llegue".
    thread
      case {PortA.receive} of MsgA then
        io:format("MultiPortWaiter: Recibido '~s' de PortA~n", [MsgA])
        {PortB.send done} % Señaliza que ya se ha procesado
      end
    end
    thread
      case {PortB.receive} of MsgB then
        io:format("MultiPortWaiter: Recibido '~s' de PortB~n", [MsgB])
        {PortA.send done} % Señaliza que ya se ha procesado
      end
    end
    % La elección de qué hilo "gana" es no determinística
  end


  % Ejemplo más directo con variables de flujo
  proc {NonDetWaiter X Y}
    io:format("Esperando X o Y...~n", [])
    if {WaitAndGet X} == event1 then
      io:format("X ocurrió primero~n", [])
    elseif {WaitAndGet Y} == event2 then
      io:format("Y ocurrió primero~n", [])
    end
    % Esto no es estrictamente no determinístico en la espera, sino en la "unificación"
    % de una de las ramas del if. La espera es en ambas.
  end

in
  % Para simular la no determinismo en Oz, es más común usar un "or" lógico en variables
  % de flujo de datos o un actor que multiplexe mensajes de varios puertos.
  %
  % Aquí un ejemplo más práctico de "no determinismo" en Oz con variables de flujo:
  X1 = _ Y1 = _
  thread {Delay 200}; X1 = event1 end
  thread {Delay 100}; Y1 = event2 end

  Z = {WaitOr X1 Y1} % No es una función directa en Oz, pero es el concepto.
                     % La primera variable que se enlaza "gana".
  io:format("Ganador: ~s~n", [Z])
  % El resultado de Z sería 'event2' porque se enlaza primero.
