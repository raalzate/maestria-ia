declare
  % Proceso (agente) que recibe mensajes a través de un port
  proc {Agent Port}
    proc {Loop}
      case {Port.receive} % Espera un mensaje
      of stop then
        io:format("Agente: Recibido 'stop', terminando.~n", [])
      of MSG then
        io:format("Agente: Recibido '~s'~n", [MSG])
        {Loop} % Continúa esperando más mensajes
      end
    end
  in
    {Loop}
  end

in
  {NewPort SendPort ReceivePort} % Crea un nuevo port
  thread {Agent ReceivePort} end % Lanza el agente en un hilo

  {SendPort "Hola"}
  {SendPort "Mundo"}
  {Delay 100} % Pequeña pausa para que el agente procese
  {SendPort stop} % Envía el mensaje de parada
